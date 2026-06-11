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
<html class="light" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title} - MCP Curriculum</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
:root {{ --bg:#f8f9ff;--text:#0d1c2f;--muted:#404752;--accent:#005faa;--border:#c2c7cf;--card:#ffffff;--card-hover:#eff4ff;--radius:12px; }}
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7; }}
.container {{ max-width:900px;margin:0 auto;padding:32px 24px; }}
header {{ position:fixed;top:0;width:100%;z-index:50;border-bottom:1px solid var(--border);background:rgba(255,255,255,0.85);backdrop-filter:blur(12px);height:60px; }}
.header-inner {{ max-width:900px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center;height:100%; }}
nav {{ display:flex;gap:20px; }}
nav a {{ font-size:0.85rem;font-weight:500;color:var(--muted);text-decoration:none;transition:color .15s; }}
nav a:hover,nav a.active {{ color:var(--accent); }}
nav a.active {{ border-bottom:2px solid var(--accent); }}
.module-card {{ margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;background:var(--card); }}
.module-header {{ display:flex;justify-content:space-between;align-items:center;padding:14px 20px;cursor:pointer;user-select:none;transition:background .15s; }}
.module-header:hover {{ background:var(--card-hover); }}
.module-id {{ font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:var(--muted);min-width:36px; }}
.module-name {{ font-weight:600;flex:1;font-size:0.95rem; }}
.module-name .ko {{ color:var(--muted);font-weight:400;font-size:0.85rem;display:block;margin-top:2px; }}
.module-meta {{ font-size:0.78rem;color:var(--muted); }}
.module-lessons {{ display:none;padding:0 20px 14px; }}
.module-card.open .module-lessons {{ display:block; }}
.lesson-item {{ display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-radius:8px;gap:10px;text-decoration:none;color:var(--text);transition:background .15s;margin-bottom:2px; }}
.lesson-item:hover {{ background:var(--card-hover); }}
.lesson-item .name {{ flex:1;font-size:0.88rem;font-weight:500; }}
.lesson-item .name .ko {{ color:var(--muted);font-weight:400;font-size:0.8rem;display:block; }}
.lesson-item .meta {{ font-size:0.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace; }}
footer {{ border-top:1px solid var(--border);padding:24px;margin-top:48px;text-align:center;font-size:0.8rem;color:var(--muted); }}
footer a {{ color:var(--accent);text-decoration:none; }}
.lang-content {{ display:none; }}
.lang-content.active {{ display:block; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
</head>
<body>
<header>
<div class="header-inner">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-[var(--accent)] text-2xl">extension</span>
<span class="font-bold text-sm">MCP Curriculum</span>
</div>
<nav>{nav}</nav>
<div id="langToggle" class="flex items-center gap-1 cursor-pointer text-[var(--muted)] hover:text-[var(--accent)] transition-colors">
<span class="material-symbols-outlined text-lg">translate</span>
<span class="text-xs font-semibold tracking-wide" id="langLabel">KO / EN</span>
</div>
</div>
</header>
<main class="pt-[76px]"><div class="container">
<h1 class="text-2xl font-bold mb-6">{title}</h1>
<div id="content-en" class="lang-content">{en_content}</div>
<div id="content-ko" class="lang-content">{ko_content}</div>
</div></main>
<footer><p>MCP Curriculum &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">microsoft/mcp-for-beginners</a></p>
<div class="flex justify-center gap-4 mt-2"><a href="index.html">Home</a> <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">GitHub</a> <a href="https://github.com/microsoft/mcp-for-beginners/blob/main/LICENSE" target="_blank">License</a></div></footer>
<script>
(function(){{var b=document.getElementById('langToggle'),l=document.getElementById('langLabel'),e=document.getElementById('content-en'),k=document.getElementById('content-ko'),n=localStorage.getItem('mcp-lang')||'ko';function s(t){{document.querySelectorAll('.lang-content').forEach(function(x){{x.classList.remove('active')}});if(t==='en'&&e){{e.classList.add('active');l.textContent='EN / KO'}}else{{k&&k.classList.add('active');l.textContent='KO / EN'}}localStorage.setItem('mcp-lang',t)}}if(b)b.addEventListener('click',function(){{s(n==='ko'?'en':'ko')}});s(n);document.querySelectorAll('.module-header').forEach(function(h){{h.addEventListener('click',function(){{this.parentElement.classList.toggle('open')}})}});}})();
</script>
</body>
</html>"""

# Template for individual lesson page
LESSON_TPL = """<!DOCTYPE html>
<html class="light" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{lesson_title} - {module_title} - MCP Curriculum</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
:root {{ --bg:#f8f9ff;--text:#0d1c2f;--muted:#404752;--accent:#005faa;--accent-hover:#004883;--border:#c2c7cf;--card:#ffffff;--code-bg:#0F172A;--radius:12px; }}
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7; }}
.container {{ max-width:900px;margin:0 auto;padding:32px 24px; }}
header {{ position:fixed;top:0;width:100%;z-index:50;border-bottom:1px solid var(--border);background:rgba(255,255,255,0.85);backdrop-filter:blur(12px);height:60px; }}
.header-inner {{ max-width:900px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center;height:100%; }}
.breadcrumb {{ font-size:0.8rem;color:var(--muted);margin-bottom:20px; }}
.breadcrumb a {{ color:var(--accent);text-decoration:none; }}
.breadcrumb a:hover {{ text-decoration:underline; }}
.lesson-nav {{ display:flex;justify-content:space-between;margin-top:32px;padding-top:20px;border-top:1px solid var(--border); }}
.lesson-nav a {{ color:var(--accent);text-decoration:none;font-size:0.9rem; }}
.lesson-nav a:hover {{ text-decoration:underline; }}
.lang-content {{ display:none; }}
.lang-content.active {{ display:block; }}
footer {{ border-top:1px solid var(--border);padding:24px;margin-top:48px;text-align:center;font-size:0.8rem;color:var(--muted); }}
footer a {{ color:var(--accent);text-decoration:none; }}
.material-symbols-outlined {{ font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
</head>
<body>
<header>
<div class="header-inner">
<div class="flex items-center gap-2">
<a href="{hub_back}" class="flex items-center gap-1 text-[var(--accent)] text-sm font-medium no-underline">
<span class="material-symbols-outlined text-lg">arrow_back</span>
MCP Curriculum
</a>
</div>
<div id="langToggle" class="flex items-center gap-1 cursor-pointer text-[var(--muted)] hover:text-[var(--accent)] transition-colors">
<span class="material-symbols-outlined text-lg">translate</span>
<span class="text-xs font-semibold tracking-wide" id="langLabel">KO / EN</span>
</div>
</div>
</header>
<main class="pt-[76px]"><div class="container">
<div class="breadcrumb"><a href="{hub_back}">{hub_title}</a> &rsaquo; {module_badge} &rsaquo; {lesson_title}</div>
<div id="content-en" class="lang-content">{en_content}</div>
<div id="content-ko" class="lang-content">{ko_content}</div>
<div class="lesson-nav">
  <span>{prev_link}</span>
  <span>{next_link}</span>
</div>
</div></main>
<footer><p>MCP Curriculum &mdash; <a href="https://github.com/microsoft/mcp-for-beginners" target="_blank">microsoft/mcp-for-beginners</a></p></footer>
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
            main_ko = md_to_html(md_ko, folder, True)

            lesson_pages = []
            for idx, s in enumerate(subs_en):
                safe_title = re.sub(r'[^a-zA-Z0-9\uAC00-\uD7A3\s-]', '', s['title']).strip().lower().replace(' ', '-')[:40] or 'lesson'
                fname = f'm{num}_{idx+1:02d}-{safe_title}.html'
                fpath = f'lessons/{fname}'
                e_html = md_to_html(s['content'], s['folder'], False)
                if md_ko == md_en:
                    k_html = e_html
                else:
                    kl = subs_ko[idx] if idx < len(subs_ko) else None
                    k_html = md_to_html(kl['content'], kl['folder'], True) if kl else e_html
                lesson_pages.append((fname, s['title'], e_html, k_html))

            for idx, (fname, lt, e_html, k_html) in enumerate(lesson_pages):
                total = len(lesson_pages)
                prev_l = lesson_pages[idx-1] if idx > 0 else None
                next_l = lesson_pages[idx+1] if idx < total-1 else None
                prev_link = f'<a href="{prev_l[0]}">&larr; {prev_l[1]}</a>' if prev_l else ''
                next_link = f'<a href="{next_l[0]}">{next_l[1]} &rarr;</a>' if next_l else ''
                badge = f'<span class="text-xs font-semibold tracking-wide uppercase text-[var(--accent)]">Module {num}: {title_en}</span>'
                page = LESSON_TPL.replace('{lesson_title}', lt)
                for k, v in [('{module_title}', title_en), ('{hub_back}', f'../{hub_name}'), ('{hub_title}', hub_title), ('{module_badge}', badge), ('{prev_link}', prev_link), ('{next_link}', next_link), ('{en_content}', e_html), ('{ko_content}', k_html)]:
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
                    for fname, ltitle, _, _ in lps:
                        lname = ltitle if lang == 'en' else ltitle
                        lessons_html += f'<a class="lesson-item" href="../lessons/{fname}"><span class="name">{lname}</span><span class="meta">M{num}</span></a>\n'
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
