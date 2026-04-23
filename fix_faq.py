import re
with open('faq.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'(<ul class="nav-links">.*?)(</ul>)'
match = re.search(pattern, content, re.DOTALL)
if match:
    inner = match.group(1)
    if 'transportation.html' not in inner:
        print("Missing transportation")
    if 'resources/index.html' not in inner:
        print("Missing resources")
        
    inner = inner.rstrip()
    if 'transportation.html' not in inner:
        inner += '\n      <li><a href="transportation.html">交通方式</a></li>'
    if 'resources/index.html' not in inner and 'resources.html' not in inner:
        inner += '\n      <li><a href="resources/index.html">資源連結</a></li>'
    inner += '\n    '
    
    content = content[:match.start()] + inner + '</ul>' + content[match.end():]
    with open('faq.html', 'w', encoding='utf-8') as f:
        f.write(content)
