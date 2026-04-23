import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    
    # 1. Clean up duplicate 資源連結 lines
    content = re.sub(r'(<li><a href="resources/index\.html"[^>]*>資源連結</a></li>\s*)+', r'<li><a href="resources/index.html">資源連結</a></li>\n', content)
    content = re.sub(r'(<li><a href="\.\./resources/index\.html"[^>]*>資源連結</a></li>\s*)+', r'<li><a href="../resources/index.html">資源連結</a></li>\n', content)
    content = re.sub(r'(<li><a href="\.\./\.\./resources/index\.html"[^>]*>資源連結</a></li>\s*)+', r'<li><a href="../../resources/index.html">資源連結</a></li>\n', content)

    # 2. Fix Header Nav
    # We want to make sure the header nav has all 7 links in order.
    # The links are: index, services, team, news, faq, transportation, resources/index.html
    
    if filepath.endswith('.html'):
        # For non-nested HTML files
        if '/' not in filepath and not filepath.startswith('resources'):
            # First, make sure faq, transportation, resources exist at the end of nav-links
            # We'll use regex to find the end of nav-links
            nav_ul_pattern = r'(<ul class="nav-links">.*?)(</ul>)'
            match = re.search(nav_ul_pattern, content, re.DOTALL)
            if match:
                inner_html = match.group(1)
                # Check if it's missing faq, transportation, resources
                if 'faq.html' not in inner_html:
                    inner_html += '      <li><a href="faq.html">常見問答</a></li>\n'
                if 'transportation.html' not in inner_html:
                    inner_html += '      <li><a href="transportation.html">交通方式</a></li>\n'
                if 'resources/index.html' not in inner_html and 'resources.html' not in inner_html:
                    inner_html += '      <li><a href="resources/index.html">資源連結</a></li>\n    '
                
                # Replace back
                content = content[:match.start()] + inner_html + '</ul>' + content[match.end():]
                
        # 3. Fix Footer
        # Find <h4>快速連結</h4> ... </ul>
        footer_ul_pattern = r'(<h4>快速連結</h4>\s*<ul>.*?)(</ul>)'
        match = re.search(footer_ul_pattern, content, re.DOTALL)
        if match:
            inner_html = match.group(1)
            if 'transportation.html' not in inner_html:
                inner_html += '          <li><a href="transportation.html">交通方式</a></li>\n'
            if 'resources/index.html' not in inner_html and 'resources.html' not in inner_html:
                inner_html += '          <li><a href="resources/index.html">資源連結</a></li>\n        '
            
            content = content[:match.start()] + inner_html + '</ul>' + content[match.end():]

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.html'):
            fix_file(os.path.join(root, f))
