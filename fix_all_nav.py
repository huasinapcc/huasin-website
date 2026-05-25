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
    parts = filepath.split(os.sep)
    depth = len(parts) - 1 # ignoring '.'
    prefix = '../' * (depth - 1)
    
    # Generate exact paths
    index_link = f'{prefix}index.html'
    services_link = f'{prefix}services.html'
    team_link = f'{prefix}team.html'
    news_link = f'{prefix}news.html'
    faq_link = f'{prefix}faq.html'
    transport_link = f'{prefix}transportation.html'
    resource_link = f'{prefix}resources/index.html'
    assessment_link = f'{prefix}burnout-assessment.html'
    thermometer_link = f'{prefix}resources/mood-thermometer/index.html'
    support_link = f'{prefix}resources/immediate-support/index.html'
    free_link = f'{prefix}resources/free-counseling-taiwan/index.html'

    # Determine which navigation tab is active based on file name/path
    basename = os.path.basename(filepath)
    is_root = depth == 1

    index_active = ' class="active"' if (basename == 'index.html' and is_root) else ''
    services_active = ' class="active"' if (basename == 'services.html' or 'service-' in basename) else ''
    team_active = ' class="active"' if (basename == 'team.html' or 'therapist' in basename) else ''
    news_active = ' class="active"' if (basename == 'news.html' or basename == 'article.html') else ''
    faq_active = ' class="active"' if (basename == 'faq.html') else ''
    transport_active = ' class="active"' if (basename == 'transportation.html') else ''
    resource_active = ' class="active"' if ('resources' in filepath or basename == 'burnout-assessment.html') else ''

    # Reconstruct the header nav-links inner HTML
    new_nav_inner = f'''<ul class="nav-links">
      <li><a href="{index_link}"{index_active}>關於我們</a></li>
      <li><a href="{services_link}"{services_active}>服務項目</a></li>
      <li class="has-dropdown">
        <a href="{team_link}"{team_active}>專業團隊</a>
        <div class="dropdown-menu" id="navTherapistDropdown"></div>
      </li>
      <li><a href="{news_link}"{news_active}>最新消息</a></li>
      <li><a href="{faq_link}"{faq_active}>常見問答</a></li>
      <li><a href="{transport_link}"{transport_active}>交通方式</a></li>
      <li class="has-dropdown">
        <a href="{resource_link}"{resource_active}>資源連結</a>
        <div class="dropdown-menu">
          <div class="dropdown-menu-inner">
            <a href="{resource_link}">資源總覽</a>
            <a href="{assessment_link}">電量自評</a>
            <a href="{thermometer_link}">心情溫度計</a>
            <a href="{support_link}">即時資源專線</a>
            <a href="{free_link}">全台免費諮商</a>
          </div>
        </div>
      </li>
    '''

    nav_pattern = r'<ul class="nav-links">.*?(</ul>)'
    match = re.search(nav_pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + new_nav_inner + '</ul>' + content[match.end():]
        
    # Reconstruct the footer quick links
    new_footer_inner = f'''<h4>快速連結</h4>
        <ul>
          <li><a href="{team_link}">專業團隊</a></li>
          <li><a href="{assessment_link}">電量自評</a></li>
          <li><a href="{faq_link}">常見問答</a></li>
          <li><a href="{transport_link}">交通方式</a></li>
          <li><a href="{resource_link}">資源連結</a></li>
        '''

    footer_pattern = r'<h4>快速連結</h4>\s*<ul>.*?(</ul>)'
    fmatch = re.search(footer_pattern, content, re.DOTALL)
    if fmatch:
        content = content[:fmatch.start()] + new_footer_inner + '</ul>' + content[fmatch.end():]

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
