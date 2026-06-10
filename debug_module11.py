import urllib.request, re
RAW = 'https://raw.githubusercontent.com/microsoft/mcp-for-beginners/main'
folder = '11-MCPServerHandsOnLabs'
req = urllib.request.Request(f'{RAW}/{folder}/README.md', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as r:
    md = r.read().decode('utf-8')
idx = md.find('./00-Introduction/README.md')
start = max(0, idx-200)
end = min(len(md), idx+300)
with open('debug_mod11.txt', 'w', encoding='utf-8') as f:
    f.write(md[start:end])
print("Done")
