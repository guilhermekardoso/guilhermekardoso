#!/usr/bin/env python3
"""Local preview of a GitHub profile README.

Usage: python tools/preview.py [port]

Renders ../README.md through GitHub's POST /markdown API (only when the file
changes, with an on-disk cache so the anonymous 60 req/h quota lasts), then
wraps it in the same markup as the profile page, using GitHub's current CSS.
Set GITHUB_TOKEN to raise the quota.

What this does NOT reproduce: Camo, GitHub's page CSP, the real <themed-picture>
component, Mermaid/math rendering, alerts. Validate those on github.com.
"""
import hashlib
import http.server
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CACHE = ROOT / ".preview-cache"
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "readme-local-preview"}
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8792

# Measured on github.com at a 1536 px window: 846 px article inside a 16 px padded Box.
DESKTOP_W, MOBILE_W = 880, 390


def fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def github_css():
    """Download GitHub's current stylesheets once; returns local names."""
    index = CACHE / "css-index.json"
    if index.exists():
        return json.loads(index.read_text())
    page = fetch("https://github.com/guilhermekardoso").decode("utf8", "replace")
    names = []
    urls = re.findall(r'href="(https://github\.githubassets\.com/assets/[^"]+\.css)"', page)
    for url in urls:
        name = url.rsplit("/", 1)[1]
        (CACHE / name).write_bytes(fetch(url))
        names.append(name)
    index.write_text(json.dumps(names))
    return names


# POST /markdown ejects <img> from <a><picture>, but real READMEs keep it inside
# (checked on vercel/next.js). Undo that here so the preview matches production.
EJECTED = re.compile(
    r'(<a\b[^>]*>\s*<themed-picture[^>]*><picture>(?:(?!</picture>).)*?)'
    r'\s*</picture></themed-picture>\s*</a>\s*'
    r'<a target="_blank"[^>]*>(<img\b[^>]*>)</a>',
    re.S,
)
# POST /markdown also wraps the <img> of an unlinked <picture> in <a>, which makes
# browsers ignore every <source>. Production has no such link (checked on Platane's profile).
WRAPPED = re.compile(r'(<picture>(?:(?!</picture>).)*?)<a target="_blank"[^>]*>(<img\b[^>]*>)</a>(\s*</picture>)', re.S)


def match_production(html):
    html = EJECTED.sub(r"\1\2</picture></themed-picture></a>", html)
    return WRAPPED.sub(r"\1\2\3", html)


def render_markdown():
    text = README.read_bytes()
    digest = hashlib.sha256(text).hexdigest()[:16]
    cached = CACHE / f"render-{digest}.html"
    if cached.exists():
        return match_production(cached.read_text(encoding="utf8")), digest, None
    headers = {"Content-Type": "text/plain"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        html = fetch("https://api.github.com/markdown/raw", data=text, headers=headers).decode("utf8")
    except urllib.error.HTTPError as err:
        renders = sorted(CACHE.glob("render-*.html"), key=lambda p: p.stat().st_mtime)
        stale = renders[-1].read_text(encoding="utf8") if renders else ""
        return match_production(stale), digest, f"API respondeu {err.code}: mostrando a última versão renderizada."
    cached.write_text(html, encoding="utf8")
    return match_production(html), digest, None


PAGE = """<!doctype html>
<html lang="en" data-color-mode="{theme}" data-light-theme="light" data-dark-theme="dark">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>README ({theme})</title>{links}
<style>body{{margin:0;padding:0;background:var(--bgColor-default,#0d1117)}}
.warn{{background:#9e6a03;color:#fff;font:13px sans-serif;padding:6px 16px}}</style></head>
<body data-digest="{digest}">{warn}
<div class="Box-body" style="padding:16px;border:0"><article class="markdown-body entry-content container-lg" itemprop="text">{body}</article></div>
<script>
const theme="{theme}", motion="{motion}";
// Stand-in for GitHub's <themed-picture>: resolve theme and motion from the query string.
for (const s of document.querySelectorAll("picture source[media]")) {{
  let m = s.media
    .replace(/\\(prefers-color-scheme:\\s*(\\w+)\\)/g, (_, v) => v === theme ? "all" : "not all")
    .replace(/\\(prefers-reduced-motion:\\s*(\\w+)\\)/g, (_, v) => (v === "reduce") === (motion === "reduce") ? "all" : "not all");
  // "not all and (x)" would negate the whole query, so a failed condition disables the source.
  s.media = m.includes("not all") ? "not all" : m;
}}
const send = () => parent.postMessage({{h: document.documentElement.scrollHeight, id: "{frame}"}}, "*");
addEventListener("load", send); new ResizeObserver(send).observe(document.body);
</script></body></html>"""

VIEWER = f"""<!doctype html><html><head><meta charset="utf-8"><title>README preview</title><style>
body{{margin:0;background:#2b2f36;color:#ddd;font:13px system-ui,sans-serif}}
header{{position:sticky;top:0;z-index:2;background:#16181d;padding:8px 14px;display:flex;gap:14px;align-items:center}}
main{{display:flex;gap:16px;padding:16px;align-items:flex-start;width:max-content}}
figure{{margin:0}} figcaption{{padding:0 0 6px}} iframe{{border:0;display:block;background:#fff}}
</style></head><body><header><b>README preview</b>
<label><input type="checkbox" id="m"> reduzir movimento</label>
<span id="s">aguardando alterações em README.md e assets/</span></header><main id="g"></main>
<script>
const V=[["desktop-dark",{DESKTOP_W},"dark"],["desktop-light",{DESKTOP_W},"light"],["mobile-dark",{MOBILE_W},"dark"],["mobile-light",{MOBILE_W},"light"]];
const g=document.getElementById("g"),m=document.getElementById("m"),s=document.getElementById("s");
function draw(){{g.innerHTML="";for(const [n,w,t] of V){{const f=document.createElement("figure");
f.innerHTML=`<figcaption>${{n}} (${{w}} px)</figcaption><iframe id="${{n}}" width="${{w}}" height="600" src="/render?theme=${{t}}&motion=${{m.checked?"reduce":"no-preference"}}&frame=${{n}}"></iframe>`;g.append(f)}}}}
addEventListener("message",e=>{{const f=document.getElementById(e.data.id);if(f)f.height=e.data.h}});
m.onchange=draw;draw();let v=null;
setInterval(async()=>{{const r=await(await fetch("/version")).text();if(v&&r!==v){{s.textContent="atualizado "+new Date().toLocaleTimeString();draw()}}v=r}},1000);
</script></body></html>"""


def version():
    files = [README, *ROOT.glob("assets/**/*")]
    return str(max(f.stat().st_mtime_ns for f in files if f.is_file()))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_text(self, text, ctype="text/html; charset=utf-8"):
        body = text.encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        if path == "/":
            return self.send_text(VIEWER)
        if path == "/version":
            return self.send_text(version(), "text/plain")
        if path == "/render":
            body, digest, warn = render_markdown()
            links = "".join(f'<link rel="stylesheet" href="/.preview-cache/{n}">' for n in github_css())
            return self.send_text(PAGE.format(
                theme=params.get("theme", "dark"), motion=params.get("motion", "no-preference"),
                frame=params.get("frame", ""), digest=digest, links=links, body=body,
                warn=f'<div class="warn">{warn}</div>' if warn else "",
            ))
        return super().do_GET()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"http://127.0.0.1:{PORT}", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
