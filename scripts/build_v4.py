#!/usr/bin/env python3
"""Build separate pages per lesson. Hub pages link to individual lesson pages."""
import urllib.request, os, re, html as html_mod

BASE = r'C:\Users\중진공39\mcp-site'
RAW = 'https://raw.githubusercontent.com/microsoft/mcp-for-beginners/main'
GITHUB = 'https://github.com/microsoft/mcp-for-beginners/tree/main'
CACHE = {}

def fetch(url):
    if url in CACHE: return CACHE[url]
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read().decode('utf-8')
            CACHE[url] = text; return text
    except: CACHE[url] = ''; return ''

def fetch_md(folder, ko=False):
    p = 'translations/ko/' if ko else ''
    return fetch(f'{RAW}/{p}{folder}/README.md')
def fetch_sg(ko=False):
    p = 'translations/ko/' if ko else ''
    return fetch(f'{RAW}/{p}study_guide.md')

def is_same_dir(url):
    return bool(re.match(r'^(\./)?[^./][^:]*$', url)) and not url.startswith('../') and not url.startswith('http')

def resolve_raw_url(url, folder, ko):
    p = 'translations/ko/' if ko else ''
    u = url[2:] if url.startswith('./') else url
    return f'{RAW}/{p}{folder}/{u}'

def normalize_gh(url, folder):
    if url.startswith('../'):
        n = 0; t = url
        while t.startswith('../'): n += 1; t = t[3:]
        parts = folder.split('/')
        parent = '/'.join(parts[:-n]) if n <= len(parts) else ''
        return f'{GITHUB}/{parent}/{t}' if parent else f'{GITHUB}/{t}'
    c = url[2:] if url.startswith('./') else url
    return f'{GITHUB}/{folder}/{c}'

def inline(t):
    t = re.sub(r'`([^`]+)`', r'<code class="px-1.5 py-0.5 rounded text-sm font-mono text-[var(--accent)] bg-[var(--border)]/30">\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<a class="text-[var(--accent)] underline" href="{m.group(2)}">{m.group(1)}</a>', t)
    return t

def md_to_html(md, folder=None, ko=False):
    lines = md.split('\n'); out = []; in_code = False; buf = []
    for line in lines:
        if line.startswith('```'):
            if in_code:
                out.append('<pre class="bg-code-bg text-white rounded-xl p-4 overflow-x-auto text-sm mb-4 leading-relaxed"><code>')
                for c in buf: out.append(html_mod.escape(c) + '\n')
                out.append('</code></pre>'); buf = []; in_code = False
            else: in_code = True
            continue
        if in_code: buf.append(line); continue
        if line.startswith('#### '): out.append(f'<h5 class="font-headline-sm text-headline-sm text-on-surface mt-6 mb-2">{inline(line[5:])}</h5>')
        elif line.startswith('### '): out.append(f'<h4 class="font-headline-md text-headline-md text-on-surface mt-8 mb-3">{inline(line[4:])}</h4>')
        elif line.startswith('## '): out.append(f'<h3 class="font-headline-lg text-headline-lg text-on-surface mt-10 mb-4">{inline(line[3:])}</h3>')
        elif line.startswith('# '): out.append(f'<h2 class="font-headline-xl text-headline-xl text-on-surface mt-12 mb-6">{inline(line[2:])}</h2>')
        elif line.startswith('- '): out.append(f'<li class="ml-5 list-disc text-on-surface-variant mb-2 leading-relaxed">{inline(line[2:])}</li>')
        elif line.strip() == '': out.append('')
        elif not line.startswith('!') and not line.startswith('['):
            t = inline(line)
            if len(t) > 250:
                for p in re.split(r'(?<=[.!?])\s+(?=[A-Z\uAC00-\uD7A3])', t):
                    p = p.strip()
                    if p: out.append(f'<p class="text-body-md text-on-surface-variant mb-3 leading-relaxed">{p}</p>')
            else: out.append(f'<p class="text-body-md text-on-surface-variant mb-3 leading-relaxed">{t}</p>')
    if in_code:
        out.append('<pre class="bg-code-bg text-white rounded-xl p-4 overflow-x-auto text-sm mb-4"><code>')
        for c in buf: out.append(html_mod.escape(c) + '\n')
        out.append('</code></pre>')
    result = '\n'.join(out)
    def fix_link(m):
        u = m.group(1)
        if u.startswith('http') or u.startswith('#') or u.startswith('mailto:'): return m.group(0)
        if folder: return f'<a class="text-[var(--accent)] underline" href="{normalize_gh(u, folder)}" target="_blank">{m.group(2)}</a>'
        return m.group(0)
    result = re.sub(r'<a\s+class="text-\[var\(--accent\)\] underline"\s+href="([^"]+)"[^>]*>(.*?)</a>', fix_link, result, flags=re.DOTALL)
    return result

def extract_lessons(md, folder, ko):
    seen = set(); lessons = []
    for line in md.split('\n'):
        for text, url in re.findall(r'\[([^\]]+)\]\(([^)]*README\.md)\)', line):
            if not is_same_dir(url) or url in seen: continue
            seen.add(url)
            clean_url = url[2:] if url.startswith('./') else url
            dir_part = os.path.dirname(clean_url)
            # Build title: use folder name if link text is generic
            generic = {'to the lesson', 'learn', 'start here', 'setup', 'build', 'advance', 'test', 'integrate', 'deploy', 'monitor', 'optimize', 'link', 'read more'}
            if text.lower().strip() in generic and dir_part:
                title = os.path.basename(dir_part).replace('-', ' ').title()
            elif text.lower().strip() in generic:
                title = os.path.basename(folder.rstrip('/')) + ' Lesson'
            else:
                title = text
            # Try to extract heading context
            hm = re.match(r'^#+\s+\d+\.?\s*(.+?)\s*\[', line)
            if hm: title = hm.group(1).strip()
            # For table rows, include preceding cell
            if '|' in line:
                cells = line.split('|')
                for i, c in enumerate(cells):
                    if url in c and i >= 2:
                        prev = re.sub(r'\[.*?\]\(.*?\)', '', cells[i-1]).strip()
                        if prev and prev not in title: title = f'{prev} - {title}'
                        break
            lang = ''
            for l in ['TypeScript','JavaScript','Python','C#','.NET','Java','Rust','Go']:
                if l in line: lang = l; break
            content = fetch(resolve_raw_url(url, folder, ko))
            if content:
                sub_f = folder + '/' + dir_part if dir_part else folder
                lessons.append({'title': title, 'url': url, 'folder': sub_f, 'lang': lang, 'content': content})
    return lessons

def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9\uAC00-\uD7A3\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s.strip().lower())[:50]
    return s or 'lesson'

# Template for hub page (module list with links to individual lessons)
HUB_TPL = """<!DOCTYPE html>
<html class="dark" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title} - MCP Academy</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
tailwind.config = {{ darkMode: "class", theme: {{ extend: {{ colors: {{ "surface-deep":"#050B14","surface":"#051426","surface-bright":"#2c3a4e","surface-container":"#122033","surface-container-high":"#1c2b3e","surface-container-highest":"#27354a","surface-container-lowest":"#010e21","neon-cyan":"#00F0FF","primary":"#dbfcff","secondary":"#a3c9ff","on-surface":"#d5e3fe","on-surface-variant":"#b9cacb","outline":"#849495","outline-variant":"#3b494b","terminal-green":"#00FF41","warning-gold":"#FFD700" }}, borderRadius: {{ DEFAULT:"0.125rem",lg:"0.25rem",xl:"0.5rem",full:"0.75rem" }}, spacing: {{ gutter:"24px",base:"8px","section-gap-desktop":"80px","container-max":"1280px","section-gap-mobile":"48px" }}, fontFamily: {{ "label-caps":["JetBrains Mono"],"body-md":["Inter"],"display-lg":["Hanken Grotesk"],"headline-md":["Hanken Grotesk"],"body-lg":["Inter"],"headline-lg":["Hanken Grotesk"],"code-sm":["JetBrains Mono"] }}, fontSize: {{ "label-caps":["12px",{{"lineHeight":"16px","letterSpacing":"0.1em","fontWeight":"700"}}],"body-md":["16px",{{"lineHeight":"24px","fontWeight":"400"}}],"display-lg":["48px",{{"lineHeight":"56px","letterSpacing":"-0.02em","fontWeight":"800"}}],"headline-md":["24px",{{"lineHeight":"32px","fontWeight":"600"}}],"body-lg":["18px",{{"lineHeight":"28px","fontWeight":"400"}}],"headline-lg":["32px",{{"lineHeight":"40px","fontWeight":"700"}}],"code-sm":["14px",{{"lineHeight":"20px","fontWeight":"400"}}] }} }} }} }};
</script>
<style>
:root {{ --bg:#051426;--text:#d5e3fe;--muted:#b9cacb;--accent:#00F0FF;--accent-hover:#00dbe9;--border:#3b494b;--card:#122033;--card-hover:#1c2b3e;--radius:12px;--code-bg:#0F172A; }}
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7; }}
.material-symbols-outlined {{ font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24; }}
.module-card {{ margin-bottom:16px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;background:var(--card);transition:box-shadow .2s,transform .15s,border-color .15s; }}
.module-card:hover {{ box-shadow:0 0 20px rgba(0,240,255,0.08);border-color:rgba(0,240,255,0.3); }}
.module-header {{ display:flex;justify-content:space-between;align-items:center;padding:16px 20px;cursor:pointer;user-select:none;transition:background .15s; }}
.module-header:hover {{ background:var(--card-hover); }}
.module-id {{ font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:var(--muted);min-width:36px; }}
.module-name {{ font-weight:600;flex:1;font-size:0.95rem; }}
.module-name .ko {{ color:var(--muted);font-weight:400;font-size:0.85rem;display:block;margin-top:2px; }}
.module-meta {{ font-size:0.78rem;color:var(--muted); }}
.module-lessons {{ display:none;padding:0 20px 16px; }}
.module-card.open .module-lessons {{ display:block; }}
.lesson-item {{ display:flex;align-items:center;padding:10px 12px;border-radius:8px;gap:10px;text-decoration:none;color:var(--text);transition:background .15s;margin-bottom:2px; }}
.lesson-item:hover {{ background:var(--card-hover); }}
.lesson-item .name {{ flex:1;font-size:0.88rem;font-weight:500; }}
.lesson-item .lang-badge {{ font-size:0.65rem;padding:2px 8px;border-radius:4px;font-weight:600;background:rgba(0,240,255,0.1);color:var(--accent);font-family:'JetBrains Mono',monospace;white-space:nowrap; }}
.lesson-item .meta {{ font-size:0.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace; }}
.lang-content {{ display:none; }}
.lang-content.active {{ display:block; }}
.search-wrap {{ position:relative;margin-bottom:20px; }}
.search-wrap input {{ width:100%;padding:10px 16px 10px 38px;border:1px solid var(--border);border-radius:8px;font-size:0.9rem;font-family:'Inter',sans-serif;background:var(--card);color:var(--text);outline:none;transition:border-color .15s,box-shadow .15s; }}
.search-wrap input:focus {{ border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,240,255,0.1); }}
.search-wrap .icon {{ position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:1.1rem;pointer-events:none; }}
.no-lessons {{ display:none;text-align:center;padding:40px 20px;color:var(--muted);font-size:0.9rem; }}
.hub-count {{ font-size:0.85rem;color:var(--muted); }}
nav a {{ font-size:1rem;font-weight:500;color:var(--muted);text-decoration:none;transition:color .15s; }}
nav a:hover,nav a.active {{ color:var(--accent); }}
</style>
</head>
<body class="bg-surface-deep text-on-surface font-body-md selection:bg-neon-cyan/30">
<header class="bg-surface/80 docked top-0 sticky z-50 backdrop-blur-xl border-b border-primary/10 shadow-[0_0_20px_rgba(0,240,255,0.1)] flex justify-between items-center px-gutter py-4 w-full">
<div class="flex items-center gap-4">
<a href="../index.html" class="no-underline">
<span class="font-display-lg text-display-lg text-neon-cyan tracking-tighter">MCP Academy</span>
</a>
</div>
<nav class="hidden md:flex gap-8 items-center">{nav}</nav>
<div class="flex items-center gap-4">
<div id="langToggle" class="flex items-center gap-1 cursor-pointer text-on-surface-variant hover:text-neon-cyan transition-colors">
<span class="material-symbols-outlined">translate</span>
<span class="font-label-caps text-label-caps" id="langLabel">KO / EN</span>
</div>
</div>
</header>
<main>
<section class="relative overflow-hidden border-b border-primary/10 px-gutter py-section-gap-desktop">
<div class="max-w-5xl mx-auto">
<div class="inline-flex items-center gap-2 px-3 py-1 bg-neon-cyan/10 border border-neon-cyan/30 rounded-full mb-6">
<span class="material-symbols-outlined text-neon-cyan text-sm">auto_awesome</span>
<span class="font-label-caps text-label-caps text-neon-cyan">MCP CURRICULUM</span>
</div>
<h1 class="font-display-lg text-display-lg text-white mb-4">{title}</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">MCP 학습 과정을 모듈별로 탐색하세요. 레슨을 클릭하면 상세 내용과 코드 예제를 확인할 수 있습니다.</p>
<div id="totalCount" class="hub-count mt-4 font-label-caps text-label-caps"></div>
</div>
</section>
<div class="max-w-5xl mx-auto px-gutter py-section-gap-mobile">
<div class="search-wrap">
<span class="icon material-symbols-outlined">search</span>
<input type="text" id="lessonSearch" placeholder="Search lessons..." oninput="filterLessons(this.value)">
</div>
<div class="no-lessons" id="noLessons">No lessons found matching your search.</div>
<div id="content-en" class="lang-content">{en_content}</div>
<div id="content-ko" class="lang-content">{ko_content}</div>
</div>
</main>
<footer class="bg-surface-deep border-t border-outline-variant w-full p-gutter">
<div class="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 items-center gap-base">
<div>
<span class="font-headline-md text-headline-md text-neon-cyan block mb-2">MCP Academy</span>
<p class="font-body-md text-body-md text-outline">MCP Curriculum &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank" class="text-neon-cyan hover:underline">microsoft/mcp-for-beginners</a></p>
</div>
<div class="flex flex-wrap md:justify-end gap-6">
<a href="../index.html" class="text-outline hover:text-neon-cyan transition-colors font-body-md text-body-md">Home</a>
<a href="https://github.com/microsoft/mcp-for-beginners" target="_blank" class="text-outline hover:text-neon-cyan transition-colors font-body-md text-body-md">GitHub</a>
<a href="https://github.com/microsoft/mcp-for-beginners/blob/main/LICENSE" target="_blank" class="text-outline hover:text-neon-cyan transition-colors font-body-md text-body-md">License</a>
</div>
</div>
</footer>
<script>
(function(){{var b=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko'),n=localStorage.getItem('mcp-lang')||'ko';function s(t){{document.querySelectorAll('.lang-content').forEach(function(x){{x.classList.remove('active')}});if(t==='en'&&e){{e.classList.add('active');l.textContent='EN / KO'}}else{{k&&k.classList.add('active');l.textContent='KO / EN'}}localStorage.setItem('mcp-lang',t)}}if(b)b.addEventListener('click',function(){{s(n==='ko'?'en':'ko')}});s(n);document.querySelectorAll('.module-header').forEach(function(h){{h.addEventListener('click',function(){{this.parentElement.classList.toggle('open')}})}});var tc=document.getElementById('totalCount'),total=document.querySelectorAll('.lesson-item').length;if(tc)tc.textContent='TOTAL: '+total+' LESSONS';}})();
function filterLessons(query){{var q=query.toLowerCase().trim(),cards=document.querySelectorAll('.module-card'),any=false;cards.forEach(function(c){{var items=c.querySelectorAll('.lesson-item'),has=false;items.forEach(function(it){{var match=!q||it.querySelector('.name').textContent.toLowerCase().indexOf(q)>-1;it.style.display=match?'flex':'none';if(match)has=true;}});c.style.display=has||!q?'block':'none';if(has||!q)c.classList.add('open');if(c.style.display!=='none')any=true;}});document.getElementById('noLessons').style.display=any?'none':'block';}}
</script>
</body>
</html>"""

# Template for individual lesson page
LESSON_TPL = """<!DOCTYPE html>
<html class="dark" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{lesson_title} - {module_title} - MCP Academy</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
tailwind.config = {{ darkMode: "class", theme: {{ extend: {{ colors: {{ "surface-deep":"#050B14","surface":"#051426","surface-bright":"#2c3a4e","surface-container":"#122033","surface-container-high":"#1c2b3e","surface-container-highest":"#27354a","surface-container-lowest":"#010e21","neon-cyan":"#00F0FF","primary":"#dbfcff","secondary":"#a3c9ff","on-surface":"#d5e3fe","on-surface-variant":"#b9cacb","outline":"#849495","outline-variant":"#3b494b","terminal-green":"#00FF41","warning-gold":"#FFD700" }}, borderRadius: {{ DEFAULT:"0.125rem",lg:"0.25rem",xl:"0.5rem",full:"0.75rem" }}, spacing: {{ gutter:"24px",base:"8px","section-gap-desktop":"80px","container-max":"1280px","section-gap-mobile":"48px" }}, fontFamily: {{ "label-caps":["JetBrains Mono"],"body-md":["Inter"],"display-lg":["Hanken Grotesk"],"headline-md":["Hanken Grotesk"],"body-lg":["Inter"],"headline-lg":["Hanken Grotesk"],"code-sm":["JetBrains Mono"] }}, fontSize: {{ "label-caps":["12px",{{"lineHeight":"16px","letterSpacing":"0.1em","fontWeight":"700"}}],"body-md":["16px",{{"lineHeight":"24px","fontWeight":"400"}}],"display-lg":["48px",{{"lineHeight":"56px","letterSpacing":"-0.02em","fontWeight":"800"}}],"headline-md":["24px",{{"lineHeight":"32px","fontWeight":"600"}}],"body-lg":["18px",{{"lineHeight":"28px","fontWeight":"400"}}],"headline-lg":["32px",{{"lineHeight":"40px","fontWeight":"700"}}],"code-sm":["14px",{{"lineHeight":"20px","fontWeight":"400"}}] }} }} }} }};
</script>
<style>
:root {{ --bg:#051426;--text:#d5e3fe;--muted:#b9cacb;--accent:#00F0FF;--accent-hover:#00dbe9;--border:#3b494b;--card:#122033;--card-hover:#1c2b3e;--radius:12px;--code-bg:#0F172A; }}
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7; }}
.material-symbols-outlined {{ font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24; }}
.lang-content {{ display:none; }}
.lang-content.active {{ display:block; }}
.progress-bar {{ height:3px;background:var(--border);border-radius:2px;overflow:hidden;margin-bottom:24px; }}
.progress-fill {{ height:100%;background:var(--accent);border-radius:2px;transition:width .3s; }}
.nav-card {{ display:flex;align-items:center;gap:12px;padding:14px 18px;border:1px solid var(--border);border-radius:var(--radius);text-decoration:none;color:var(--text);transition:all .15s;flex:1;background:var(--card); }}
.nav-card:hover {{ background:var(--card-hover);border-color:var(--accent);box-shadow:0 0 12px rgba(0,240,255,0.1); }}
.nav-card.prev {{ text-align:left; }}
.nav-card.next {{ text-align:right;flex-direction:row-reverse; }}
.nav-card .label {{ font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;font-family:'JetBrains Mono',monospace; }}
.nav-card .lname {{ font-size:0.85rem;font-weight:500; }}
</style>
</head>
<body class="bg-surface-deep text-on-surface font-body-md selection:bg-neon-cyan/30">
<header class="bg-surface/80 docked top-0 sticky z-50 backdrop-blur-xl border-b border-primary/10 shadow-[0_0_20px_rgba(0,240,255,0.1)] flex justify-between items-center px-gutter py-4 w-full" style="height:64px;">
<div class="flex items-center gap-4">
<a href="{hub_back}" class="flex items-center gap-2 text-neon-cyan no-underline hover:underline">
<span class="material-symbols-outlined">arrow_back</span>
<span class="hidden sm:inline font-headline-md text-headline-md">{hub_title}</span>
<span class="sm:hidden font-headline-md text-headline-md">Back</span>
</a>
</div>
<div class="flex items-center gap-4">
<span class="font-label-caps text-label-caps text-neon-cyan hidden sm:inline">{module_badge_inline}</span>
<div id="langToggle" class="flex items-center gap-1 cursor-pointer text-on-surface-variant hover:text-neon-cyan transition-colors">
<span class="material-symbols-outlined">translate</span>
<span class="font-label-caps text-label-caps hidden sm:inline" id="langLabel">KO / EN</span>
</div>
</div>
</header>
<main>
<div class="max-w-4xl mx-auto px-gutter py-section-gap-mobile">
<div class="progress-bar"><div class="progress-fill" style="width:{progress_pct}%"></div></div>
<div class="flex items-center gap-2 text-sm text-[var(--muted)] mb-6 font-label-caps text-label-caps">
<a href="{hub_back}" class="text-neon-cyan no-underline hover:underline">{hub_title}</a>
<span class="text-outline mx-1">&rsaquo;</span>
<span class="text-neon-cyan">{module_badge_text}</span>
<span class="text-outline mx-1">&rsaquo;</span>
<span class="text-on-surface">{lesson_title}</span>
</div>
<div id="content-en" class="lang-content">{en_content}</div>
<div id="content-ko" class="lang-content">{ko_content}</div>
<div class="flex gap-4 mt-10 pt-6 border-t border-[var(--border)]">
{prev_link}
{next_link}
</div>
</div>
</main>
<footer class="bg-surface-deep border-t border-outline-variant w-full p-gutter">
<div class="max-w-4xl mx-auto text-center">
<span class="font-headline-md text-headline-md text-neon-cyan block mb-2">MCP Academy</span>
<p class="font-body-md text-body-md text-outline">MCP Curriculum &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank" class="text-neon-cyan hover:underline">microsoft/mcp-for-beginners</a></p>
</div>
</footer>
<script>
(function(){{var b=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko'),n=localStorage.getItem('mcp-lang')||'ko';function s(t){{document.querySelectorAll('.lang-content').forEach(function(x){{x.classList.remove('active')}});if(t==='en'&&e){{e.classList.add('active');l.textContent='EN / KO'}}else{{k&&k.classList.add('active');l.textContent='KO / EN'}}localStorage.setItem('mcp-lang',t)}}if(b)b.addEventListener('click',function(){{s(n==='ko'?'en':'ko')}});s(n);}})();
</script>
</body>
</html>"""

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

NAV = [('Fundamentals','fundamentals.html'),('Getting Started','getting-started.html'),('Intermediate','intermediate.html'),('Ecosystem','ecosystem.html'),('Production','production.html')]

def build_nav(cur):
    items = []
    for name, href in NAV:
        cls = 'active' if href == cur else ''
        items.append(f'<a class="{cls}" href="{href}">{name}</a>')
    return '\n          '.join(items)

def main():
    os.makedirs(os.path.join(BASE, 'lessons'), exist_ok=True)

    for hub_name, modules, _ in [('fundamentals.html', MODS[0:3], False),
                                  ('getting-started.html', MODS[3:4], False),
                                  ('intermediate.html', MODS[4:6], False),
                                  ('ecosystem.html', MODS[6:8], False),
                                  ('production.html', MODS[8:12], True)]:
        print(f'\n=== Processing {hub_name} ===')
        sg_en = sg_ko = ''
        if hub_name == 'production.html':
            sg_en = fetch_sg(); sg_ko = fetch_sg(True)
            if len(sg_ko) < len(sg_en) * 0.3: sg_ko = sg_en

        hub_title = hub_name.replace('.html','').title()
        nav = build_nav(hub_name)
        hub_modules = []  # (num, folder, title_en, title_ko, lesson_pages, main_en, main_ko)

        for num, folder, title_en, title_ko in modules:
            print(f'  Module {num} ({folder})...')
            md_en = fetch_md(folder); md_ko = fetch_md(folder, True)
            if len(md_ko) < len(md_en) * 0.3: md_ko = md_en
            subs_en = extract_lessons(md_en, folder, False)
            subs_ko = extract_lessons(md_ko, folder, True)
            main_en = md_to_html(md_en, folder, False)
            for phrase in ['_(Click the image above to view video of this lesson)_', '_(Click the image above to view the video for this lesson)_']:
                main_en = main_en.replace(phrase, '')
            main_ko = md_to_html(md_ko, folder, True)
            for phrase in ['_(동영상을 보려면 이미지를 클릭하세요)_', '_(클릭하여 동영상 보기)_']:
                main_ko = main_ko.replace(phrase, '')

            lesson_pages = []
            for idx, s in enumerate(subs_en):
                safe_title = re.sub(r'[^a-zA-Z0-9\uAC00-\uD7A3\s-]', '', s['title']).strip().lower().replace(' ', '-')[:40] or 'lesson'
                fname = f'm{num}_{idx+1:02d}-{safe_title}.html'
                fpath = f'lessons/{fname}'
                e_html = md_to_html(s['content'], s['folder'], False)
                for phrase in ['_(Click the image above to view video of this lesson)_', '_(Click the image above to view the video for this lesson)_']:
                    e_html = e_html.replace(phrase, '')
                if md_ko == md_en:
                    k_html = e_html
                else:
                    kl = subs_ko[idx] if idx < len(subs_ko) else None
                    k_html = md_to_html(kl['content'], kl['folder'], True) if kl else e_html
                    for phrase in ['_(동영상을 보려면 이미지를 클릭하세요)_', '_(클릭하여 동영상 보기)_']:
                        k_html = k_html.replace(phrase, '')
                lang = s.get('lang', '')
                lesson_pages.append((fname, s['title'], e_html, k_html, lang))

            for idx, (fname, lt, e_html, k_html, _) in enumerate(lesson_pages):
                total = len(lesson_pages)
                prev_l = lesson_pages[idx-1] if idx > 0 else None
                next_l = lesson_pages[idx+1] if idx < total-1 else None
                pct = int((idx + 1) / total * 100)
                prev_link = f'<a href="{prev_l[0]}" class="nav-card prev"><span class="material-symbols-outlined text-[var(--accent)]">chevron_left</span><div><div class="label">Previous</div><div class="lname">{prev_l[1]}</div></div></a>' if prev_l else '<div></div>'
                next_link = f'<a href="{next_l[0]}" class="nav-card next"><span class="material-symbols-outlined text-[var(--accent)]">chevron_right</span><div><div class="label">Next</div><div class="lname">{next_l[1]}</div></div></a>' if next_l else '<div></div>'
                badge = f'<span>Module {num}: {title_en}</span>'
                badge_text = f'Module {num}: {title_en}'
                badge_inline = f'Module {num}: {title_en}'
                page = LESSON_TPL.replace('{lesson_title}', lt)
                for k, v in [('{module_title}', title_en), ('{hub_back}', f'../{hub_name}'), ('{hub_title}', hub_title), ('{module_badge}', badge), ('{module_badge_inline}', badge_inline), ('{module_badge_text}', badge_text), ('{progress_pct}', str(pct)), ('{prev_link}', prev_link), ('{next_link}', next_link), ('{en_content}', e_html), ('{ko_content}', k_html)]:
                    page = page.replace(k, v)
                page = page.replace('href="index.html"', 'href="../index.html"')
                lesson_path = os.path.join(BASE, 'lessons', fname)
                with open(lesson_path, 'w', encoding='utf-8') as f:
                    f.write(page)
                print(f'    -> lessons/{fname}')

            hub_modules.append((num, title_en, title_ko, lesson_pages, main_en, main_ko))

        # Build hub pages (EN and KO)
        def build_hub_content(lang):
            entries = []
            for num, title_en, title_ko, lps, main_en_html, main_ko_html in hub_modules:
                if lps:
                    lt = title_en if lang == 'en' else title_ko
                    lessons_html = ''
                    for item in lps:
                        fname, ltitle, _, _, llang = item if len(item) >= 5 else (item[0], item[1], None, None, '')
                        lname = ltitle if lang == 'en' else ltitle
                        badge = f'<span class="lang-badge">{llang}</span>' if llang else ''
                        lessons_html += f'<a class="lesson-item" href="../lessons/{fname}">{badge}<span class="name">{lname}</span><span class="meta">M{num}</span></a>\n'
                    entries.append(f'''<div class="module-card"><div class="module-header">
  <span class="module-id">M{num}</span>
  <span class="module-name">{title_en if lang=="en" else title_ko}<span class="ko">{title_ko if lang=="en" else title_en}</span></span>
  <span class="module-meta">{len(lps)} lessons</span>
</div><div class="module-lessons">{lessons_html}</div></div>''')
                else:
                    html = main_en_html if lang == 'en' else main_ko_html
                    entries.append(f'''<div class="module-card"><div class="module-header">
  <span class="module-id">M{num}</span>
  <span class="module-name">{title_en if lang=="en" else title_ko}<span class="ko">{title_ko if lang=="en" else title_en}</span></span>
  <span class="module-meta">overview</span>
</div><div class="module-lessons">{html}</div></div>''')
            return '\n'.join(entries)

        en_content = build_hub_content('en')
        ko_content = build_hub_content('ko')

        if hub_name == 'production.html' and sg_en:
            sg_html = md_to_html(sg_en)
            sg_ko_html = md_to_html(sg_ko)
            en_content += f'''<div class="module-card"><div class="module-header">
  <span class="module-id">SG</span><span class="module-name">Study Guide</span><span class="module-meta">1 guide</span>
</div><div class="module-lessons"><div class="bg-surface-container-low rounded-xl p-4 mb-3 text-sm text-on-surface-variant">{sg_html}</div></div></div>'''
            ko_content += f'''<div class="module-card"><div class="module-header">
  <span class="module-id">SG</span><span class="module-name">스터디 가이드</span><span class="module-meta">1 guide</span>
</div><div class="module-lessons"><div class="bg-surface-container-low rounded-xl p-4 mb-3 text-sm text-on-surface-variant">{sg_ko_html}</div></div></div>'''

        page = HUB_TPL.replace('{title}', hub_title).replace('{nav}', nav)
        page = page.replace('{en_content}', en_content).replace('{ko_content}', ko_content)
        page = page.replace('href="index.html"', 'href="../index.html"')
        with open(os.path.join(BASE, 'pages', hub_name), 'w', encoding='utf-8') as f:
            f.write(page)
        print(f'  -> pages/{hub_name} saved ({len(page)} bytes)')

    print('\nAll done!')

if __name__ == '__main__':
    main()
