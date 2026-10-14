# LAAS standards — formatted PDF pipeline

Renders the four LAAS standards-format documents in `docs/laas/standards/`
into PDFs published by KellerAI, each formatted after the drafting
conventions of one body (`build.sh:4-6`, `build.sh:45`).

| Source | Theme | Cover | Output | Page | Look |
|--------|-------|-------|--------|------|------|
| `../laas-ieee.md` | `themes/ieee.css` | `covers/ieee-cover.html` | `out/laas-ieee.pdf` | US Letter | IEEE-format: centred serif title, navy ruled clause heads, justified Times-like body, KellerAI designation running header |
| `../laas-nist.md` | `themes/nist.css` | `covers/nist-cover.html` | `out/laas-nist.pdf` | US Letter | NIST-format: blue sans heads over serif body, blue table headers, KellerAI designation running header, unofficial-draft footer |
| `../laas-iso.md` | `themes/iso.css` | `covers/iso-cover.html` | `out/laas-iso.pdf` | A4 | ISO-format (after the ISO/IEC Directives Part 2 layout): KellerAI designation header, blue sans clause heads, justified serif body, unofficial-draft footer |
| `../laas-sr.md` | `themes/sr.css` | `covers/sr-cover.html` | `out/laas-sr.pdf` | US Letter | SR-letter-format (after SR 11-7 / SR 26-2): serif body, KellerAI designation running header, KellerAI publisher cover, page-break clause heads |

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

Each rendering is a KellerAI publication formatted after a body's drafting
conventions; none is issued, approved, or endorsed by that body. The themes
carry **no** official IEEE, NIST, ISO/IEC, or Federal Reserve logos, seals,
or trademarks (`build.sh:6-8`, `themes/ieee.css:1-2`, `themes/nist.css:1-2`,
`themes/iso.css:1-2`, `themes/sr.css:1-2`).

The covers share these conventions:

- **Publisher:** `Published by KellerAI.` (`covers/ieee-cover.html:11`,
  `covers/nist-cover.html:7`, `covers/iso-cover.html:7`,
  `covers/sr-cover.html:2`).
- **Designation:** `KellerAI LAAS 1.1 · <FORMAT> rendering · Draft 1 (2026)`,
  where `<FORMAT>` is `IEEE-format`, `NIST-format`, `ISO-format`, or
  `SR-letter-format` (`covers/ieee-cover.html:3`, `covers/nist-cover.html:3`,
  `covers/iso-cover.html:8`, `covers/sr-cover.html:4`).
- **Attribution:** `Formatted after the drafting conventions of <BODY>. Not
  issued, approved, or endorsed by <BODY>.` (`covers/ieee-cover.html:11`,
  `covers/nist-cover.html:11`, `covers/iso-cover.html:11`,
  `covers/sr-cover.html:9`).
- **Copyright:** `© 2026 KellerAI contributors. Licensed under Apache-2.0.`
  (`covers/ieee-cover.html:11`, `covers/nist-cover.html:11`,
  `covers/iso-cover.html:9`, `covers/sr-cover.html:9`).

Every body page carries the KellerAI designation in its running header
(`themes/ieee.css:8`, `themes/nist.css:8`, `themes/iso.css:8`,
`themes/sr.css:8`) and an `Unofficial: not a publication of <BODY>.` footer
(`themes/ieee.css:20`, `themes/nist.css:22`, `themes/iso.css:14`,
`themes/sr.css:16`).
