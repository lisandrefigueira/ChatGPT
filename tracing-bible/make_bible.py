import json, os, sys
from fontTools.ttLib import TTFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.lib.units import mm
from reportlab.lib.colors import Color

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = S + '/dl'
OUT = sys.argv[1]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # test: only first N books

# ---- fonts (woff -> ttf)
os.makedirs(S + '/gen/fonts', exist_ok=True)
def mk(name, woff):
    ttf = f'{S}/gen/fonts/{name}.ttf'
    f = TTFont(woff); f.flavor = None; f.save(ttf)
    pdfmetrics.registerFont(RLFont(name, ttf))
mk('Kalam', f'{DL}/f_kalam/package/files/kalam-latin-400-normal.woff')
mk('KalamL', f'{DL}/f_kalam/package/files/kalam-latin-300-normal.woff')
mk('KalamB', f'{DL}/f_kalam/package/files/kalam-latin-700-normal.woff')
mk('Kaushan', f'{DL}/f_kaushan-script/package/files/kaushan-script-latin-400-normal.woff')
HEAD = 'Helvetica'

BOOKS = [("Matthew","matthew"),("Mark","mark"),("Luke","luke"),("John","john"),("Acts","acts"),
 ("Romans","romans"),("1 Corinthians","1corinthians"),("2 Corinthians","2corinthians"),
 ("Galatians","galatians"),("Ephesians","ephesians"),("Philippians","philippians"),
 ("Colossians","colossians"),("1 Thessalonians","1thessalonians"),("2 Thessalonians","2thessalonians"),
 ("1 Timothy","1timothy"),("2 Timothy","2timothy"),("Titus","titus"),("Philemon","philemon"),
 ("Hebrews","hebrews"),("James","james"),("1 Peter","1peter"),("2 Peter","2peter"),
 ("1 John","1john"),("2 John","2john"),("3 John","3john"),("Jude","jude"),("Revelation","revelation")]
if LIMIT: BOOKS = BOOKS[:LIMIT]

# ---- page geometry: 16:10 like Galaxy Tab
PW, PH = 170*mm, 272*mm
MX, MT, MB = 15*mm, 24*mm, 20*mm
TW = PW - 2*MX
FS, LEAD = 14.2, 27.0           # generous leading to trace with a stylus
VFS = 8.2
FONT = 'Kalam'
GRAY = Color(0.70, 0.70, 0.72)      # tracing text
VGRAY = Color(0.55, 0.55, 0.58)
INK = Color(0.12, 0.12, 0.15)
BIG = 46

def load(slug):
    """-> chapters: {n: [block]} block = ('p',[(v,text)]) or ('s',[[(v,text)],...])"""
    d = json.load(open(f'{DL}/x/package/json/{slug}.json'))
    ch = {}; cur = None; mode = None; line = None
    for x in d:
        t = x['type']
        if t == 'paragraph start': mode = 'p'; cur = ('p', [])
        elif t == 'paragraph end':
            if cur and cur[1]: ch.setdefault(last, []).append(cur)
            cur = None
        elif t == 'stanza start': cur = ('s', []); line = []; mode = 's'
        elif t == 'line break':
            if line: cur[1].append(line)
            line = []
        elif t == 'stanza end':
            if line: cur[1].append(line)
            if cur[1]: ch.setdefault(last, []).append(cur)
            cur = None
        elif t in ('paragraph text', 'line text'):
            v = x['value']; last = x['chapterNumber']
            if not v.strip(): continue
            seg = (x['verseNumber'], v)
            if cur is None: cur = ('p', []); mode = 'p'
            if cur[0] == 'p': cur[1].append(seg)
            else: line.append(seg)
    return ch

def tokens(segs, seen):
    out = []
    for v, text in segs:
        if v not in seen:
            seen.add(v); out.append(('v', str(v)))
        for w in text.split():
            out.append(('w', w))
    return out

c = canvas.Canvas(OUT, pagesize=(PW, PH), pageCompression=1)
c.setTitle('New Testament - Tracing Edition (WEB)')
c.setAuthor('World English Bible (public domain)')
page_no = [0]
toc = []   # (book, page)
state = {'y': 0, 'hdr': ''}

def header():
    c.setFont(HEAD, 7.5); c.setFillColor(VGRAY)
    c.drawString(MX, PH - 12*mm, state['hdr'].upper())
    c.drawRightString(PW - MX, PH - 12*mm, str(page_no[0]))

def newpage(hdr=None):
    if page_no[0]: c.showPage()
    page_no[0] += 1
    if hdr is not None: state['hdr'] = hdr
    header(); state['y'] = PH - MT

def ensure(h, hdr=None):
    if state['y'] - h < MB: newpage(hdr)

def draw_tokens(toks, indent_first=0.0, indent_rest=0.0, big_lines=0, bigw=0.0, first_line_hdr=None):
    """Greedy wrap. Returns after drawing. indent_first applies to line 1; big_lines lines get bigw indent."""
    sp = pdfmetrics.stringWidth(' ', FONT, FS)
    lines = []; cur = []; w = 0.0; idx = 0
    def avail(i):
        base = indent_first if i == 0 else indent_rest
        if i < big_lines: base = max(base, bigw)
        return TW - base, base
    for kind, s in toks:
        tw = pdfmetrics.stringWidth(s, 'KalamB' if kind == 'v' else FONT, VFS if kind == 'v' else FS)
        if kind == 'v': tw += 1.5
        a, _ = avail(len(lines))
        add = tw + (sp if cur and cur[-1][0] != 'v' else 0)
        if cur and w + add > a and kind == 'w':
            lines.append(cur); cur = []; w = 0; add = tw
        elif cur and kind == 'v' and w + add + 22 > a:   # keep a verse number with its next word
            lines.append(cur); cur = []; w = 0; add = tw
        cur.append((kind, s, tw)); w += add
    if cur: lines.append(cur)
    for i, ln in enumerate(lines):
        ensure(LEAD, first_line_hdr)
        a, base = avail(i)
        x = MX + base; y = state['y'] - FS
        prev = None
        for kind, s, tw in ln:
            if kind == 'w':
                if prev == 'w': x += sp
                c.setFont(FONT, FS); c.setFillColor(GRAY); c.drawString(x, y, s); x += tw
            else:
                if prev == 'w': x += sp * 0.8
                c.setFont('KalamB', VFS); c.setFillColor(VGRAY); c.drawString(x, y + 5, s); x += tw
            prev = kind
        state['y'] -= LEAD
    return len(lines)

def render_book(name, slug):
    chapters = load(slug)
    newpage(name)
    toc.append((name, page_no[0]))
    c.bookmarkPage(f'b_{slug}'); c.addOutlineEntry(name, f'b_{slug}', level=0)
    # book title page header: big script title
    c.setFont('Kaushan', 40); c.setFillColor(INK)
    c.drawString(MX, state['y'] - 40, name)
    c.setStrokeColor(INK); c.setLineWidth(1.2)
    c.line(MX, state['y'] - 52, MX + 60*mm, state['y'] - 52)
    state['y'] -= 78
    for n in sorted(chapters):
        seen = set()
        ensure(LEAD * 4 + 10, f'{name} {n}')
        state['hdr'] = f'{name} {n}'
        c.bookmarkPage(f'c_{slug}_{n}', fit='XYZ', top=state['y'] + 6)
        c.addOutlineEntry(f'{name} {n}', f'c_{slug}_{n}', level=1)
        # redraw header with current chapter reference
        c.setFillColor(Color(1,1,1)); c.rect(MX - 1, PH - 14*mm, 90*mm, 7*mm, stroke=0, fill=1)
        header()
        # big chapter numeral
        top = state['y']
        c.setFont('Kaushan', BIG); c.setFillColor(INK)
        c.drawString(MX, top - BIG * 0.80, str(n))
        bigw = pdfmetrics.stringWidth(str(n), 'Kaushan', BIG) + 4*mm
        first = True
        for kind, body in chapters[n]:
            if kind == 'p':
                toks = tokens(body, seen)
                if first and toks and toks[0][0] == 'v' and toks[0][1] == '1': toks = toks[1:]
                draw_tokens(toks, 0, 0, big_lines=2 if first else 0, bigw=bigw)
                first = False
            else:
                for ln in body:
                    toks = tokens(ln, seen)
                    draw_tokens(toks, 9*mm, 15*mm, big_lines=2 if first else 0, bigw=bigw)
                    first = False
                state['y'] -= 5
        # make sure a short chapter still clears the big numeral
        if top - state['y'] < BIG + 6: state['y'] = top - (BIG + 6)
        state['y'] -= 14

# --- front matter: title page + TOC placeholder pages reserved (2 pages) then books
# Title
page_no[0] = 1
c.setFillColor(INK); c.setFont('Kaushan', 44)
c.drawCentredString(PW/2, PH - 95*mm, 'The New Testament')
c.setFont('Kaushan', 26); c.drawCentredString(PW/2, PH - 118*mm, 'Tracing Edition')
c.setStrokeColor(INK); c.setLineWidth(1.2); c.line(PW/2 - 30*mm, PH - 128*mm, PW/2 + 30*mm, PH - 128*mm)
c.setFont(HEAD, 10); c.setFillColor(VGRAY)
c.drawCentredString(PW/2, PH - 142*mm, 'Text: World English Bible (WEB) - public domain')
c.drawCentredString(PW/2, PH - 150*mm, 'Made for stylus use on Samsung Galaxy Tab (16:10)')
c.setFont(HEAD, 9)
c.drawCentredString(PW/2, 40*mm, 'Trace the light gray text with your stylus in any note-taking app (Samsung Notes, Noteshelf, GoodNotes...).')
c.drawCentredString(PW/2, 34*mm, 'Tip: open the PDF in an app that lets you draw on it and duplicate/keep the original as a clean copy.')
# reserve TOC page 2 (filled at the end via second pass) -> we write TOC at page 2 by building book pages first in memory is complex;
# simpler: fixed 1 TOC page; compute afterwards by re-rendering. Do two passes.

# ---- TOC page (page 2) using page numbers from pass 1
TOCF = S + '/gen/toc.json'
prev = json.load(open(TOCF)) if os.path.exists(TOCF) else {}
newpage('Contents')
c.setFont('Kaushan', 30); c.setFillColor(INK); c.drawString(MX, state['y'] - 30, 'Contents')
state['y'] -= 62
c.bookmarkPage('toc'); c.addOutlineEntry('Contents', 'toc', level=0)
for name, slug in BOOKS:
    pg = prev.get(name, '')
    y = state['y'] - 12
    c.setFont(HEAD, 11); c.setFillColor(INK); c.drawString(MX + 4*mm, y, name)
    c.setFillColor(VGRAY)
    nw = pdfmetrics.stringWidth(name, HEAD, 11); pw = pdfmetrics.stringWidth(str(pg), HEAD, 11)
    c.setFont(HEAD, 11)
    c.drawRightString(PW - MX - 4*mm, y, str(pg))
    c.setDash(1, 3); c.setStrokeColor(VGRAY); c.setLineWidth(0.5)
    c.line(MX + 4*mm + nw + 3*mm, y + 1, PW - MX - 4*mm - pw - 3*mm, y + 1); c.setDash()
    c.linkRect('', f'b_{slug}', (MX, y - 4, PW - MX, y + 10), relative=0, thickness=0)
    state['y'] -= 17

for name, slug in BOOKS:
    render_book(name, slug)
c.showPage(); c.save()
json.dump({n: p for n, p in toc}, open(TOCF, 'w'))
print('pages', page_no[0])
