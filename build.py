#!/usr/bin/env python3
"""Gera o site do vitae (vitae.paodelonga.dev) a partir de src/.

Saída: dist/ (é o que o GitHub Pages publica, pelo workflow .github/workflows/pages.yml).

    python3 build.py           monta dist/ usando os PDFs já versionados em pdf/
    python3 build.py --pdf     regenera os PDFs em pdf/ (precisa de Chromium), depois monta dist/

Dependências: python3 (stdlib), pandoc. Para --pdf também: chromium (ou google-chrome).
Os PDFs são versionados em pdf/ porque o build no Actions não tem Chromium.
"""

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
SITE = SRC / "site"
DIST = ROOT / "dist"
PDF_DIR = ROOT / "pdf"
BUILD = ROOT / ".build"

# name = nome do arquivo público (sem extensão). Mantenha os nomes: os links antigos dependem deles.
CVS = [
    {
        "src": SRC / "cv" / "pt-br" / "full.md",
        "name": "curriculum-abiel_mendes-pt_br-full",
        "lang": "pt-br",
        "title": "Abiel Mendes dos Santos · currículo",
        "description": "Currículo completo de Abiel Mendes dos Santos (pt-br).",
        "other": ("curriculum-abiel_mendes-en_us-full", "en-us"),
        "listed": True,
    },
    {
        "src": SRC / "cv" / "en-us" / "full.md",
        "name": "curriculum-abiel_mendes-en_us-full",
        "lang": "en-us",
        "title": "Abiel Mendes dos Santos · CV",
        "description": "Full CV of Abiel Mendes dos Santos (en-us).",
        "other": ("curriculum-abiel_mendes-pt_br-full", "pt-br"),
        "listed": True,
    },
    {
        "src": SRC / "cv" / "pt-br" / "minimal.md",
        "name": "curriculum-abiel_mendes-pt_br-minimal",
        "lang": "pt-br",
        "title": "Abiel Mendes dos Santos · currículo curto",
        "description": "Versão curta do currículo de Abiel Mendes dos Santos (pt-br).",
        "other": None,
        "listed": False,  # publicada, mas fora da página principal até ser revisada
    },
]

# Cabeçalhos que o ATS reconhece (templates/ats-rules.yml do career-ops). Só avisamos.
ATS_HEADERS_PT = ["Resumo Profissional", "Experiência Profissional", "Formação", "Habilidades", "Projetos"]
ATS_HEADERS_EN = ["Professional Summary", "Work Experience", "Education", "Skills", "Projects"]

# Botão "PDF" no fim de cada .md antigo: some do HTML, o link já está no cabeçalho da página.
PDF_BUTTON = re.compile(r"\n+-{3,}\n+\[<kbd>.*?</kbd>\]\([^)]*\)\s*$", re.S)


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def md_to_html(md_text):
    text = PDF_BUTTON.sub("\n", md_text)
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html5", "--wrap=none"],
        input=text, capture_output=True, text=True, check=True,
    )
    return result.stdout


def chrome_bin():
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("erro: Chromium não encontrado (necessário para --pdf)")


def make_pdf(html_path, pdf_path):
    cmd = [
        chrome_bin(), "--headless=new", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    run(cmd, timeout=180)


def check_ats(pdf_path, md_path):
    """Avisos, não erros: texto extraível, número de páginas e cabeçalhos fora do padrão."""
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        return
    text = run(["pdftotext", str(pdf_path), "-"]).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", run(["pdfinfo", str(pdf_path)]).stdout).group(1))
    headings = re.findall(r"^## (.+)$", md_path.read_text(encoding="utf-8"), re.M)
    print(f"  {pdf_path.name}: {pages} página(s), {len(text)} caracteres extraídos")
    print(f"    seções: {' | '.join(headings)}")
    if pages > 2:
        print("    aviso: mais de 2 páginas (o career-ops marca 2 como o limite)")
    standard = set(ATS_HEADERS_PT) | set(ATS_HEADERS_EN)
    odd = [h for h in headings if h not in standard]
    if odd:
        print(f"    nota: cabeçalhos fora do padrão ATS: {' | '.join(odd)}")


def build_cv_pages():
    page_tpl = (SITE / "cv-page.html").read_text(encoding="utf-8")
    print_tpl = (SITE / "cv-print.html").read_text(encoding="utf-8")
    print_css = (SITE / "print-ats.css").read_text(encoding="utf-8")
    BUILD.mkdir(exist_ok=True)

    for cv in CVS:
        body = md_to_html(cv["src"].read_text(encoding="utf-8"))

        # página HTML, no mesmo estilo da página principal
        if cv["other"]:
            other_name, other_lang = cv["other"]
            lang_links = (
                f'<span aria-current="true">{cv["lang"]}</span>'
                f'<span aria-hidden="true">/</span>'
                f'<a href="./{other_name}.html" lang="{other_lang}">{other_lang}</a>'
            )
        else:
            lang_links = f'<span aria-current="true">{cv["lang"]}</span>'

        page = (
            page_tpl
            .replace("{{LANG}}", cv["lang"])
            .replace("{{TITLE}}", html.escape(cv["title"]))
            .replace("{{DESCRIPTION}}", html.escape(cv["description"]))
            .replace("{{LANG_LINKS}}", lang_links)
            .replace("{{PDF_NAME}}", cv["name"] + ".pdf")
            .replace("{{BODY}}", body)
        )
        (DIST / f'{cv["name"]}.html').write_text(page, encoding="utf-8")

        # HTML de impressão, com o CSS do ATS embutido: é dele que sai o PDF
        print_html = BUILD / f'{cv["name"]}.print.html'
        print_html.write_text(
            print_tpl
            .replace("{{LANG}}", cv["lang"])
            .replace("{{TITLE}}", html.escape(cv["title"]))
            .replace("{{CSS}}", print_css)
            .replace("{{BODY}}", body),
            encoding="utf-8",
        )
        yield cv, print_html


def main():
    regen = "--pdf" in sys.argv

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    PDF_DIR.mkdir(exist_ok=True)

    # estático: página principal, estilo compartilhado, domínio personalizado
    shutil.copy(SITE / "index.html", DIST / "index.html")
    shutil.copy(SITE / "style.css", DIST / "style.css")
    shutil.copy(ROOT / "CNAME", DIST / "CNAME")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    print("currículos:")
    for cv, print_html in build_cv_pages():
        pdf_path = PDF_DIR / f'{cv["name"]}.pdf'
        if regen:
            make_pdf(print_html, pdf_path)
            print(f"  gerado {pdf_path.relative_to(ROOT)}")
        if pdf_path.exists():
            check_ats(pdf_path, cv["src"])
        else:
            print(f"  aviso: {pdf_path.relative_to(ROOT)} não existe; rode com --pdf")

    # PDFs versionados entram em dist/pdf/ para os links da página
    (DIST / "pdf").mkdir()
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        shutil.copy(pdf, DIST / "pdf" / pdf.name)

    if BUILD.exists():
        shutil.rmtree(BUILD)
    print(f"ok: {DIST.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
