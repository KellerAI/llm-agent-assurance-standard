# LAAS standards — house-styled PDF pipeline

Renders the four LAAS standards-format documents in `docs/laas/standards/`
into PDFs that visually emulate each issuing body's house style
(`build.sh:45`).

| Source | Theme | Cover | Output | Page | Look |
|--------|-------|-------|--------|------|------|
| `../laas-ieee.md` | `themes/ieee.css` | `covers/ieee-cover.html` | `out/laas-ieee.pdf` | US Letter | IEEE-Std drafting: centred serif title, navy ruled clause heads, justified Times-like body, designation running header |
| `../laas-nist.md` | `themes/nist.css` | `covers/nist-cover.html` | `out/laas-nist.pdf` | US Letter | NIST SP: sans (NIST-blue) heads over serif body, blue table headers, SP-style running header/footer |
| `../laas-iso.md` | `themes/iso.css` | `covers/iso-cover.html` | `out/laas-iso.pdf` | A4 | ISO/IEC Directives: `ISO/IEC XXXXX:2026(E)` header, ISO-blue sans clause heads, justified serif body, rights-reserved footer |
| `../laas-sr.md` | `themes/sr.css` | `covers/sr-cover.html` | `out/laas-sr.pdf` | US Letter | Federal Reserve SR-letter style (SR 11-7 / SR 26-2): serif body, `SR 26-XX (Unofficial Draft)` running header, centred letterhead cover, page-break clause heads |

Each document needs all three inputs: the source markdown, the theme
stylesheet, and the cover page, which pandoc inserts before the body. The
script stops with an error if any of them is missing (`build.sh:52-54`,
`build.sh:62`).

## Build

From the repository root:

```bash
bash docs/laas/standards/pdf/build.sh
```

The script resolves its own paths (`build.sh:15-18`), so `./build.sh` run
from `docs/laas/standards/pdf/` works too.

For each document, pandoc converts the source from GitHub-flavoured
markdown to HTML5 (`build.sh:57-64`), and WeasyPrint renders that HTML to
PDF with the theme stylesheet (`build.sh:65`). The PDFs land in `out/`
(`build.sh:18`, `build.sh:50`), which is git-ignored (`.gitignore:3`). The
intermediate HTML file is deleted after each render (`build.sh:66`).

Requires `pandoc` and `weasyprint` on `PATH`; the script exits with an
error if either is missing (`build.sh:21-23`). It also uses the base
utility `mktemp` for a temporary pandoc template (`build.sh:27`).

## Scope and marks

These themes are an **unofficial visual emulation**. They carry **no**
official IEEE, NIST, ISO/IEC, or Federal Reserve logos, seals, or
trademarks (`build.sh:6-7`, `themes/sr.css:2`), and every rendering is
watermarked in its header/footer as a draft that is **not** an approved
standard or official issuance of any body (`themes/ieee.css:20`,
`themes/nist.css:22`, `themes/iso.css:14`, `themes/sr.css:16`). The
designations (`IEEE P-XXXX`, `ISO/IEC XXXXX`, `SR 26-XX`, etc.) are
placeholders (`covers/ieee-cover.html:11`, `covers/sr-cover.html:16`).
