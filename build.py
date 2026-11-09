#!/usr/bin/env python3
"""Build the site into _site/.

Everything you edit lives in content/ and files/:
  site.yml                 name, affiliation, links
  content/home.md          home page text
  content/research/*.md    one file per paper (front matter + abstract)
  content/teaching/*.md    one file per course
  files/*                  PDFs, slides, CV (copied to /files/)
Files whose name starts with "_" are ignored.
"""
import html
import re
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
MD = markdown.Markdown(extensions=["extra", "smarty"])

SECTIONS = [  # (slug, label)
    ("index", "Home"),
    ("research", "Research"),
    ("teaching", "Teaching"),
    ("cv", "CV"),
    ("contact", "Contact"),
]
STATUS_ORDER = [
    ("publication", "Publications"),
    ("working-paper", "Working papers"),
    ("work-in-progress", "Work in progress"),
]


def read(path):
    """Return (front-matter dict, body html)."""
    text = path.read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        text = m.group(2)
    MD.reset()
    return meta, MD.convert(text)


def items(folder):
    out = []
    for p in sorted((ROOT / "content" / folder).glob("*.md")):
        if p.name.startswith("_"):
            continue
        meta, body = read(p)
        if meta.get("draft"):
            continue
        out.append((meta, body))
    return out


def e(s):
    return html.escape(str(s))


def page(slug, title, body, cfg):
    nav = "".join(
        f'<a href="{"/" if s == "index" else f"/{s}/"}"{" class=on" if s == slug else ""}>{l}</a>'
        for s, l in SECTIONS
    )
    t = cfg["name"] if slug == "index" else f'{title} · {cfg["name"]}'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t)}</title>
<link rel="stylesheet" href="/assets/style.css"></head>
<body><div class="wrap">
<header><a class="name" href="/">{e(cfg["name"])}</a><nav>{nav}</nav></header>
<main>{body}</main>
<footer>Last updated {e(cfg["_built"])}</footer>
</div></body></html>"""


def write(slug, html_text):
    d = OUT if slug == "index" else OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html_text, encoding="utf-8")


def links(meta):
    parts = []
    for key, label in [("pdf", "PDF"), ("slides", "Slides"), ("code", "Code"), ("data", "Data")]:
        v = meta.get(key)
        if v:
            href = v if str(v).startswith("http") else f"/files/{v}"
            parts.append(f'<a href="{e(href)}">{label}</a>')
    if meta.get("url"):
        parts.append(f'<a href="{e(meta["url"])}">Journal / SSRN</a>')
    return " · ".join(parts)


def paper(meta, body):
    co = f'<div class="co">with {e(meta["coauthors"])}</div>' if meta.get("coauthors") else ""
    venue = f'<div class="venue">{e(meta["venue"])}</div>' if meta.get("venue") else ""
    ln = links(meta)
    abstract = (
        f'<details><summary>Abstract</summary>{body}</details>' if body.strip() else ""
    )
    return (
        f'<article class="item"><h3>{e(meta.get("title", "Untitled"))}</h3>{co}{venue}'
        f'{abstract}<div class="links">{ln}</div></article>'
    )


def build():
    cfg = yaml.safe_load((ROOT / "site.yml").read_text())
    import datetime

    cfg["_built"] = datetime.date.today().strftime("%d %B %Y")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    shutil.copytree(ROOT / "files", OUT / "files", ignore=shutil.ignore_patterns(".gitkeep"))
    (OUT / ".nojekyll").touch()

    # Home
    _, home = read(ROOT / "content" / "home.md")
    photo = cfg.get("photo")
    img = f'<img class="photo" src="/files/{e(photo)}" alt="{e(cfg["name"])}">' if photo and (ROOT / "files" / photo).exists() else ""
    side = f'<aside>{img}<p>{e(cfg.get("position", ""))}<br>{e(cfg.get("affiliation", ""))}</p>{ext_links(cfg)}</aside>'
    write("index", page("index", "Home", f'<div class="home"><div>{home}</div>{side}</div>', cfg))

    # Research
    papers = items("research")
    body = "<h1>Research</h1>"
    if cfg.get("research_interests"):
        body += f'<p class="lede">{e(cfg["research_interests"])}</p>'
    for status, label in STATUS_ORDER:
        group = [p for p in papers if p[0].get("status", "working-paper") == status]
        group.sort(key=lambda p: -int(p[0].get("year", 0)))
        if group:
            body += f"<h2>{label}</h2>" + "".join(paper(m, b) for m, b in group)
    if not papers:
        body += "<p>Papers will appear here.</p>"
    write("research", page("research", "Research", body, cfg))

    # Teaching
    courses = items("teaching")
    courses.sort(key=lambda c: -int(c[0].get("year", 0)))
    body = "<h1>Teaching</h1>"
    for m, b in courses:
        sub = " · ".join(e(m[k]) for k in ("role", "institution", "term") if m.get(k))
        body += f'<article class="item"><h3>{e(m.get("title", ""))}</h3><div class="venue">{sub}</div>{b}<div class="links">{links(m)}</div></article>'
    if not courses:
        body += "<p>Teaching information will appear here.</p>"
    write("teaching", page("teaching", "Teaching", body, cfg))

    # CV
    cv = cfg.get("cv_file", "cv.pdf")
    if (ROOT / "files" / cv).exists():
        body = (f'<h1>CV</h1><p><a href="/files/{e(cv)}">Download CV (PDF)</a></p>'
                f'<object class="cv" data="/files/{e(cv)}" type="application/pdf"></object>')
    else:
        body = f"<h1>CV</h1><p>Add your CV as <code>files/{e(cv)}</code>.</p>"
    write("cv", page("cv", "CV", body, cfg))

    # Contact
    _, contact = read(ROOT / "content" / "contact.md")
    body = f"<h1>Contact</h1>{contact}"
    if cfg.get("email"):
        body += f'<p>Email: <a href="mailto:{e(cfg["email"])}">{e(cfg["email"])}</a></p>'
    write("contact", page("contact", "Contact", body, cfg))

    print(f"Built {len(papers)} papers, {len(courses)} courses -> {OUT}")


def ext_links(cfg):
    out = [f'<a href="{e(u)}">{e(l)}</a>' for l, u in (cfg.get("links") or {}).items()]
    return '<p class="ext">' + " · ".join(out) + "</p>" if out else ""


if __name__ == "__main__":
    build()
