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
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title} - MCP Academy</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{{--bg:#0a0f1a;--surface:#111827;--card:#1a2235;--hover:#222d42;--border:#2a3548;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--green:#4ade80;--radius:12px}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}}
header{{position:sticky;top:0;z-index:50;background:rgba(10,15,26,0.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between}}
.logo{{font-size:22px;font-weight:800;color:var(--accent);text-decoration:none}}
nav a{{color:var(--muted);text-decoration:none;font-size:14px;font-weight:500;margin-left:28px;transition:color .15s}}
nav a:hover,nav a.active{{color:var(--accent)}}
main{{max-width:960px;margin:0 auto;padding:48px 24px 80px}}
.hero{{margin-bottom:48px}}
.badge{{display:inline-block;background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.25);color:var(--accent);font-size:12px;font-weight:600;padding:5px 14px;border-radius:20px;letter-spacing:0.06em;margin-bottom:20px}}
h1{{font-size:36px;font-weight:800;color:#fff;margin-bottom:8px}}
.hero p{{color:var(--muted);font-size:16px;max-width:560px}}
.search{{position:relative;margin-bottom:32px}}
.search input{{width:100%;padding:12px 16px 12px 40px;background:var(--surface);border:1px solid var(--border);border-radius:10px;color:var(--text);font-size:15px;outline:none;transition:border-color .15s}}
.search input:focus{{border-color:var(--accent)}}
.search svg{{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--muted)}}
.module{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:20px;overflow:hidden}}
.module-top{{display:flex;align-items:center;justify-content:space-between;padding:18px 24px;cursor:pointer;user-select:none;transition:background .15s}}
.module-top:hover{{background:var(--hover)}}
.module-top h2{{font-size:20px;font-weight:700;color:#fff}}
.module-top .sub{{color:var(--muted);font-size:13px;margin-left:8px;font-weight:400}}
.module-top .count{{font-size:12px;color:var(--muted);background:var(--hover);padding:4px 12px;border-radius:12px;font-weight:600}}
.module-rows{{display:none;border-top:1px solid var(--border)}}
.module.open .module-rows{{display:block}}
.row{{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;text-decoration:none;color:var(--text);border-bottom:1px solid rgba(42,53,72,0.5);transition:background .15s;gap:16px}}
.row:hover{{background:var(--hover)}}
.row:last-child{{border-bottom:none}}
.row h3{{font-size:15px;font-weight:600;color:#fff;flex:1;min-width:0}}
.row .tags{{display:flex;align-items:center;gap:10px;flex-shrink:0}}
.tag{{font-size:11px;font-weight:700;padding:3px 10px;border-radius:5px;text-transform:uppercase;letter-spacing:0.04em}}
.tag.build{{background:rgba(56,189,248,0.12);color:var(--accent)}}
.tag.learn{{background:rgba(74,222,128,0.12);color:var(--green)}}
.tag.lang{{color:var(--muted);font-size:12px;font-family:'JetBrains Mono',monospace}}
.overview-body{{padding:24px;border-top:1px solid var(--border);display:none}}
.module.open .overview-body{{display:block}}
.overview-body h2,.overview-body h3,.overview-body h4,.overview-body h5{{color:#fff;margin:24px 0 10px;font-weight:700}}
.overview-body h2{{font-size:24px}}
.overview-body h3{{font-size:20px}}
.overview-body h4{{font-size:17px}}
.overview-body h5{{font-size:15px}}
.overview-body p{{color:var(--muted);margin-bottom:14px;font-size:15px}}
.overview-body ul,.overview-body ol{{color:var(--muted);padding-left:20px;margin-bottom:14px;font-size:15px}}
.overview-body li{{margin-bottom:6px}}
.overview-body a{{color:var(--accent)}}
.overview-body code{{background:var(--hover);color:var(--accent);padding:2px 6px;border-radius:4px;font-size:13px;font-family:'JetBrains Mono',monospace}}
.overview-body pre{{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;overflow-x:auto;margin-bottom:16px}}
.overview-body pre code{{background:none;color:var(--text);padding:0;font-size:13px;line-height:1.6;display:block}}
.overview-body table{{width:100%;border-collapse:collapse;margin-bottom:16px}}
.overview-body th,.overview-body td{{border:1px solid var(--border);padding:8px 12px;text-align:left;font-size:14px}}
.overview-body th{{background:var(--hover);color:#fff;font-weight:600}}
.overview-body td{{color:var(--muted)}}
.overview-body strong{{color:#fff}}
.overview-body hr{{border:none;border-top:1px solid var(--border);margin:24px 0}}
.chevron{{font-size:20px;color:var(--accent);transition:transform .2s;flex-shrink:0;margin-left:12px}}
.module.open .chevron{{transform:rotate(180deg)}}
.lang-content{{display:none}}
.lang-content.active{{display:block}}
.no-results{{display:none;text-align:center;padding:40px;color:var(--muted);font-size:15px}}
#totalCount{{font-size:13px;color:var(--muted);margin-top:12px;font-weight:500}}
.toggle-btn{{display:flex;align-items:center;gap:6px;cursor:pointer;color:var(--muted);font-size:13px;font-weight:600;background:none;border:1px solid var(--border);padding:6px 14px;border-radius:8px;transition:all .15s}}
.toggle-btn:hover{{color:var(--accent);border-color:var(--accent)}}
.mobile-btn{{display:none;background:none;border:none;color:var(--text);font-size:20px;cursor:pointer}}
footer{{border-top:1px solid var(--border);padding:32px 24px;text-align:center;color:var(--muted);font-size:14px}}
footer a{{color:var(--accent);text-decoration:none}}
@media(max-width:768px){{
.mobile-btn{{display:block}}
nav{{display:none;position:fixed;top:56px;left:0;right:0;background:var(--surface);flex-direction:column;padding:16px;border-bottom:1px solid var(--border);gap:8px;z-index:40}}
nav.open{{display:flex}}
nav a{{margin:0;padding:12px 16px;border-radius:8px;font-size:15px}}
nav a:hover{{background:var(--hover)}}
h1{{font-size:28px}}
}}
</style>
</head>
<body>
<header>
<a href="../index.html" class="logo">MCP Academy</a>
<button class="mobile-btn" onclick="document.querySelector('nav').classList.toggle('open')">&#9776;</button>
<nav>{nav}</nav>
<div style="display:flex;align-items:center;gap:20px">
<button class="toggle-btn" id="langToggle">
<span id="langLabel">KO &#8644; EN</span>
</button>
</div>
</header>
<main>
<div class="hero">
<div class="badge">MCP CURRICULUM</div>
<h1>{title}</h1>
<p>Explore modules and lessons. Click for details and code examples.</p>
<div id="totalCount"></div>
</div>
<div class="search">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
<input type="text" id="lessonSearch" placeholder="Search lessons..." oninput="filter(this.value)">
</div>
<div class="no-results" id="noResults">No results found.</div>
<div id="content-en" class="lang-content">{en_content}</div>
<div id="content-ko" class="lang-content">{ko_content}</div>
</main>
<footer>
MCP Curriculum &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">microsoft/mcp-for-beginners</a>
</footer>
<script>
(function(){{
var t=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko'),n=localStorage.getItem('mcp-lang')||'ko';
function s(v){{document.querySelectorAll('.lang-content').forEach(function(x){{x.classList.remove('active')}});if(v==='en'){{e.classList.add('active');l.textContent='EN \\21C4 KO'}}else{{k.classList.add('active');l.textContent='KO \\21C4 EN'}}localStorage.setItem('mcp-lang',v)}}
t.addEventListener('click',function(){{s(n==='ko'?'en':'ko')}});s(n);
document.querySelectorAll('.module-top').forEach(function(m){{m.addEventListener('click',function(){{this.parentElement.classList.toggle('open')}})}});
var tc=document.getElementById('totalCount'),total=document.querySelectorAll('.row').length;if(tc)tc.textContent='TOTAL: '+total+' LESSONS';
}})();
function filter(q){{
var v=q.toLowerCase().trim(),cards=document.querySelectorAll('.module'),any=false;
cards.forEach(function(c){{
var rows=c.querySelectorAll('.row'),has=false;
rows.forEach(function(r){{var match=!v||r.querySelector('h3').textContent.toLowerCase().indexOf(v)>-1;r.style.display=match?'flex':'none';if(match)has=true;}});
c.style.display=has||!v?'':'none';if(has||!v)c.classList.add('open');
if(c.style.display!=='none')any=true;
}});
document.getElementById('noResults').style.display=any?'none':'block';
}}
</script>
</body>
</html>"""

# Template for individual lesson page
LESSON_TPL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{lesson_title} - {module_title} - MCP Academy</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{{--bg:#0a0f1a;--surface:#111827;--card:#1a2235;--hover:#222d42;--border:#2a3548;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--green:#4ade80;--radius:12px}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7;-webkit-font-smoothing:antialiased}}
header{{position:sticky;top:0;z-index:50;background:rgba(10,15,26,0.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between}}
header a{{color:var(--accent);text-decoration:none;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}}
.badge{{font-size:12px;color:var(--muted);font-weight:500}}
.toggle-btn{{display:flex;align-items:center;gap:6px;cursor:pointer;color:var(--muted);font-size:13px;font-weight:600;background:none;border:1px solid var(--border);padding:6px 14px;border-radius:8px;transition:all .15s}}
.toggle-btn:hover{{color:var(--accent);border-color:var(--accent)}}
main{{max-width:800px;margin:0 auto;padding:32px 24px 80px}}
.breadcrumb{{font-size:13px;color:var(--muted);margin-bottom:8px}}
.breadcrumb a{{color:var(--accent);text-decoration:none}}
.progress{{height:3px;background:var(--border);border-radius:2px;margin-bottom:28px;overflow:hidden}}
.progress-fill{{height:100%;background:var(--accent);border-radius:2px;transition:width .3s}}
.lang-content{{display:none}}
.lang-content.active{{display:block}}
.overview-body h2,.overview-body h3,.overview-body h4,.overview-body h5{{color:#fff;margin:28px 0 12px;font-weight:700}}
.overview-body h2{{font-size:28px}}
.overview-body h3{{font-size:22px}}
.overview-body h4{{font-size:18px}}
.overview-body h5{{font-size:16px}}
.overview-body p{{color:var(--muted);margin-bottom:16px;font-size:15px}}
.overview-body ul,.overview-body ol{{color:var(--muted);padding-left:22px;margin-bottom:16px;font-size:15px}}
.overview-body li{{margin-bottom:6px}}
.overview-body a{{color:var(--accent)}}
.overview-body code{{background:var(--hover);color:var(--accent);padding:2px 6px;border-radius:4px;font-size:13px;font-family:'JetBrains Mono',monospace}}
.overview-body pre{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px;overflow-x:auto;margin-bottom:18px;position:relative}}
.overview-body pre code{{background:none;color:var(--text);padding:0;font-size:13px;line-height:1.6;display:block}}
.overview-body table{{width:100%;border-collapse:collapse;margin-bottom:18px}}
.overview-body th,.overview-body td{{border:1px solid var(--border);padding:8px 12px;text-align:left;font-size:14px}}
.overview-body th{{background:var(--hover);color:#fff;font-weight:600}}
.overview-body td{{color:var(--muted)}}
.overview-body strong{{color:#fff}}
.overview-body hr{{border:none;border-top:1px solid var(--border);margin:28px 0}}
.nav-row{{display:flex;gap:16px;margin-top:48px;padding-top:24px;border-top:1px solid var(--border)}}
.nav-link{{flex:1;display:flex;align-items:center;gap:12px;padding:16px 20px;background:var(--card);border:1px solid var(--border);border-radius:10px;text-decoration:none;color:var(--text);transition:all .15s}}
.nav-link:hover{{background:var(--hover);border-color:var(--accent)}}
.nav-link.next{{flex-direction:row-reverse;text-align:right}}
.nav-link .dir{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;font-family:'JetBrains Mono',monospace}}
.nav-link .title{{font-size:14px;font-weight:600;color:#fff}}
footer{{border-top:1px solid var(--border);padding:32px 24px;text-align:center;color:var(--muted);font-size:14px}}
footer a{{color:var(--accent);text-decoration:none}}
</style>
</head>
<body>
<header>
<a href="{hub_back}">&larr; {hub_title}</a>
<div style="display:flex;align-items:center;gap:16px">
<span class="badge">{module_badge_text}</span>
<button class="toggle-btn" id="langToggle"><span id="langLabel">KO &#8644; EN</span></button>
</div>
</header>
<main>
<div class="progress"><div class="progress-fill" style="width:{progress_pct}%"></div></div>
<div class="breadcrumb"><a href="{hub_back}">{hub_title}</a> &rsaquo; {module_badge_text} &rsaquo; {lesson_title}</div>
<div id="content-en" class="lang-content overview-body">{en_content}</div>
<div id="content-ko" class="lang-content overview-body">{ko_content}</div>
<div class="nav-row">{prev_link}{next_link}</div>
</main>
<footer>MCP Curriculum &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">microsoft/mcp-for-beginners</a></footer>
<script>
(function(){{
var t=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko'),n=localStorage.getItem('mcp-lang')||'ko';
function s(v){{document.querySelectorAll('.lang-content').forEach(function(x){{x.classList.remove('active')}});if(v==='en'){{e.classList.add('active');l.textContent='EN \\21C4 KO'}}else{{k.classList.add('active');l.textContent='KO \\21C4 EN'}}localStorage.setItem('mcp-lang',v)}}
t.addEventListener('click',function(){{s(n==='ko'?'en':'ko')}});s(n);
}})();
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

            # If no lessons extracted, create one lesson from the full module content
            if not subs_en:
                safe_title = slugify(title_en)
                fname = f'm{num}_01-{safe_title}.html'
                lesson_pages.append((fname, title_en, main_en, main_ko, ''))

            for idx, (fname, lt, e_html, k_html, _) in enumerate(lesson_pages):
                total = len(lesson_pages)
                prev_l = lesson_pages[idx-1] if idx > 0 else None
                next_l = lesson_pages[idx+1] if idx < total-1 else None
                pct = int((idx + 1) / total * 100)
                prev_link = f'<a href="{prev_l[0]}" class="nav-link prev"><span class="dir">Previous</span><span class="title">{prev_l[1]}</span></a>' if prev_l else '<div></div>'
                next_link = f'<a href="{next_l[0]}" class="nav-link next"><span class="dir">Next</span><span class="title">{next_l[1]}</span></a>' if next_l else '<div></div>'
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
                    rows = ''
                    for item in lps:
                        fname, ltitle, _, _, llang = item if len(item) >= 5 else (item[0], item[1], None, None, '')
                        lname = ltitle if lang == 'en' else ltitle
                        cls = 'build' if llang else 'learn'
                        label = 'BUILD' if llang else 'LEARN'
                        lang_tag = f'<span class="tag lang">{llang}</span>' if llang else ''
                        rows += f'''<a href="../lessons/{fname}" class="row">
  <h3>{lname}</h3>
  <div class="tags"><span class="tag {cls}">{label}</span>{lang_tag}</div>
</a>
'''
                    entries.append(f'''<div class="module">
<div class="module-top" onclick="this.parentElement.classList.toggle('open')">
  <div><h2>M{num}: {title_en if lang=="en" else title_ko} <span class="sub">{title_ko if lang=="en" else title_en}</span></h2></div>
  <div style="display:flex;align-items:center;gap:12px"><span class="count">{len(lps)} lessons</span><span class="chevron">&#8250;</span></div>
</div>
<div class="module-rows">{rows}</div>
</div>''')
                else:
                    html = main_en_html if lang == 'en' else main_ko_html
                    entries.append(f'''<div class="module">
<div class="module-top" onclick="this.parentElement.classList.toggle('open')">
  <div><h2>M{num}: {title_en if lang=="en" else title_ko} <span class="sub">{title_ko if lang=="en" else title_en}</span></h2></div>
  <div style="display:flex;align-items:center;gap:12px"><span class="count">overview</span><span class="chevron">&#8250;</span></div>
</div>
<div class="overview-body">{html}</div>
</div>''')
            return '\n'.join(entries)

        en_content = build_hub_content('en')
        ko_content = build_hub_content('ko')

        if hub_name == 'production.html' and sg_en:
            sg_html = md_to_html(sg_en)
            sg_ko_html = md_to_html(sg_ko)
            en_content += f'''<div class="module">
<div class="module-top" onclick="this.parentElement.classList.toggle('open')">
  <div><h2>Study Guide</h2></div>
  <div style="display:flex;align-items:center;gap:12px"><span class="count">1 guide</span><span class="chevron">&#8250;</span></div>
</div>
<div class="overview-body">{sg_html}</div>
</div>'''
            ko_content += f'''<div class="module">
<div class="module-top" onclick="this.parentElement.classList.toggle('open')">
  <div><h2>스터디 가이드</h2></div>
  <div style="display:flex;align-items:center;gap:12px"><span class="count">1 guide</span><span class="chevron">&#8250;</span></div>
</div>
<div class="overview-body">{sg_ko_html}</div>
</div>'''

        page = HUB_TPL.replace('{title}', hub_title).replace('{nav}', nav)
        page = page.replace('{en_content}', en_content).replace('{ko_content}', ko_content)
        page = page.replace('href="index.html"', 'href="../index.html"')
        with open(os.path.join(BASE, 'pages', hub_name), 'w', encoding='utf-8') as f:
            f.write(page)
        print(f'  -> pages/{hub_name} saved ({len(page)} bytes)')

    print('\nAll done!')

if __name__ == '__main__':
    main()
