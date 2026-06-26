# LAAS standards — house-styled PDF pipeline

Renders the three LAAS standards-format documents in `docs/laas/standards/`
into PDFs that visually emulate each issuing body's house style.

| Source | Theme | Page | Look |
|--------|-------|------|------|
| `../laas-ieee.md` | `themes/ieee.css` | US Letter | IEEE-Std drafting: centred serif title, navy ruled clause heads, justified Times-like body, designation running header |
| `../laas-nist.md` | `themes/nist.css` | US Letter | NIST SP: sans (NIST-blue) heads over serif body, blue table headers, SP-style running header/footer |
| `../laas-iso.md` | `themes/iso.css` | A4 | ISO/IEC Directives: `ISO/IEC XXXXX:2026(E)` header, ISO-blue sans clause heads, justified serif body, rights-reserved footer |
| `../laas-sr.md` | `themes/sr.css` | US Letter | Federal Reserve SR-letter style (SR 11-7 / SR 26-2): serif body, `SR 26-XX (Unofficial Draft)` running header, centred letterhead cover, page-break clause heads |

## Build

```bash
./build.sh
```

Outputs land in `out/` (git-ignored). Requires `pandoc` and `weasyprint`
on `PATH`.

## Scope and marks

These themes are an **unofficial visual emulation**. They carry **no**
official IEEE, NIST, or ISO/IEC logos, seals, or trademarks, and every
rendering is watermarked in its header/footer as a draft that is **not**
an approved standard of any body. The designations (`IEEE P-XXXX`,
`ISO/IEC XXXXX`, etc.) are placeholders.
