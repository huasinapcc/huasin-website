#!/usr/bin/env python3
"""
心理師靜態頁面產生器
用法: python3 generate_pages.py

從 Google Sheets 拉取心理師資料，為每位心理師產生靜態 HTML（therapist-{id}.html）。
心理師異動時：改 Sheets → 執行此腳本 → git push
"""

import json
import re
import urllib.request
import os
import html as html_module

SHEET_ID = '1o0di_U7q_NKiDuwkHEnUqlX2QQNxAeXR1TKpAJl0WAQ'
THERAPISTS_SHEET = 'therapists'
ARTICLES_SHEET = 'articles'
BASE_URL = 'https://www.hua-sin.com'
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_sheet(sheet_name):
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json&sheet={urllib.parse.quote(sheet_name)}'
    with urllib.request.urlopen(url) as r:
        text = r.read().decode('utf-8')
    match = re.search(r'\{.*\}', text, re.DOTALL)
    obj = json.loads(match.group())
    cols = [c.get('label', '').lower().strip() for c in obj['table']['cols']]
    rows = obj['table']['rows'] or []
    result = []
    for row in rows:
        record = {}
        for i, col in enumerate(cols):
            val = row['c'][i]
            record[col] = val.get('v', '') if val else ''
        result.append(record)
    return result


def parse_lines(s):
    if not s:
        return []
    return [x.strip() for x in re.split(r'[\n；;]', str(s)) if x.strip()]


def drive_img_url(url):
    if not url:
        return ''
    m = re.search(r'/d/([a-zA-Z0-9_-]+)', str(url))
    if m:
        return f'https://lh3.googleusercontent.com/d/{m[1]}=w400'
    return str(url)


def h(s):
    return html_module.escape(str(s)) if s else ''


def render_list_items(lines):
    return ''.join(f'<li class="info-item">{h(line)}</li>' for line in lines)


def render_therapist_page(t, all_therapists, articles):
    tid = str(t.get('id', '')).rstrip('.0') if str(t.get('id', '')).endswith('.0') else str(t.get('id', ''))
    # normalize id to integer string
    try:
        tid = str(int(float(t['id'])))
    except Exception:
        tid = str(t.get('id', ''))

    name = t.get('name', '')
    title = t.get('title', '')
    license_no = t.get('license_no', '')
    philosophy = t.get('philosophy', '')
    specialties = t.get('specialties', '')

    positions = parse_lines(t.get('current_positions', ''))
    education = parse_lines(t.get('education', ''))
    experience = parse_lines(t.get('experience', ''))
    certifications = parse_lines(t.get('certifications', ''))
    social_links = t.get('social_links', '')

    # Photo: try local file, then Drive URL
    local_avif = f'images/therapists/{tid}.avif'
    local_png = f'images/therapists/{tid}.png'
    avif_exists = os.path.exists(os.path.join(OUTPUT_DIR, local_avif))
    png_exists = os.path.exists(os.path.join(OUTPUT_DIR, local_png))
    drive_url = drive_img_url(t.get('photo_url', ''))

    if avif_exists:
        photo_html = f'<img src="{local_avif}" alt="{h(name)}">'
    elif png_exists:
        photo_html = f'<img src="{local_png}" alt="{h(name)}">'
    elif drive_url:
        photo_html = f'<img src="{h(drive_url)}" alt="{h(name)}">'
    else:
        photo_html = f'<div class="photo-placeholder">{h(name[0]) if name else ""}</div>'

    # Articles matching this therapist
    my_articles = [
        a for a in articles
        if str(a.get('active', '')).upper() == 'TRUE'
        and (str(a.get('author_id', '')).strip() == name or str(a.get('author_id', '')).strip() == tid)
    ]

    articles_html = ''
    if my_articles:
        for a in my_articles:
            art_id = str(a.get('id', '')).rstrip('.0')
            try:
                art_id = str(int(float(a['id'])))
            except Exception:
                pass
            articles_html += f'<a href="article.html?id={art_id}" class="article-link">・ {h(a.get("title",""))}</a>'

    # Social links
    links_html = ''
    if social_links:
        for lnk in social_links.split('|'):
            parts = lnk.strip().split(':', 1)
            if len(parts) == 2:
                label, url = parts[0].strip(), parts[1].strip()
                full_url = url if url.startswith('http') else 'https://' + url
                links_html += f'<div class="info-item"><strong>{h(label)}:</strong> <a href="{h(full_url)}" target="_blank" class="article-link" style="display:inline">{h(url)}</a></div>'

    # Prev/Next navigation
    active_all = [x for x in all_therapists if str(x.get('active', '')).upper() == 'TRUE' and x.get('name')]
    idx = next((i for i, x in enumerate(active_all) if str(x.get('id', '')) == str(t.get('id', ''))), -1)
    prev_link = ''
    next_link = ''
    if idx > 0:
        prev = active_all[idx - 1]
        prev_id = str(int(float(prev['id'])))
        prev_link = f'<a href="therapist-{prev_id}.html" class="pn-link">← 上一位: {h(prev["name"])}</a>'
    if idx < len(active_all) - 1:
        nxt = active_all[idx + 1]
        nxt_id = str(int(float(nxt['id'])))
        next_link = f'<a href="therapist-{nxt_id}.html" class="pn-link">下一位: {h(nxt["name"])} →</a>'

    # Blocks visibility
    def block(block_id, title_text, content_html):
        if not content_html.strip():
            return ''
        return f'''
        <div id="{block_id}">
          <span class="section-title">{title_text}</span>
          {content_html}
        </div>'''

    positions_block = block('positionsBlock', '現職', f'<ul class="info-list">{render_list_items(positions)}</ul>')
    education_block = block('educationBlock', '學歷', f'<ul class="info-list">{render_list_items(education)}</ul>')
    experience_block = block('experienceBlock', '經歷', f'<ul class="info-list">{render_list_items(experience)}</ul>')
    certs_block = block('certsBlock', '專業證照', f'<ul class="info-list">{render_list_items(certifications)}</ul>')
    articles_block = block('articlesBlock', '發表文章', articles_html)
    links_block = block('linksBlock', '個人專頁連結', links_html)

    philosophy_block = ''
    if philosophy:
        philosophy_block = f'''
        <div class="side-box mint" id="philosophyBlock">
          <h3>諮商理念</h3>
          <p class="side-text">{h(philosophy)}</p>
        </div>'''

    specialties_block = ''
    if specialties:
        specialties_block = f'''
        <div class="side-box blue" id="specialtiesBlock">
          <h3>諮商專長</h3>
          <p class="side-text">{h(specialties)}</p>
        </div>'''

    page_url = f'{BASE_URL}/therapist-{tid}.html'
    desc = f'{name}{title}，{specialties[:60] if specialties else ""}｜華昕藝心心理諮商所'

    return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{h(name)} {h(title)}｜華昕藝心心理諮商所</title>
  <meta name="description" content="{h(desc)}">
  <meta name="keywords" content="{h(name)},心理師,{h(title)},南港心理諮商,華昕藝心">
  <link rel="canonical" href="{page_url}">
  <meta property="og:type" content="profile">
  <meta property="og:locale" content="zh_TW">
  <meta property="og:site_name" content="華昕藝心心理諮商所">
  <meta property="og:url" content="{page_url}">
  <meta property="og:title" content="{h(name)} {h(title)}｜華昕藝心心理諮商所">
  <meta property="og:description" content="{h(desc)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{h(name)} {h(title)}｜華昕藝心心理諮商所">
  <meta name="twitter:description" content="{h(desc)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;500&family=Noto+Sans+TC:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="nav-dropdown.css">
  <style>
    :root {{ --blue: #7BB8C8; --mint: #A8D5C2; --sand: #F5F0EA; --dark: #2C4A5A; --white: #FAFAFA; --lb: #E3F2F7; --lm: #E9F5F0; --muted: #6B8A98 }}
    * {{ margin: 0; padding: 0; box-sizing: border-box }}
    html {{ scroll-behavior: smooth }}
    body {{ font-family: 'Noto Sans TC', sans-serif; background: #fff; color: var(--dark); line-height: 1.7 }}
    nav {{ position: fixed; top: 0; width: 100%; z-index: 1000; background: rgba(255,255,255,.9); backdrop-filter: blur(10px); border-bottom: 1px solid #eee; padding: 0 56px; height: 72px; display: flex; align-items: center; justify-content: space-between }}
    .logo {{ font-family: 'Noto Serif TC', serif; font-size: 18px; font-weight: 500; letter-spacing: 4px; color: var(--dark); text-decoration: none }}
    .logo em {{ font-style: normal; color: var(--blue) }}
    .nav-links {{ display: flex; gap: 40px; list-style: none }}
    .nav-links a {{ text-decoration: none; color: var(--dark); font-size: 14px; letter-spacing: 1px; transition: all .3s }}
    .nav-links a:hover, .nav-links a.active {{ color: var(--blue) }}
    .header-section {{ padding: 140px 56px 60px; max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 60px }}
    .photo-circle {{ width: 220px; height: 220px; border-radius: 50%; overflow: hidden; background: var(--lb); flex-shrink: 0 }}
    .photo-circle img {{ width: 100%; height: 100%; object-fit: cover }}
    .photo-placeholder {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif TC', serif; font-size: 72px; color: var(--blue) }}
    .name-info h1 {{ font-family: 'Noto Serif TC', serif; font-size: 42px; font-weight: 400; color: var(--dark); letter-spacing: 6px; margin-bottom: 10px }}
    .name-info h1 em {{ font-style: normal; color: var(--blue); font-size: 24px; margin-left: 14px; letter-spacing: 2px }}
    .license-no {{ font-size: 16px; color: var(--muted); letter-spacing: 2px }}
    .main-grid {{ max-width: 1200px; margin: 0 auto; padding: 0 56px 120px; display: grid; grid-template-columns: 1fr 420px; gap: 80px; align-items: start }}
    .left-col {{ display: flex; flex-direction: column; gap: 50px }}
    .right-col {{ display: flex; flex-direction: column; gap: 30px; position: sticky; top: 100px }}
    .section-title {{ font-family: 'Noto Serif TC', serif; font-size: 22px; color: var(--blue); letter-spacing: 4px; margin-bottom: 20px; display: block }}
    .info-list {{ list-style: none }}
    .info-item {{ font-size: 15px; color: var(--dark); margin-bottom: 10px; line-height: 1.8 }}
    .info-item strong {{ font-weight: 500; margin-right: 8px }}
    .article-link {{ display: block; font-size: 15px; color: var(--dark); text-decoration: none; margin-bottom: 12px; transition: color .2s }}
    .article-link:hover {{ color: var(--blue) }}
    .side-box {{ padding: 40px; border-radius: 12px }}
    .side-box.mint {{ background: var(--lm) }}
    .side-box.blue {{ background: var(--lb) }}
    .side-box h3 {{ font-family: 'Noto Serif TC', serif; font-size: 20px; color: var(--dark); letter-spacing: 4px; margin-bottom: 24px; text-align: center }}
    .side-text {{ font-size: 15px; line-height: 2.2; color: var(--dark); white-space: pre-wrap }}
    .page-nav {{ padding: 60px 56px 120px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #eee; max-width: 1200px; margin: 0 auto }}
    .pn-link {{ text-decoration: none; color: var(--muted); font-size: 14px; display: flex; align-items: center; gap: 10px }}
    .pn-link:hover {{ color: var(--blue) }}
    .line-float {{ position: fixed; bottom: 30px; right: 30px; background: #06C755; color: #fff; padding: 12px 24px; border-radius: 100px; text-decoration: none; display: flex; align-items: center; gap: 10px; box-shadow: 0 10px 30px rgba(6,199,85,.3); z-index: 9999; transition: transform .3s; font-size: 14px }}
    .line-float:hover {{ transform: translateY(-5px) }}
    .cta-btns {{ display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; position: relative; z-index: 2; margin-top: 20px }}
    .btn-o-white {{ border: 1.5px solid #fff; color: #fff; padding: 12px 34px; border-radius: 40px; text-decoration: none; font-size: 14px; letter-spacing: 2px; transition: all .3s }}
    .btn-o-white:hover {{ background: rgba(255,255,255,.1); transform: translateY(-3px) }}
    footer {{ background: var(--dark); color: #fff; padding: 80px 56px 40px }}
    .fg {{ display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 60px; margin-bottom: 60px }}
    .fb h3 {{ font-family: 'Noto Serif TC', serif; font-size: 18px; letter-spacing: 3px; margin-bottom: 15px }}
    .fb p {{ font-size: 13px; color: rgba(255,255,255,0.4); line-height: 2.2; margin-bottom: 24px }}
    .socs {{ display: flex; gap: 12px }}
    .soc {{ width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; transition: background 0.3s }}
    .soc:hover {{ background: var(--blue) }}
    .soc svg {{ width: 18px; height: 18px; stroke: #fff; fill: none; stroke-width: 1.5 }}
    .fc h4 {{ font-size: 11px; letter-spacing: 4px; color: var(--mint); margin-bottom: 20px }}
    .fc ul {{ list-style: none }}
    .fc li {{ margin-bottom: 10px }}
    .fc a {{ color: rgba(255,255,255,0.4); text-decoration: none; font-size: 14px; transition: color 0.2s }}
    .fc a:hover {{ color: #fff }}
    .fbot {{ border-top: 1px solid rgba(255,255,255,0.08); padding-top: 24px; display: flex; justify-content: space-between; font-size: 12px; color: rgba(255,255,255,0.2) }}
    .cta {{ padding: 80px 56px; background: linear-gradient(135deg, var(--blue), var(--mint)); text-align: center; color: #fff }}
    .cta h2 {{ font-family: 'Noto Serif TC', serif; font-size: 30px; letter-spacing: 5px; margin-bottom: 15px }}
    .cta p {{ font-size: 15px; opacity: 0.9; margin-bottom: 30px }}
    .nav-cta {{ background: var(--dark); color: #fff; padding: 10px 28px; border-radius: 40px; text-decoration: none; font-size: 14px; letter-spacing: 2px; transition: all .3s }}
    .nav-cta:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(44,74,90,.3) }}
    @media(max-width:1000px) {{
      .header-section {{ flex-direction: column; text-align: center; gap: 30px; padding: 120px 24px 40px }}
      .main-grid {{ grid-template-columns: 1fr; gap: 50px; padding: 0 24px 80px }}
      .right-col {{ position: static }}
      .fg {{ grid-template-columns: 1fr; gap: 40px }}
      footer {{ padding: 60px 24px }}
    }}
    @media(max-width:768px) {{ .line-float span {{ display: none }} }}
  </style>
</head>
<body>

  <nav>
    <a href="index.html" class="logo">華昕<em>藝心</em></a>
    <ul class="nav-links">
      <li><a href="index.html">關於我們</a></li>
      <li><a href="services.html">服務項目</a></li>
      <li class="has-dropdown">
        <a href="team.html" class="active">專業團隊</a>
        <div class="dropdown-menu" id="navTherapistDropdown"></div>
      </li>
      <li><a href="news.html">最新消息</a></li>
      <li><a href="faq.html">常見問答</a></li>
      <li><a href="transportation.html">交通方式</a></li>
      <li><a href="resources/index.html">資源連結</a></li>
    </ul>
  </nav>

  <div class="header-section">
    <div class="photo-circle">{photo_html}</div>
    <div class="name-info">
      <h1>{h(name)} <em>{h(title)}</em></h1>
      <div class="license-no">{h(license_no)}</div>
    </div>
  </div>

  <div class="main-grid">
    <div class="left-col">
      {positions_block}
      {education_block}
      {experience_block}
      {certs_block}
      {articles_block}
      {links_block}
    </div>
    <div class="right-col">
      {philosophy_block}
      {specialties_block}
    </div>
  </div>

  <div class="page-nav">
    <div>{prev_link}</div>
    <div>{next_link}</div>
  </div>

  <section class="cta">
    <h2>找到適合您的陪伴了嗎？</h2>
    <p>如果您不確定哪位心理師最適合您的需求，歡迎與小助手聊聊，讓我們為您推薦。</p>
    <div class="cta-btns">
      <a href="https://forms.gle/ZJu7T7U1CWNZDshq8" class="nav-cta" style="padding: 14px 40px">立即預約諮商</a>
      <a href="https://lin.ee/nOmKPpP" class="btn-o-white">由我們為您推薦</a>
    </div>
  </section>

  <footer>
    <div class="fg">
      <div class="fb">
        <h3>華昕藝心心理諮商所</h3>
        <p>藝術 × 心理諮商的深度結合<br>陪你同行，在南港找到你的療癒空間<br>北市衛心字第XY01120039號</p>
        <div class="socs">
          <a href="https://lin.ee/nOmKPpP" class="soc"><svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></a>
          <a href="https://www.facebook.com/huasin.apcc" class="soc"><svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg></a>
          <a href="https://www.instagram.com/huasin.apcc/" class="soc"><svg viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg></a>
        </div>
      </div>
      <div class="fc">
        <h4>服務項目</h4>
        <ul>
          <li><a href="service-individual.html">個別諮商</a></li>
          <li><a href="service-couples.html">伴侶婚姻諮商</a></li>
          <li><a href="service-parenting.html">親子諮商</a></li>
          <li><a href="service-online.html">線上遠距諮商</a></li>
          <li><a href="service-group.html">團體諮商／工作坊</a></li>
          <li><a href="service-eap.html">企業合作方案</a></li>
        </ul>
      </div>
      <div class="fc">
        <h4>快速連結</h4>
        <ul>
          <li><a href="https://forms.gle/ZJu7T7U1CWNZDshq8">預約諮商</a></li>
          <li><a href="team.html">專業團隊</a></li>
          <li><a href="faq.html">常見問答</a></li>
          <li><a href="transportation.html">交通方式</a></li>
        </ul>
      </div>
    </div>
    <div class="fbot">
      <p>© 2025 華昕藝心心理諮商所 All rights reserved.</p>
      <p>02-6605-7103 ｜ huasin.apcc@gmail.com</p>
    </div>
  </footer>

  <a href="https://lin.ee/nOmKPpP" target="_blank" class="line-float">
    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
    <span>預約或了解更多？加入LINE由專人協助</span>
  </a>

  <script src="nav-dropdown.js"></script>
</body>
</html>'''


def generate_sitemap(therapist_ids):
    urls = []
    static_pages = [
        '', 'services.html', 'team.html', 'news.html', 'faq.html',
        'transportation.html', 'service-individual.html', 'service-couples.html',
        'service-parenting.html', 'service-online.html', 'service-group.html', 'service-eap.html',
    ]
    for page in static_pages:
        urls.append(f'  <url><loc>{BASE_URL}/{page}</loc><changefreq>monthly</changefreq></url>')
    for tid in therapist_ids:
        urls.append(f'  <url><loc>{BASE_URL}/therapist-{tid}.html</loc><changefreq>monthly</changefreq></url>')
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>'


import urllib.parse

def main():
    print('正在從 Google Sheets 拉取資料...')
    therapists = fetch_sheet(THERAPISTS_SHEET)
    articles = fetch_sheet(ARTICLES_SHEET)

    active = [t for t in therapists if str(t.get('active', '')).upper() == 'TRUE' and t.get('name')]
    active.sort(key=lambda t: float(t.get('sort_order') or t.get('id') or 9999))
    print(f'找到 {len(active)} 位心理師')

    generated_ids = []
    for t in active:
        try:
            tid = str(int(float(t['id'])))
        except Exception:
            tid = str(t.get('id', ''))

        html = render_therapist_page(t, active, articles)
        filename = f'therapist-{tid}.html'
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        generated_ids.append(tid)
        print(f'  ✓ {filename}  ({t["name"]} {t.get("title","")})')

    # Generate sitemap
    sitemap = generate_sitemap(generated_ids)
    sitemap_path = os.path.join(OUTPUT_DIR, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print(f'✓ sitemap.xml 已更新（{len(generated_ids)} 位心理師）')

    print('\n完成！請執行：')
    print('  git add therapist-*.html sitemap.xml')
    print('  git commit -m "更新心理師靜態頁面"')
    print('  git push')


if __name__ == '__main__':
    main()
