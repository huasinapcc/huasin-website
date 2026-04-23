import os
import re

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.html') and 'node_modules' not in root:
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            nav_pattern = r'(<ul class="nav-links">.*?</ul>)'
            match = re.search(nav_pattern, content, re.DOTALL)
            if match:
                inner = match.group(1)
                missing = []
                if 'transportation.html' not in inner and '../transportation.html' not in inner and '../../transportation.html' not in inner:
                    missing.append('transportation.html')
                if 'resources' not in inner:
                    missing.append('resources/index.html')
                
                if missing:
                    print(f"{filepath} is missing in header: {missing}")
                    
            footer_pattern = r'(<h4>快速連結</h4>\s*<ul>.*?</ul>)'
            fmatch = re.search(footer_pattern, content, re.DOTALL)
            if fmatch:
                finner = fmatch.group(1)
                missing_f = []
                if 'transportation.html' not in finner and '../transportation.html' not in finner and '../../transportation.html' not in finner:
                    missing_f.append('transportation.html')
                if 'resources' not in finner:
                    missing_f.append('resources/index.html')
                
                if missing_f:
                    print(f"{filepath} is missing in footer: {missing_f}")
