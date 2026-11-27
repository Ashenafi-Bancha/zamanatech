"""Build every page of zamanatech.com from one source file.

    python scripts/build.py

Source:   src/site.html  (the full site, edit content here)
          i18n/am.json   (English -> Amharic translations)
Output:   website/*.html, website/am/*.html, website/sitemap.xml

Each page gets its own sections, title, description, canonical URL and
Amharic twin. The build stops and lists any English text without an Amharic
translation, so the two languages can never drift apart.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "site.html"
WEB = ROOT / "website"
SITE = "https://www.zamanatech.com"
VERSION = "20261207"

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
# slug: (nav label, <title>, meta description, sections)
PAGES = {
    "": ("Home", "ZamanaTech — Innovating Beyond Tomorrow",
         "Zamana Technologies PLC is a technology and innovation company in Wolaita Sodo, Ethiopia, building software, AI, cloud and secure digital solutions.",
         ["Hero", "Clients", "Services", "Why a website", "Work / Portfolio", "Why ZamanaTech", "Testimonials"]),
    "about": ("About", "About Us | ZamanaTech",
              "Learn about Zamana Technologies PLC, a technology and innovation company in Wolaita Sodo, Ethiopia: our vision, mission, values and expertise.",
              ["About", "Expertise", "Why ZamanaTech"]),
    "services": ("Services", "Services: Websites, Mobile Apps, ERP & AI | ZamanaTech",
                 "Websites, Android and iOS apps, ERP and business management systems, Telegram bots, AI, cloud, cybersecurity and digital support for businesses in Ethiopia.",
                 ["Services", "Why a website"]),
    "branding": ("Branding & design", "Branding & Logo Design | ZamanaTech",
                 "Tell us your idea and we turn it into a brand: logo design, colors, business cards, stamps, social media kits, signage and brand guidelines.",
                 ["Branding"]),
    "work": ("Work", "Our Work & Portfolio | ZamanaTech",
             "See ZamanaMenu and the websites, apps and platforms ZamanaTech has built for clients in hospitality, fintech, education, transport and culture.",
             ["Work / Portfolio", "Testimonials"]),
    "team": ("Team", "Our Team | ZamanaTech",
             "Meet the engineers behind ZamanaTech, former Wolaita Liqa School students now building software, ERP and AI solutions.",
             ["Team"]),
    "approach": ("Approach", "How We Work | ZamanaTech",
                 "Our four-step approach: discover, strategize, build and evolve, keeping you involved from the first conversation to continuous improvement.",
                 ["Approach"]),
    "faq": ("FAQ", "Frequently Asked Questions | ZamanaTech",
            "Answers about ZamanaTech services, ZamanaMenu, website benefits, pricing, timelines, support after launch and how to get started.",
            ["FAQ"]),
    "contact": ("Contact", "Contact Us | ZamanaTech",
                "Contact ZamanaTech in Wolaita Sodo, Ethiopia. Call or WhatsApp +251 949 685 555 or email contact@zamanatech.com. We reply within 24 hours.",
                ["Contact"]),
}

# Old one-page anchors -> new page URLs (anchors that still exist on a page keep their hash)
LINKS = {
    "#top": "/", "#home": "/", "#about": "/about", "#services": "/services", "#work": "/work",
    "#team": "/team", "#approach": "/approach", "#faq": "/faq", "#contact": "/contact",
    "#branding": "/branding", "#why-website": "/services#why-website", "#expertise": "/about#expertise",
}
NAV = ["", "about", "services", "work", "team", "approach", "faq"]
HOME_WORK_CARDS = 3
JSONLD = ('<script type="application/ld+json">' + json.dumps({
    "@context": "https://schema.org", "@type": "Organization", "name": "Zamana Technologies PLC",
    "alternateName": "ZamanaTech", "url": SITE + "/", "logo": SITE + "/assets/android-chrome-512x512.png",
    "email": "contact@zamanatech.com", "telephone": "+251949685555",
    "address": {"@type": "PostalAddress", "addressLocality": "Wolaita Sodo", "addressCountry": "ET"},
    "sameAs": ["https://www.linkedin.com/company/zamanatech", "https://www.facebook.com/zamanatech",
               "https://www.instagram.com/zamanatech", "https://t.me/zamanatech", "https://x.com/zamanatech",
               "https://github.com/zamanatech"],
}, ensure_ascii=False) + "</script>")

# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
KEEP = {
    "ZamanaTech", "ZamanaMenu", "Marota College", "EthioFund", "Denver Black Limo", "Addis Limo",
    "Lidya Cultura", "Bushaashe Garuwa", "Damarios", "Bushaashe Garuwa Lodge", "Denver Black Limo LLC",
    "Marota Film & Software College", "Ashenafi Bancha", "Elsae Arba", "Mebratu Cheka",
    "AB", "EA", "MC", "M", "E", "D", "QR", "Aa", "Manrope", "Inter", "bushaashegaruwa.com", "BrokerSodo", "brokersodo.com", "Lidya Cultural Food", "Lidya Cultural Food Zone & Catering", "Dallas Café & Booth", "denverblacklimo.llc", "marota.tech", "ethiofund.com", "addislimo.com", "lidyaculturalfood.com",
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

TR = json.loads((ROOT / "i18n" / "am.json").read_text(encoding="utf-8"))
missing = []


def tr_text(raw):
    key = " ".join(html.unescape(raw).split())
    if not key or not re.search(r"[A-Za-z]", key) or key in KEEP:
        return raw
    if key not in TR:
        missing.append(key)
        return raw
    lead = raw[: len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()):]
    return lead + html.escape(TR[key], quote=False) + trail


def to_amharic(page):
    page = META.sub(lambda m: m[1] + tr_text(m[2]) + m[3], page)
    parts = TOKEN.split(page)
    in_card = False
    for i, part in enumerate(parts):
        if i % 2:
            if 'class="bb-card bb-back"' in part:
                in_card = True
            elif 'class="bb-swatches"' in part:
                in_card = False
            if not in_card and not part.startswith(("<meta", "<!--", "<script", "<style", "<svg")):
                parts[i] = ATTR.sub(lambda m: f'{m[1]}="{tr_text(m[2])}"', part)
        elif not in_card:
            parts[i] = tr_text(part)
    page = "".join(parts)
    for en, am in WA_TEXT.items():
        page = page.replace("text=" + quote(en, safe=""), "text=" + quote(am, safe=""))
    page = page.replace('<html lang="en">', '<html lang="am">', 1)
    page = page.replace("family=Inter:", "family=Noto+Sans+Ethiopic:wght@400;500;600;700;800&family=Inter:", 1)
    # internal page links -> Amharic pages
    page = re.sub(r'href="/(?=[a-z#"])', 'href="/am/', page)
    page = page.replace('href="/am/"', 'href="/am"')
    page = re.sub(r'href="/am/(assets|styles\.css|main\.js|site\.webmanifest)', r'href="/\1', page)
    return page


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------
def url(slug, am=False):
    path = ("/am" if am else "") + ("/" + slug if slug else ("" if am else "/"))
    return SITE + path


def build_page(slug, src, sections):
    label, title, desc, wanted = PAGES[slug]
    head, header, main, tail = src["head"], src["header"], src["main"], src["tail"]

    body = []
    for n, name in enumerate(wanted):
        block = sections[name]
        if slug == "" and name == "Services":
            block = re.sub(r'\n        <div class="offers">.*?\n        </div>\n(?=      </div>\n    </section>)', "\n", block, flags=re.S)
            block = block.replace("\n      </div>\n    </section>", '\n        <p class="more-link reveal"><a href="/services" class="btn btn-outline-dark">Explore all services <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h11m-4-4 4 4-4 4"/></svg></a></p>\n      </div>\n    </section>', 1)
        if slug == "" and name == "Work / Portfolio":
            cards = re.findall(r'(?m)^          <!-- [^>]+ -->\n          <article class="work-card.*?</article>\n\n?', block, re.S)
            for c in cards[HOME_WORK_CARDS:]:
                block = block.replace(c, "")
            block = block.replace("\n      </div>\n    </section>", '\n        <p class="more-link reveal"><a href="/work" class="btn btn-outline-dark">See all projects <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h11m-4-4 4 4-4 4"/></svg></a></p>\n      </div>\n    </section>', 1)
        if slug and n == 0:
            # the page's main section: h2 -> h1, room for the fixed header
            block = re.sub(r'<section class="section ', '<section class="section page-first ', block, count=1)
            block = re.sub(r"<h2\b([^>]*)>(.*?)</h2>", r"<h1\1>\2</h1>", block, count=1, flags=re.S)
        body.append(block)
    page_main = main.replace("{{SECTIONS}}", "".join(body))

    # header: solid on inner pages, active nav item
    hdr = header
    if slug:
        hdr = hdr.replace('<header class="site-header"', '<header class="site-header site-header--solid"', 1)
    for s in NAV:
        href = "/" + s
        cur = ' class="is-active" aria-current="page"' if s == slug else ""
        hdr = hdr.replace(f'<a href="{LINKS["#" + (s or "home")]}">', f'<a href="{href}"{cur}>', 1)

    page = head + hdr + page_main + tail

    # SEO head
    page = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", page, count=1)
    page = re.sub(r'(<meta name="description" content=")[^"]*', r"\g<1>" + desc.replace("\\", ""), page, count=1)
    page = re.sub(r'(<meta property="og:title" content=")[^"]*', r"\g<1>" + title, page, count=1)
    page = re.sub(r'(<meta property="og:description" content=")[^"]*', r"\g<1>" + desc, page, count=1)
    page = page.replace("{{CANONICAL}}", url(slug)).replace("{{EN_URL}}", url(slug)).replace("{{AM_URL}}", url(slug, True))
    page = page.replace("{{LANG_HREF}}", "/am" + ("/" + slug if slug else ""))
    page = page.replace("{{JSONLD}}", JSONLD if not slug else "")
    return page


def crumbs_jsonld(slug, am):
    label = PAGES[slug][0]
    names = (TR["Home"], TR[label]) if am else ("Home", label)
    items = [{"@type": "ListItem", "position": 1, "name": names[0], "item": url("", am)},
             {"@type": "ListItem", "position": 2, "name": names[1], "item": url(slug, am)}]
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


def split_source():
    raw = SRC.read_text(encoding="utf-8")
    raw = re.sub(r"(styles\.css|main\.js)\?v=\d+", rf"\1?v={VERSION}", raw)
    for a, b in LINKS.items():
        raw = raw.replace(f'href="{a}"', f'href="{b}"')
    raw = re.sub(r'\b(href|src)="(assets/|styles\.css|main\.js|site\.webmanifest)', r'\1="/\2', raw)
    raw = raw.replace('content="assets/og-image.png"', f'content="{SITE}/assets/og-image.png"')

    head, rest = raw.split("<body>\n", 1)
    head += "<body>\n"
    header, rest = rest.split("  <main id=\"main\">\n", 1)
    main_inner, tail = rest.split("  </main>\n", 1)
    marks = list(re.finditer(r"    <!-- ========== (.+?) ========== -->\n", main_inner))
    sections = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(main_inner)
        sections[m[1]] = main_inner[m.start():end].rstrip() + "\n\n"
    return {"head": head, "header": header, "main": '  <main id="main">\n\n{{SECTIONS}}  </main>\n', "tail": tail}, sections


def main():
    src, sections = split_source()
    for slug, (_, _, _, wanted) in PAGES.items():
        unknown = [w for w in wanted if w not in sections]
        if unknown:
            sys.exit(f"Unknown section(s) for /{slug}: {unknown}. Available: {list(sections)}")

    (WEB / "am").mkdir(exist_ok=True)
    built = []
    for slug in PAGES:
        en = build_page(slug, src, sections)
        am = to_amharic(en)
        am = am.replace(f'<link rel="canonical" href="{url(slug)}">', f'<link rel="canonical" href="{url(slug, True)}">')
        am = am.replace(f'<meta property="og:url" content="{url(slug)}">', f'<meta property="og:url" content="{url(slug, True)}">')
        am = am.replace('<a class="lang-switch" href="/am/am', '<a class="lang-switch" href="/am')
        am = re.sub(r'<a class="lang-switch" href="[^"]*" hreflang="am" lang="am" aria-label="[^"]*">አማርኛ</a>',
                    f'<a class="lang-switch" href="/{slug}" hreflang="en" lang="en" aria-label="Switch to English">English</a>', am)
        if slug:  # breadcrumb for Google only, not shown on the page
            en = en.replace("</head>", crumbs_jsonld(slug, False) + "\n</head>", 1)
            am = am.replace("</head>", crumbs_jsonld(slug, True) + "\n</head>", 1)
        name = (slug or "index") + ".html"
        (WEB / name).write_text(en, encoding="utf-8", newline="\n")
        (WEB / "am" / name).write_text(am, encoding="utf-8", newline="\n")
        built.append(slug)

    if missing:
        print("Missing Amharic translations:", file=sys.stderr)
        for item in dict.fromkeys(missing):
            print(" -", item, file=sys.stderr)
        sys.exit(1)

    today = date.today().isoformat()
    rows = []
    for slug in built:
        for am in (False, True):
            rows.append(
                f"  <url>\n    <loc>{url(slug, am)}</loc>\n    <lastmod>{today}</lastmod>\n"
                f'    <xhtml:link rel="alternate" hreflang="en" href="{url(slug)}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="am" href="{url(slug, True)}"/>\n'
                f"    <priority>{'1.0' if not slug else '0.8'}</priority>\n  </url>")
    (WEB / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(rows) + "\n</urlset>\n", encoding="utf-8", newline="\n")
    print(f"Built {len(built)} pages x 2 languages, sitemap with {len(rows)} URLs")


if __name__ == "__main__":
    main()
