#!/usr/bin/env python3
"""Rebuild sub-pages: embed sub-README content instead of broken links."""
import urllib.request
import os, re, html as html_mod, json

BASE = r'C:\Users\중진공39\mcp-site'
RAW = 'https://raw.githubusercontent.com/microsoft/mcp-for-beginners/main'
TREE = 'https://github.com/microsoft/mcp-for-beginners/tree/main'

CACHE = {}

TAILWIND_CONFIG = '''"colors": {
  "background-surface": "#F8FAFC","surface-container-highest": "#d5e3fd","on-surface": "#0d1c2f",
  "on-secondary": "#ffffff","secondary-fixed-dim": "#a2c9ff","tertiary": "#974700",
  "on-primary-fixed": "#001c39","error-container": "#ffdad6","outline": "#717783",
  "tertiary-fixed": "#ffdbc8","on-primary": "#ffffff","on-primary-fixed-variant": "#004883",
  "on-tertiary-fixed": "#311300","on-tertiary-container": "#ffffff",
  "glass-fill": "rgba(255, 255, 255, 0.7)","on-secondary-fixed": "#001c38",
  "on-secondary-fixed-variant": "#004881","surface-container-lowest": "#ffffff",
  "tertiary-fixed-dim": "#ffb689","surface-dim": "#ccdbf4","inverse-surface": "#233144",
  "on-primary-container": "#ffffff","primary-container": "#0078d4","secondary-container": "#78b4fe",
  "on-secondary-container": "#00457b","success-green": "#34D399","on-background": "#0d1c2f",
  "surface-container-low": "#eff4ff","surface-bright": "#f8f9ff","surface-container-high": "#dde9ff",
  "inverse-on-surface": "#ebf1ff","tertiary-container": "#bc5b00","secondary": "#1260a5",
  "error": "#ba1a1a","primary-fixed": "#d3e3ff","primary-fixed-dim": "#a3c9ff",
  "on-tertiary": "#ffffff","surface-tint": "#0060ab","background": "#f8f9ff","surface": "#f8f9ff",
  "on-primary": "#ffffff","on-error": "#ffffff","outline-variant": "#c2c7cf",
  "code-bg": "#0F172A","card": "#ffffff","accent": "#06b6d4","on-accent": "#ffffff",
  "primary-container": "#0078d4","surface-container": "#e6eeff","surface-variant": "#d5e3fd",
  "inverse-primary": "#a3c9ff","primary": "#005faa","on-error-container": "#93000a",
  "on-surface-variant": "#404752","secondary-fixed": "#d3e4ff","on-tertiary-fixed-variant": "#743500"
}'''

def fetch(url):
    if url in CACHE:
        return CACHE[url]
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            text = r.read().decode('utf-8')
            CACHE[url] = text
            return text
    except:
        CACHE[url] = ''
        return ''

def fetch_md(folder, ko=False):
    p = 'translations/ko/' if ko else ''
    return fetch(f'{RAW}/{p}{folder}/README.md')

def fetch_sg(ko=False):
    p = 'translations/ko/' if ko else ''
    return fetch(f'{RAW}/{p}study_guide.md')

def find_sub_md_links(md, folder, ko=False):
    """Find relative README links like [text](somepath/README.md)"""
    pattern = r'\[([^\]]+)\]\(([^)]*README\.md)\)'
    links = []
    for m in re.finditer(pattern, md):
        text, url = m.group(1), m.group(2)
        if not url.startswith('http'):
            # Relative link
            p = 'translations/ko/' if ko else ''
            full_url = f'{RAW}/{p}{folder}/{url}'
            links.append((text, url, full_url))
    return links

def fetch_sub_readme(folder, sub_path, ko=False):
    p = 'translations/ko/' if ko else ''
    return fetch(f'{RAW}/{p}{folder}/{sub_path}')

def md_to_html(md, folder=None, ko=False):
    lines = md.split('\n')
    out = []
    in_code = False
    buf = []
    for line in lines:
        if line.startswith('```'):
            if in_code:
                out.append('<pre class="bg-inverse-surface text-white rounded-xl p-4 overflow-x-auto text-sm mb-4 leading-relaxed"><code>')
                for c in buf:
                    out.append(html_mod.escape(c) + '\n')
                out.append('</code></pre>')
                buf = []; in_code = False
            else:
                in_code = True
            continue
        if in_code:
            buf.append(line)
            continue
        if line.startswith('### '):
            out.append(f'<h4 class="font-headline-md text-headline-md text-on-surface mt-8 mb-3">{line[4:]}</h4>')
        elif line.startswith('## '):
            out.append(f'<h3 class="font-headline-lg text-headline-lg text-on-surface mt-10 mb-4">{line[3:]}</h3>')
        elif line.startswith('# '):
            out.append(f'<h2 class="font-headline-xl text-headline-xl text-on-surface mt-12 mb-6">{line[2:]}</h2>')
        elif line.startswith('- '):
            t = line[2:]
            # Check if this line has a sub-readme link
            sub_match = re.search(r'\[([^\]]+)\]\(([^)]*README\.md)\)', t)
            if sub_match and folder:
                sub_url = sub_match.group(2)
                sub_text = sub_match.group(1)
                if not sub_url.startswith('http'):
                    p = 'translations/ko/' if ko else ''
                    sub_content = fetch(f'{RAW}/{p}{folder}/{sub_url}')
                    if sub_content:
                        # Replace the link text to indicate expanded content
                        t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', t)
                        t = re.sub(r'`([^`]+)`', r'<code class="bg-surface-container-high px-1.5 py-0.5 rounded text-sm font-mono">\1</code>', t)
                        t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
                        out.append(f'<li class="ml-5 list-disc text-on-surface-variant mb-1 leading-relaxed">{t}</li>')
                        # Embed sub-content in a styled box
                        sub_html = md_to_html(sub_content)
                        out.append(f'<div class="ml-8 mb-3 mt-2 bg-surface-container-low rounded-xl p-4 border border-outline-variant/20">')
                        out.append(sub_html)
                        out.append('</div>')
                        continue
            # No sub-readme or not found - normal list item
            t = re.sub(r'`([^`]+)`', r'<code class="bg-surface-container-high px-1.5 py-0.5 rounded text-sm font-mono">\1</code>', t)
            t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
            t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<a href="{m.group(2)}" class="text-primary underline" target="_blank">{m.group(1)}</a>', t)
            out.append(f'<li class="ml-5 list-disc text-on-surface-variant mb-2 leading-relaxed">{t}</li>')
        elif line.strip() == '':
            out.append('')
        elif not line.startswith('!') and not line.startswith('['):
            t = re.sub(r'`([^`]+)`', r'<code class="bg-surface-container-high px-1.5 py-0.5 rounded text-sm font-mono">\1</code>', line)
            t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
            t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<a href="{m.group(2)}" class="text-primary underline" target="_blank">{m.group(1)}</a>', t)
            if len(t) > 250:
                parts = re.split(r'(?<=[.!?])\s+(?=[A-Z\uAC00-\uD7A3])', t)
                if len(parts) > 1:
                    for p in parts:
                        p = p.strip()
                        if p: out.append(f'<p class="text-body-md text-on-surface-variant mb-3 leading-relaxed">{p}</p>')
                else:
                    out.append(f'<p class="text-body-md text-on-surface-variant mb-3 leading-relaxed">{t}</p>')
            else:
                out.append(f'<p class="text-body-md text-on-surface-variant mb-3 leading-relaxed">{t}</p>')
    if in_code:
        out.append('<pre class="bg-inverse-surface text-white rounded-xl p-4 overflow-x-auto text-sm mb-4"><code>')
        for c in buf:
            out.append(html_mod.escape(c) + '\n')
        out.append('</code></pre>')
    return '\n'.join(out)

PAGE_TPL = '''<!DOCTYPE html>
<html class="light" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title} - MCP Curriculum</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script>
tailwind.config = {{
  darkMode: "class",
  theme: {{
    extend: {{
      {colors}
    }}
  }}
}}
</script>
<style>
body {{ font-family: 'Inter', sans-serif; background-color: #f8f9ff; }}
.glass {{ background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(12px); }}
.material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
.scroll-mt-24 {{ scroll-margin-top: 6rem; }}
.lang-content {{ display: none; }}
.lang-content.active {{ display: block; }}
</style>
</head>
<body class="text-on-background">
<header class="fixed top-0 w-full z-50 glass backdrop-blur-md border-b border-outline-variant shadow-sm h-16">
<div class="max-w-container-max mx-auto px-md flex justify-between items-center h-full">
<div class="flex items-center gap-xs">
<span class="material-symbols-outlined text-primary text-3xl">extension</span>
<span class="text-headline-md font-headline-md font-bold text-on-surface">MCP Curriculum</span>
</div>
<nav class="hidden md:flex gap-lg items-center">
  {nav}
</nav>
<div class="flex items-center gap-md">
<div id="langToggleBtn" class="flex items-center gap-xs cursor-pointer text-on-surface-variant hover:text-primary transition-colors">
<span class="material-symbols-outlined">translate</span>
<span class="font-label-sm text-label-sm" id="langLabel">KO / EN</span>
</div>
</div>
</div>
</header>
<main class="pt-16">
{content_en}
{content_ko}
</main>
<footer class="bg-surface-container-lowest border-t border-outline-variant w-full py-xl px-lg mt-section-gap">
<div class="max-w-container-max mx-auto flex flex-col md:flex-row justify-between items-center gap-md">
<div class="flex flex-col gap-xs items-center md:items-start">
<span class="text-headline-md font-headline-md font-bold text-on-surface">MCP Curriculum</span>
<p class="font-label-sm text-label-sm text-on-surface-variant">&copy; 2024 Microsoft Corporation</p>
</div>
<div class="flex flex-wrap gap-lg justify-center">
<a href="index.html" class="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-all">Home</a>
<a href="https://github.com/microsoft/mcp-for-beginners" class="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-all" target="_blank">GitHub</a>
<a href="https://github.com/microsoft/mcp-for-beginners/blob/main/LICENSE" class="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-all" target="_blank">License</a>
</div>
</div>
</footer>
<script>
// Language toggle
(function() {{
  var btn = document.getElementById('langToggleBtn');
  var label = document.getElementById('langLabel');
  var en = document.getElementById('content-en');
  var ko = document.getElementById('content-ko');
  var lang = localStorage.getItem('mcp-lang') || 'ko';
  function setLang(l) {{
    document.querySelectorAll('.lang-content').forEach(function(e) {{ e.classList.remove('active'); }});
    if (l === 'en' && en) {{ en.classList.add('active'); label.textContent = 'EN / KO'; }}
    else {{ if (ko) ko.classList.add('active'); label.textContent = 'KO / EN'; }}
    localStorage.setItem('mcp-lang', l);
  }}
  if (btn) btn.addEventListener('click', function() {{ setLang(lang === 'ko' ? 'en' : 'ko'); }});
  setLang(lang);
}})();
// Header shadow
window.addEventListener('scroll', function() {{
  var h = document.querySelector('header');
  if (window.scrollY > 20) {{ h.classList.add('shadow-md'); h.classList.remove('shadow-sm'); }}
  else {{ h.classList.remove('shadow-md'); h.classList.add('shadow-sm'); }}
}});
</script>
</body>
</html>'''

MODS = [
    ('00','00-Introduction','Introduction','소개'),
    ('01','01-CoreConcepts','Core Concepts','핵심 개념'),
    ('02','02-Security','Security','보안'),
    ('03','03-GettingStarted','Getting Started','시작하기'),
    ('04','04-PracticalImplementation','Practical Implementation','실용적인 구현'),
    ('05','05-AdvancedTopics','Advanced Topics','고급 주제'),
    ('06','06-CommunityContributions','Community Contributions','커뮤니티 기여'),
    ('07','07-LessonsfromEarlyAdoption','Lessons from Early Adoption','초기 도입 교훈'),
    ('08','08-BestPractices','Best Practices','모범 사례'),
    ('09','09-CaseStudy','Case Study','사례 연구'),
    ('10','10-StreamliningAIWorkflowsBuildingAnMCPServerWithAIToolkit','AI Toolkit','AI 툴킷'),
    ('11','11-MCPServerHandsOnLabs','PostgreSQL','PostgreSQL'),
]

def module_section(num, title, html, folder):
    return f'''
<section class="py-section-gap px-md scroll-mt-24">
  <div class="max-w-container-max mx-auto">
    <div class="inline-flex items-center gap-xs px-sm py-base bg-surface-container-high text-primary rounded-full mb-lg border border-primary/20">
      <span class="material-symbols-outlined text-sm">code</span>
      <span class="font-label-sm text-label-sm uppercase tracking-wider">Module {num}</span>
    </div>
    <h2 class="font-headline-lg text-headline-lg text-on-surface mb-md">{title}</h2>
    <div class="bg-white rounded-2xl p-lg md:p-xl border border-outline-variant/30 shadow-sm">
      {html}
    </div>
  </div>
</section>'''

NAV_ITEMS = [
    ('Fundamentals', 'fundamentals.html'),
    ('Getting Started', 'getting-started.html'),
    ('Intermediate', 'intermediate.html'),
    ('Ecosystem', 'ecosystem.html'),
    ('Production', 'production.html'),
]

def build_nav(current):
    items = []
    for name, href in NAV_ITEMS:
        cls = 'text-primary border-b-2 border-primary pb-1' if href == current else 'text-on-surface-variant hover:text-primary transition-colors'
        items.append(f'<a class="font-body-md text-body-md {cls}" href="{href}">{name}</a>')
    return '\n          '.join(items)

def build_page(modules, fname, include_sg=False):
    en_secs = []; ko_secs = []
    for num, folder, title_en, title_ko in modules:
        print(f"  Module {num} ({folder})...")
        md_en = fetch_md(folder); md_ko = fetch_md(folder, True)
        if len(md_ko) < len(md_en) * 0.3:
            md_ko = md_en
        en_html = md_to_html(md_en, folder=folder, ko=False)
        ko_html = md_to_html(md_ko, folder=folder, ko=True)
        en_secs.append(module_section(num, title_en, en_html, folder))
        ko_secs.append(module_section(num, f'Module {num} &mdash; {title_ko}', ko_html, folder))
    if include_sg:
        print("  Study guide...")
        sg_en = fetch_sg(); sg_ko = fetch_sg(True)
        if len(sg_ko) < len(sg_en) * 0.3:
            sg_ko = sg_en
        en_secs.append(f'''
<section class="py-section-gap px-md scroll-mt-24 bg-surface-container-low">
  <div class="max-w-container-max mx-auto">
    <div class="inline-flex items-center gap-xs px-sm py-base bg-secondary/10 text-secondary rounded-full mb-lg border border-secondary/20">
      <span class="material-symbols-outlined text-sm">school</span>
      <span class="font-label-sm text-label-sm uppercase tracking-wider">Study Guide</span>
    </div>
    <h2 class="font-headline-lg text-headline-lg text-on-surface mb-md">Study Guide</h2>
    <div class="bg-white rounded-2xl p-lg md:p-xl border border-outline-variant/30 shadow-sm">
      {md_to_html(sg_en)}
    </div>
  </div>
</section>''')
        ko_secs.append(f'''
<section class="py-section-gap px-md scroll-mt-24 bg-surface-container-low">
  <div class="max-w-container-max mx-auto">
    <div class="inline-flex items-center gap-xs px-sm py-base bg-secondary/10 text-secondary rounded-full mb-lg border border-secondary/20">
      <span class="material-symbols-outlined text-sm">school</span>
      <span class="font-label-sm text-label-sm uppercase tracking-wider">스터디 가이드</span>
    </div>
    <h2 class="font-headline-lg text-headline-lg text-on-surface mb-md">스터디 가이드</h2>
    <div class="bg-white rounded-2xl p-lg md:p-xl border border-outline-variant/30 shadow-sm">
      {md_to_html(sg_ko)}
    </div>
  </div>
</section>''')
    title = fname.replace('.html','').capitalize()
    nav_html = build_nav(fname)
    content_en = '<div id="content-en" class="lang-content">\n' + '\n'.join(en_secs) + '\n</div>'
    content_ko = '<div id="content-ko" class="lang-content">\n' + '\n'.join(ko_secs) + '\n</div>'
    html = PAGE_TPL.replace('{title}', title).replace('{colors}', TAILWIND_CONFIG).replace('{nav}', nav_html).replace('{content_en}', content_en).replace('{content_ko}', content_ko)
    html = html.replace('href="index.html"', 'href="../index.html"')
    return html

def main():
    os.makedirs(os.path.join(BASE, 'pages'), exist_ok=True)
    pages = [
        ('fundamentals.html', MODS[0:3], False),
        ('getting-started.html', MODS[3:4], False),
        ('intermediate.html', MODS[4:6], False),
        ('ecosystem.html', MODS[6:8], False),
        ('production.html', MODS[8:12], True),
    ]
    for fname, mods, sg in pages:
        print(f"\n=== {fname} ===")
        html = build_page(mods, fname, sg)
        path = os.path.join(BASE, 'pages', fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  -> saved ({len(html)} bytes)")
    print("\nAll done!")

if __name__ == '__main__':
    main()
