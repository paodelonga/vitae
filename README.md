# vitae

Site e currículos de Pão (Abiel Mendes dos Santos), publicados em <https://vitae.paodelonga.dev>.

## Estrutura

```
src/
  cv/pt-br/full.md        currículo completo, PT-BR (fonte da verdade)
  cv/en-us/full.md        currículo completo, EN-US (tradução do de cima)
  cv/pt-br/minimal.md     versão curta, PT-BR (publicada, fora da página principal)
  cv/archive/             versões antigas, não publicadas
  site/index.html         página principal
  site/style.css          estilo compartilhado (página e currículos em HTML)
  site/cv-page.html       modelo do currículo em HTML
  site/cv-print.html      modelo do PDF
  site/print-ats.css      estilo do PDF (ATS: uma coluna, texto preto, fonte padrão)
pdf/                      PDFs gerados e versionados
perfil/                   textos para LinkedIn e Instagram (não publicados)
build.py                  gera dist/ a partir de src/
CNAME                     domínio personalizado (vitae.paodelonga.dev)
```

## Como gerar

```sh
python3 build.py          # monta dist/ com os PDFs de pdf/
python3 build.py --pdf    # regenera os PDFs em pdf/ (precisa de Chromium) e monta dist/
```

Dependências: Python 3, pandoc. Para `--pdf`, também Chromium. O workflow
`.github/workflows/pages.yml` roda `build.py` e publica `dist/`; ele não gera PDF.

## Regras

- **Fonte da verdade:** os currículos em `src/cv/` são a única fonte. A página em
  HTML e o PDF saem deles. Editou o currículo, rode `build.py --pdf` e commite o PDF.
- **Fatos:** a versão em inglês é tradução, não reescrita. Mudança de fato vale nas duas línguas.
- **ATS:** o PDF segue as regras de `templates/ats-rules.yml` do
  [career-ops](https://github.com/career-ops-hq/career-ops): uma coluna, texto selecionável,
  nome e contato no corpo (não no cabeçalho do PDF), cabeçalhos padrão
  (Resumo Profissional, Experiência Profissional, Formação, Habilidades, Projetos),
  sem tabelas aninhadas nem texto escondido. O `build.py` avisa quando um PDF passa de 2 páginas
  ou tem cabeçalho fora do padrão.
- **Nomes de arquivo:** os nomes `curriculum-abiel_mendes-*` são públicos. Não renomeie sem
  ajustar os links da página principal e do perfil do GitHub.
