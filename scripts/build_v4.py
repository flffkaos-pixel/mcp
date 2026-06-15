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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#0d0d12;--card:#15151d;--card-hover:#1c1c26;--border:#2a2a35;--text:#e4e4e7;--muted:#888896;--accent:#5588ff;--accent-hover:#6699ff;--green:#22a67e;--amber:#e8a000;--radius:12px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR','Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7;-webkit-font-smoothing:antialiased}
.container{max-width:900px;margin:0 auto;padding:40px 24px}
h1{font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;letter-spacing:-0.02em}
h1 .ko{display:block;font-family:'Noto Sans KR','Inter',sans-serif;font-size:1.1rem;font-weight:400;color:var(--muted);margin-top:4px}
.subtitle{color:var(--muted);font-size:1.05rem;max-width:640px;margin:12px 0 0}
.stats-bar{display:flex;gap:24px;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 28px;margin:28px 0}
.stat-item{text-align:center;flex:1}
.stat-num{font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:var(--accent)}
.stat-label{font-size:0.8rem;color:var(--muted);margin-top:2px}
.toc-header{display:flex;justify-content:space-between;align-items:flex-end;margin:40px 0 20px}
.toc-header h2{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;letter-spacing:-0.02em}
.phase{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:12px;overflow:hidden}
.phase-header{display:flex;justify-content:space-between;align-items:center;padding:18px 24px;cursor:pointer;user-select:none;transition:background .15s}
.phase-header:hover{background:var(--card-hover)}
.phase-header .caret{font-family:'JetBrains Mono',monospace;color:var(--accent);font-size:0.85rem;transition:transform .2s;flex-shrink:0;margin-left:12px}
.phase.open .phase-header .caret{transform:rotate(90deg)}
.phase-info{flex:1;min-width:0}
.phase-info h3{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:600}
.phase-info .ko-sub{display:block;font-size:0.85rem;color:var(--muted);margin-top:2px}
.phase-meta{font-size:0.78rem;color:var(--muted);font-family:'JetBrains Mono',monospace;white-space:nowrap;margin-left:12px}
.phase-lessons{display:none;border-top:1px solid var(--border)}
.phase.open .phase-lessons{display:block}
.overview-body{display:none;border-top:1px solid var(--border);padding:24px}
.phase.open .overview-body{display:block}
.lesson{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;text-decoration:none;color:var(--text);border-bottom:1px solid var(--border);transition:background .15s;gap:16px}
.lesson:hover{background:var(--card-hover)}
.lesson:last-child{border-bottom:none}
.lesson-name{font-size:0.92rem;font-weight:500;flex:1;min-width:0}
.lesson-tags{display:flex;align-items:center;gap:8px;flex-shrink:0}
.tag{font-family:'JetBrains Mono',monospace;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;padding:3px 10px;border-radius:4px}
.tag.build{background:var(--accent);color:#fff}
.tag.learn{background:var(--green);color:#fff}
.tag.lang{color:var(--muted);font-size:0.72rem;font-family:'JetBrains Mono',monospace}
.status-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.status-dot.complete{background:var(--green)}
.status-dot.wip{background:var(--amber)}
.search{position:relative;margin:0 0 24px}
.search input{width:100%;padding:10px 16px;background:var(--card);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:0.9rem;font-family:'JetBrains Mono',monospace;outline:none;transition:border-color .2s}
.search input:focus{border-color:var(--accent)}
.no-results{display:none;text-align:center;padding:40px;color:var(--muted);font-family:'JetBrains Mono',monospace;font-size:0.85rem}
.colophon{margin-top:48px;padding-top:24px;border-top:1px solid var(--border);display:flex;justify-content:space-between;flex-wrap:wrap;gap:16px;font-size:0.85rem;color:var(--muted);font-family:'JetBrains Mono',monospace}
.colophon a{color:var(--accent);text-decoration:none}
.colophon a:hover{color:var(--accent-hover)}
.lang-content{display:none}
.lang-content.active{display:block}
.controls{display:flex;align-items:center;gap:8px}
.btn{border:1px solid var(--border);background:var(--card);color:var(--text);padding:6px 14px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:0.78rem;cursor:pointer;transition:all .2s}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn-active{background:var(--accent);color:#fff;border-color:var(--accent)}
.header-row{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px}
.overview-body h2,.overview-body h3,.overview-body h4{font-family:'JetBrains Mono',monospace;color:var(--text);margin:28px 0 12px}
.overview-body h2{font-size:1.3rem;font-weight:700}
.overview-body h3{font-size:1.1rem;font-weight:600}
.overview-body h4{font-size:0.95rem;font-weight:600}
.overview-body h5{font-size:0.9rem;font-weight:600;color:var(--text);margin:20px 0 8px}
.overview-body p{color:var(--muted);margin-bottom:14px;font-size:0.95rem}
.overview-body ul,.overview-body ol{color:var(--muted);padding-left:20px;margin-bottom:14px;font-size:0.95rem}
.overview-body li{margin-bottom:5px}
.overview-body a{color:var(--accent);text-decoration:none}
.overview-body a:hover{color:var(--accent-hover)}
.overview-body code{background:var(--bg);border:1px solid var(--border);color:var(--accent);padding:2px 6px;border-radius:4px;font-size:0.85rem;font-family:'JetBrains Mono',monospace}
.overview-body pre{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px;overflow-x:auto;margin-bottom:16px}
.overview-body pre code{background:none;border:none;color:var(--text);padding:0;font-size:0.82rem;line-height:1.6;display:block}
.overview-body table{width:100%;border-collapse:collapse;margin-bottom:16px}
.overview-body th,.overview-body td{border:1px solid var(--border);padding:8px 12px;text-align:left;font-size:0.88rem}
.overview-body th{background:var(--card-hover);font-weight:600;font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:var(--accent)}
.overview-body td{color:var(--muted)}
.overview-body strong{color:var(--text)}
.overview-body hr{border:none;border-top:1px solid var(--border);margin:24px 0}
.overview-body blockquote{border-left:3px solid var(--accent);padding:8px 16px;margin:16px 0;color:var(--muted)}
@media(max-width:640px){
.container{padding:24px 16px}
h1{font-size:1.5rem}
.stats-bar{gap:12px;padding:16px}
.stat-num{font-size:1.2rem}
.lesson{flex-wrap:wrap}
.lesson-tags{margin-left:auto}
.phase-meta{display:none}
.controls{margin-top:8px}
}
</style>
</head>
<body>
<div class="container">
<div class="header-row">
<div>
<a href="../index.html" style="text-decoration:none;color:inherit"><h1>MCP Academy<span class="ko">MCP Curriculum / {title}</span></h1></a>
<p class="subtitle">Explore modules and lessons. Click for details and code examples.</p>
<p class="subtitle" style="font-size:0.92rem;margin-top:4px">모듈과 레슨을 탐색하세요. 클릭하여 상세 내용과 코드 예제를 확인하세요.</p>
</div>
<div class="controls">
<button class="btn" id="langToggle"><span id="langLabel">KO</span></button>
</div>
</div>

<div id="content-en" class="lang-content">
<div class="stats-bar">
<div class="stat-item"><div class="stat-num" id="modsEn">0</div><div class="stat-label">Modules</div></div>
<div class="stat-item"><div class="stat-num" id="totalEn">0</div><div class="stat-label">Lessons</div></div>
</div>
<div class="toc-header"><h2>Curriculum</h2></div>
<div class="search">
<input type="text" id="searchEn" placeholder="Search lessons..." oninput="filter(this.value,'en')">
</div>
<div class="no-results" id="noEn">No results found.</div>
{en_content}
</div>

<div id="content-ko" class="lang-content">
<div class="stats-bar">
<div class="stat-item"><div class="stat-num" id="modsKo">0</div><div class="stat-label">모듈</div></div>
<div class="stat-item"><div class="stat-num" id="totalKo">0</div><div class="stat-label">레슨</div></div>
</div>
<div class="toc-header"><h2>커리큘럼</h2></div>
<div class="search">
<input type="text" id="searchKo" placeholder="레슨 검색..." oninput="filter(this.value,'ko')">
</div>
<div class="no-results" id="noKo">검색 결과가 없습니다.</div>
{ko_content}
</div>

<div class="colophon">
<span>MCP Academy</span>
<div>
<a href="../index.html">Home</a>
<span style="margin:0 8px;color:var(--border)">|</span>
<a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">GitHub</a>
<span style="margin:0 8px;color:var(--border)">|</span>
<a href="https://github.com/microsoft/mcp-for-beginners/blob/main/LICENSE" target="_blank">License</a>
</div>
</div>
</div>
<script>
document.addEventListener('DOMContentLoaded', function(){{
(function(){{
var t=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko');
function s(v){{e.classList.remove('active');k.classList.remove('active');if(v==='ko'){{k.classList.add('active');l.textContent='EN'}}else{{e.classList.add('active');l.textContent='KO'}}localStorage.setItem('mcp-lang',v)}}
t.addEventListener('click',function(){{var n=localStorage.getItem('mcp-lang')||'ko';s(n==='ko'?'en':'ko')}});
var n=localStorage.getItem('mcp-lang')||'ko';
s(n||'ko');
var totalLessons=document.querySelectorAll('.lesson').length/2;
var te=document.getElementById('totalEn'), tk=document.getElementById('totalKo'), me=document.getElementById('modsEn'), mk=document.getElementById('modsKo');
if(te) te.textContent=totalLessons;
if(tk) tk.textContent=totalLessons;
if(me) me.textContent=document.querySelectorAll('.phase').length/2;
if(mk) mk.textContent=document.querySelectorAll('.phase').length/2;
document.querySelectorAll('.phase-header').forEach(function(h){{h.addEventListener('click',function(){{this.parentElement.classList.toggle('open')}})}});
}})();
function filter(q,lang){{
var v=q.toLowerCase().trim(),phases=document.querySelectorAll('#content-'+lang+' .phase'),any=false;
phases.forEach(function(p){{
var lessons=p.querySelectorAll('.lesson'),has=false;
lessons.forEach(function(l){{var match=!v||l.querySelector('.lesson-name').textContent.toLowerCase().indexOf(v)>-1;l.style.display=match?'flex':'none';if(match)has=true;}});
p.style.display=has||!v?'':'none';if(has||!v)p.classList.add('open');
if(p.style.display!=='none')any=true;
}});
document.getElementById('no'+(lang==='ko'?'Ko':'En')).style.display=any?'none':'block';
}}
}});
</script>
</body>
</html>"""

# Template for individual lesson page
LESSON_TPL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{module_title} - MCP Academy</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#0d0d12;--card:#15151d;--card-hover:#1c1c26;--border:#2a2a35;--text:#e4e4e7;--muted:#888896;--accent:#5588ff;--accent-hover:#6699ff;--green:#22a67e;--amber:#e8a000;--radius:12px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR','Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7;-webkit-font-smoothing:antialiased}
.container{max-width:800px;margin:0 auto;padding:40px 24px}
.nav-bar{display:flex;justify-content:space-between;align-items:center;padding-bottom:16px;margin-bottom:24px;border-bottom:1px solid var(--border)}
.nav-bar a{font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:var(--accent);text-decoration:none}
.nav-bar a:hover{color:var(--accent-hover)}
.breadcrumb{font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:var(--muted);margin-bottom:4px}
.breadcrumb a{color:var(--accent);text-decoration:none}
.breadcrumb a:hover{color:var(--accent-hover)}
h1{font-family:'JetBrains Mono',monospace;font-size:1.8rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:24px}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;margin-bottom:20px}
.meta-grid{display:flex;flex-wrap:wrap;gap:12px}
.meta-item{flex:1;min-width:120px;text-align:center;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 16px}
.meta-item .label{font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:var(--accent);text-transform:uppercase;letter-spacing:0.04em}
.meta-item .value{font-size:0.95rem;margin-top:4px;font-weight:500}
.lang-content{display:none}
.lang-content.active{display:block}
.content h2,.content h3,.content h4{font-family:'JetBrains Mono',monospace;color:var(--text);margin:28px 0 12px}
.content h2{font-size:1.3rem;font-weight:700}
.content h3{font-size:1.1rem;font-weight:600}
.content h4{font-size:0.95rem;font-weight:600}
.content h5{font-size:0.9rem;font-weight:600;color:var(--text);margin:20px 0 8px}
.content p{color:var(--muted);margin-bottom:14px;font-size:0.95rem}
.content ul,.content ol{color:var(--muted);padding-left:20px;margin-bottom:14px;font-size:0.95rem}
.content li{margin-bottom:5px}
.content a{color:var(--accent);text-decoration:none}
.content a:hover{color:var(--accent-hover)}
.content code{background:var(--bg);border:1px solid var(--border);color:var(--accent);padding:2px 6px;border-radius:4px;font-size:0.85rem;font-family:'JetBrains Mono',monospace}
.content pre{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px;overflow-x:auto;margin-bottom:16px}
.content pre code{background:none;border:none;color:var(--text);padding:0;font-size:0.82rem;line-height:1.6;display:block}
.content table{width:100%;border-collapse:collapse;margin-bottom:16px}
.content th,.content td{border:1px solid var(--border);padding:8px 12px;text-align:left;font-size:0.88rem}
.content th{background:var(--card-hover);font-weight:600;font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:var(--accent)}
.content td{color:var(--muted)}
.content strong{color:var(--text)}
.content hr{border:none;border-top:1px solid var(--border);margin:24px 0}
.content blockquote{border-left:3px solid var(--accent);padding:8px 16px;margin:16px 0;color:var(--muted)}
.nav-links{display:flex;gap:16px;margin-top:32px;padding-top:24px;border-top:1px solid var(--border)}
.nav-link{flex:1;display:flex;flex-direction:column;padding:16px 20px;background:var(--card);border:1px solid var(--border);border-radius:8px;text-decoration:none;color:var(--text);transition:all .15s}
.nav-link:hover{background:var(--card-hover);border-color:var(--accent)}
.nav-link.next{text-align:right;align-items:flex-end}
.nav-link .dir{font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:var(--accent);text-transform:uppercase;letter-spacing:0.04em}
.nav-link .title{font-size:0.92rem;font-weight:500;margin-top:4px}
.colophon{margin-top:48px;padding-top:24px;border-top:1px solid var(--border);text-align:center;font-size:0.85rem;color:var(--muted);font-family:'JetBrains Mono',monospace}
.colophon a{color:var(--accent);text-decoration:none}
.colophon a:hover{color:var(--accent-hover)}
.controls{display:flex;align-items:center;gap:8px}
.btn{border:1px solid var(--border);background:var(--card);color:var(--text);padding:6px 14px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:0.78rem;cursor:pointer;transition:all .2s}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn-active{background:var(--accent);color:#fff;border-color:var(--accent)}
@media(max-width:640px){
.container{padding:24px 16px}
h1{font-size:1.4rem}
.meta-item{min-width:100px}
.nav-links{flex-direction:column}
}
</style>
</head>
<body>
<div class="container">
<div class="nav-bar">
<a href="{hub_back}">&larr; Back to {hub_title}</a>
<div class="controls">
<button class="btn" id="langToggle" type="button"><span id="langLabel">KO</span></button>
</div>
</div>
<div class="breadcrumb">
<a href="{hub_back}">{hub_title}</a> &rsaquo; {module_badge_text} &rsaquo; {lesson_title}
</div>
<h1>{lesson_title}</h1>
<div class="meta-grid">
<div class="meta-item"><div class="label">Module</div><div class="value">{module_badge_text}</div></div>
<div class="meta-item"><div class="label">Progress</div><div class="value">{progress_pct}%</div></div>
</div>
<div class="card">
<div id="content-en" class="lang-content content active">{en_content}</div>
<div id="content-ko" class="lang-content content">{ko_content}</div>
</div>
<div class="nav-links">{prev_link}{next_link}</div>
<div class="colophon">
MCP Academy &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">microsoft/mcp-for-beginners</a>
</div>
</div>
<script>
(function(){
var t=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko');
function s(v){e.classList.remove('active');k.classList.remove('active');if(v==='ko'){k.classList.add('active');l.textContent='EN'}else{e.classList.add('active');l.textContent='KO'}localStorage.setItem('mcp-lang',v)}
t.addEventListener('click',function(){var n=localStorage.getItem('mcp-lang')||'ko';s(n==='ko'?'en':'ko')});
var n=localStorage.getItem('mcp-lang')||'ko';
s(n||'ko');
})();
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
                    for phrase in ['_(동영상을 보려면 이미지를 클릭하세요)_', '_(클릭하여 동영상 보기)_', '_(위 이미지를 클릭하면 이 강의의 영상을 볼 수 있습니다)_', '_(동영상 보기)_', 'Click the image above to view video of this lesson', 'Click the image above to view the video for this lesson']:
                        k_html = k_html.replace(phrase, '')
                lang = s.get('lang', '')
                lesson_pages.append((fname, s['title'], e_html, k_html, lang))

            # If no lessons extracted, create one lesson from the full module content
            if not subs_en:
                safe_title = slugify(title_en)
                fname = f'm{num}_01-{safe_title}.html'
                main_en_clean = main_en
                main_ko_clean = main_ko
                for phrase in ['_(Click the image above to view video of this lesson)_', '_(Click the image above to view the video for this lesson)_', '_(동영상을 보려면 이미지를 클릭하세요)_', '_(클릭하여 동영상 보기)_', '_(위 이미지를 클릭하면 이 강의의 영상을 볼 수 있습니다)_', '_(동영상 보기)_']:
                    main_en_clean = main_en_clean.replace(phrase, '')
                    main_ko_clean = main_ko_clean.replace(phrase, '')
                lesson_pages.append((fname, title_en, main_en_clean, main_ko_clean, ''))

            for idx, (fname, lt, e_html, k_html, _) in enumerate(lesson_pages):
                total = len(lesson_pages)
                prev_l = lesson_pages[idx-1] if idx > 0 else None
                next_l = lesson_pages[idx+1] if idx < total-1 else None
                pct = int((idx + 1) / total * 100)
                prev_link = f'<a href="{prev_l[0]}" class="nav-link prev"><span class="dir">Previous</span><span class="title">{prev_l[1]}</span></a>' if prev_l else '<div></div>'
                next_link = f'<a href="{next_l[0]}" class="nav-link next"><span class="dir">Next</span><span class="title">{next_l[1]}</span></a>' if next_l else '<div></div>'
                badge = f'{title_en}'
                badge_text = f'{title_en}'
                badge_inline = f'{title_en}'
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
                rows = ''
                for item in lps:
                    fname, ltitle, _, _, llang = item if len(item) >= 5 else (item[0], item[1], None, None, '')
                    lname = ltitle if lang == 'en' else ltitle
                    cls = 'build' if llang else 'learn'
                    label = 'BUILD' if llang else 'LEARN'
                    lang_tag = f'<span class="tag lang">{llang}</span>' if llang else ''
                    rows += f'''<a href="../lessons/{fname}" class="lesson">
  <span class="lesson-name">{lname}</span>
  <span class="lesson-tags"><span class="tag {cls}">{label}</span>{lang_tag}</span>
</a>
'''
                entries.append(f'''<div class="phase">
<div class="phase-header" onclick="this.parentElement.classList.toggle('open')">
  <div class="phase-info"><h3>{title_en if lang=="en" else title_ko}</h3><div class="ko-sub">{title_ko if lang=="en" else title_en}</div></div>
  <div class="phase-meta">{len(lps)} lessons</div><span class="caret">&blacktriangleright;</span>
</div>
<div class="phase-lessons">{rows}</div>
</div>''')
            return '\n'.join(entries)

        en_content = build_hub_content('en')
        ko_content = build_hub_content('ko')

        if hub_name == 'production.html' and sg_en:
            sg_html = md_to_html(sg_en)
            sg_ko_html = md_to_html(sg_ko)
            en_content += f'''<div class="phase">
<div class="phase-header" onclick="this.parentElement.classList.toggle('open')">
  <div class="phase-info"><h3>Study Guide</h3><div class="ko-sub">Reference material</div></div>
  <div class="phase-meta">1 guide</div><span class="caret">&#9654;</span>
</div>
<div class="phase-lessons"><div class="overview-body" style="display:block;border-top:none;padding:24px">{sg_html}</div></div>
</div>'''
            ko_content += f'''<div class="phase">
<div class="phase-header" onclick="this.parentElement.classList.toggle('open')">
  <div class="phase-info"><h3>스터디 가이드</h3><div class="ko-sub">참고 자료</div></div>
  <div class="phase-meta">1 가이드</div><span class="caret">&#9654;</span>
</div>
<div class="phase-lessons"><div class="overview-body" style="display:block;border-top:none;padding:24px">{sg_ko_html}</div></div>
</div>'''

        page = HUB_TPL.replace('{title}', hub_title)
        page = page.replace('{en_content}', en_content).replace('{ko_content}', ko_content)
        page = page.replace('href="index.html"', 'href="../index.html"')
        with open(os.path.join(BASE, 'pages', hub_name), 'w', encoding='utf-8') as f:
            f.write(page)
        print(f'  -> pages/{hub_name} saved ({len(page)} bytes)')

    print('\nAll done!')

if __name__ == '__main__':
    main()
