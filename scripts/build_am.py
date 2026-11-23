"""Generate website/am/index.html from website/index.html and i18n/am.json.

Run from anywhere after changing the English page:
    python scripts/build_am.py

The build stops and lists any English text that has no translation, so the
Amharic page can never silently fall out of date.
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "website" / "index.html"
OUT = ROOT / "website" / "am" / "index.html"
SITE = "https://www.zamanatech.com"

# Names and contact details stay as written.
KEEP = {
    "ZamanaTech", "ZamanaMenu", "Marota College", "EthioFund", "Denver Black Limo", "Addis Limo",
    "Lidya Cultura", "Bushaashe Garuwa", "Damarios", "Bushaashe Garuwa Lodge", "Denver Black Limo LLC",
    "Marota Film & Software College", "Ashenafi Bancha", "Elsae Arba", "Mebratu Cheka",
    "AB", "EA", "MC", "M", "E", "D", "QR", "Aa", "Manrope", "Inter", "bushaashegaruwa.com",
    "www.zamanatech.com", "contact@zamanatech.com", "Zamana Technologies PLC", "Wolaita Sodo, Ethiopia",
    "English", "አማርኛ",
}
WA_TEXT = {
    "Hello ZamanaTech, I'd like to talk about a project.": "ሰላም ZamanaTech፣ ስለ አንድ ፕሮጀክት መነጋገር እፈልጋለሁ።",
    "Hello ZamanaTech, I have an idea and I'd like you to create a brand for it.": "ሰላም ZamanaTech፣ አንድ ሐሳብ አለኝ፤ ብራንድ እንድትሠሩልኝ እፈልጋለሁ።",
}
TOKEN = re.compile(r"(<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<svg\b.*?</svg>|<[^>]+>)", re.S | re.I)
ATTR = re.compile(r'\b(aria-label|alt|title|placeholder)="([^"]*)"')
META = re.compile(r'(<meta\s+(?:name="description"|property="og:(?:title|description)")\s+content=")([^"]*)(")')

tr = json.loads((ROOT / "i18n" / "am.json").read_text(encoding="utf-8"))
missing = []


def translate(raw):
    key = " ".join(html.unescape(raw).split())
    if not key or not re.search(r"[A-Za-z]", key) or key in KEEP:
        return raw
    if key not in tr:
        missing.append(key)
        return raw
    lead = raw[: len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()) :]
    return lead + html.escape(tr[key], quote=False) + trail


def tag(token):
    if token.startswith(("<!--", "<script", "<style", "<svg")):
        return token
    return ATTR.sub(lambda m: f'{m[1]}="{translate(m[2])}"', token)


page = SRC.read_text(encoding="utf-8")
page = META.sub(lambda m: m[1] + translate(m[2]) + m[3], page)
parts = TOKEN.split(page)
in_card = False
for i, part in enumerate(parts):
    if i % 2:
        if 'class="bb-card bb-back"' in part:
            in_card = True
        elif 'class="bb-swatches"' in part:
            in_card = False
        if not in_card and not part.startswith("<meta"):
            parts[i] = tag(part)
    elif not in_card:
        parts[i] = translate(part)
page = "".join(parts)

if missing:
    print("Missing Amharic translations:", file=sys.stderr)
    for item in dict.fromkeys(missing):
        print(" -", item, file=sys.stderr)
    sys.exit(1)

for en, am in WA_TEXT.items():
    encoded = quote(en, safe="")
    variants = {encoded, encoded.replace("%27", "'"), quote(en, safe=",'")}
    variants.add(en.replace(" ", "%20").replace(",", "%2C").replace("'", "%27"))
    for v in variants:
        page = page.replace("text=" + v, "text=" + quote(am, safe=""))

page = page.replace('<html lang="en">', '<html lang="am">', 1)
page = re.sub(r'\b(href|src)="(assets/|styles\.css|main\.js|site\.webmanifest)', r'\1="../\2', page)
page = page.replace('family=Inter:', 'family=Noto+Sans+Ethiopic:wght@400;500;600;700;800&family=Inter:', 1)
page = page.replace(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{SITE}/am/">')
page = page.replace(f'<meta property="og:url" content="{SITE}/">', f'<meta property="og:url" content="{SITE}/am/">')
page = page.replace(
    '<a class="lang-switch" href="am/" hreflang="am" lang="am" aria-label="ወደ አማርኛ ቀይር">አማርኛ</a>',
    '<a class="lang-switch" href="../" hreflang="en" lang="en" aria-label="Switch to English">English</a>',
)

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(page, encoding="utf-8", newline="\n")
print(f"Built {OUT.relative_to(ROOT)} ({len(tr)} translations)")
