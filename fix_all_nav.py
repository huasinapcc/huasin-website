import os
import re

def fix_file(filepath):
    # Skip temporary or backup files
    if '~' in filepath or '#' in filepath:
        return

    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    original = content
    
    # Calculate relative prefix based on depth
    # e.g., ./index.html -> depth 1, prefix = ""
    # e.g., ./resources/index.html -> depth 2, prefix = "../"
    parts = filepath.split(os.sep)
    depth = len(parts) - 1 # ignoring '.'
    prefix = '../' * (depth - 1)
    
    # Replace resources.html with resources/index.html
    # In some places they used resources.html but the folder is resources/index.html
    # Let's just append the missing ones exactly.
    
    faq_link = f'{prefix}faq.html'
    transport_link = f'{prefix}transportation.html'
    resource_link = f'{prefix}resources/index.html'
    assessment_link = f'{prefix}burnout-assessment.html'

    nav_pattern = r'(<ul class="nav-links">.*?)(</ul>)'
    match = re.search(nav_pattern, content, re.DOTALL)
    if match:
        inner = match.group(1)
        inner = inner.rstrip()
        
        # If transportation is missing
        if 'transportation.html' not in inner:
            inner += f'\n      <li><a href="{transport_link}">交通方式</a></li>'
            
        # If resources is missing
        if 'resources' not in inner and '資源連結' not in inner:
            inner += f'\n      <li><a href="{resource_link}">資源連結</a></li>'
            
        # If burnout assessment is missing
        if 'burnout-assessment.html' not in inner:
            # Try to insert after news.html
            news_pattern = rf'<li><a href="{prefix}news.html"( class="active")?>最新消息</a></li>'
            if re.search(news_pattern, inner):
                replacement = f'<li><a href="{prefix}news.html"\\1>最新消息</a></li>\n      <li><a href="{assessment_link}">電量自評</a></li>'
                inner = re.sub(news_pattern, replacement, inner)
            else:
                inner += f'\n      <li><a href="{assessment_link}">電量自評</a></li>'
            
        inner += '\n    '
        content = content[:match.start()] + inner + '</ul>' + content[match.end():]
        
    footer_pattern = r'(<h4>快速連結</h4>\s*<ul>.*?)(</ul>)'
    fmatch = re.search(footer_pattern, content, re.DOTALL)
    if fmatch:
        finner = fmatch.group(1)
        finner = finner.rstrip()
        
        if 'transportation.html' not in finner:
            finner += f'\n          <li><a href="{transport_link}">交通方式</a></li>'
            
        if 'resources' not in finner and '資源連結' not in finner:
            finner += f'\n          <li><a href="{resource_link}">資源連結</a></li>'
            
        # If burnout assessment is missing
        if 'burnout-assessment.html' not in finner:
            team_pattern = rf'<li><a href="{prefix}team.html">專業團隊</a></li>'
            if re.search(team_pattern, finner):
                replacement = f'<li><a href="{prefix}team.html">專業團隊</a></li>\n          <li><a href="{assessment_link}">電量自評</a></li>'
                finner = re.sub(team_pattern, replacement, finner)
            else:
                finner += f'\n          <li><a href="{assessment_link}">電量自評</a></li>'
            
        finner += '\n        '
        content = content[:fmatch.start()] + finner + '</ul>' + content[fmatch.end():]

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or '.gemini' in root or 'antigravity' in root:
        continue
    for f in files:
        if f.endswith('.html'):
            fix_file(os.path.join(root, f))
