# Tracing Bible generator

`make_bible.py` builds a tracing-edition PDF (light-gray text to trace with a stylus), page 170x272 mm (16:10, Galaxy Tab).

Usage: `python3 -I make_bible.py OUTPUT.pdf [N_BOOKS]` — run it twice (the 1st pass records page numbers for the table of contents).

Requires: `reportlab`, `fonttools`.

Inputs expected next to the script's parent folder (`S` = parent of `tracing-bible/`'s equivalent `gen/` dir):
- `dl/x/package/json/<book>.json` — World English Bible JSON from the npm package `world-english-bible` (public domain).
- `dl/f_kalam/...` and `dl/f_kaushan-script/...` — npm packages `@fontsource/kalam` and `@fontsource/kaushan-script` (woff files, converted to ttf at run time).

To make another translation (e.g. Portuguese Almeida, public domain), replace the JSON loader `load()` and the `BOOKS` list.
Layout: font Kalam 14.2pt, leading 27pt, Kaushan Script titles, gray text (0.70).
