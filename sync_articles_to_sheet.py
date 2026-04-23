"""
sync_articles_to_sheet.py
將從 hua-sin.com 爬取的文章寫入 Google Sheet。

安裝：
    pip install gspread google-auth

Google 憑證設定：
  1. 前往 https://console.cloud.google.com/
  2. 新增專案 → 啟用 Google Sheets API 和 Google Drive API
  3. 建立「服務帳戶」→ 下載 JSON 金鑰，改名為 service_account.json 放在此資料夾
  4. 開啟 Google Sheet → 共用 → 把 service_account.json 裡的 client_email 加為「編輯者」

執行：
    python sync_articles_to_sheet.py
"""

import gspread
from google.oauth2.service_account import Credentials

# ── 設定區 ────────────────────────────────────────────────
SHEET_ID = "1o0di_U7q_NKiDuwkHEnUqlX2QQNxAeXR1TKpAJl0WAQ"
SHEET_TAB = "工作表1"           # 分頁名稱，如不同請修改
SERVICE_ACCOUNT_FILE = "service_account.json"
# ──────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 欄位順序需與 Sheet 標題列一致
# Id | title | author_id | category | image_url | summary | content | date | active | is_featured | hashtags

ARTICLES = [
    {
        "title": "1219北捷事件心理健康支持方案",
        "author_id": "",
        "category": "最新消息",
        "image_url": "",
        "summary": "提供每人 3 次心理諮商｜不限年齡、從寬認定｜由政府全額補助",
        "content": (
            "年底本來是回顧與整理的時刻，但近日的突發事件，讓很多人心裡多了一層不安。\n\n"
            "華昕藝心推出針對北捷暴力事件受影響民眾的心理支持計畫。\n"
            "此方案由政府全額補助，受影響人士可獲得每人3次免費心理諮商服務。\n\n"
            "申請資格採寬鬆認定標準，涵蓋所有年齡層。只要受事件影響——無論是親身經歷、"
            "目睹或因媒體報導而感到焦慮——民眾即可申請。\n\n"
            "服務形式為實體晤談，每次40分鐘，總療程不超過3個月，"
            "預約間隔須在7天至1個月間。\n\n"
            "心理諮商是照護受傷心靈的必要舉措，鼓勵民眾勿自責，"
            "支持資源將持續至2026年底。"
        ),
        "date": "12/24",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#1219北捷事件 #心理健康支持 #免費諮商 #華昕藝心",
    },
    {
        "title": "「遠離麻疹之亂，一起守護安心健康」",
        "author_id": "陳瑜慧 諮商心理師",
        "category": "心理衛教文章",
        "image_url": "https://static.wixstatic.com/media/71d48f_8a45b4f45f29418d8d9d51be2f0d5643~mv2.jpg",
        "summary": "",
        "content": (
            "最近新聞報導麻疹群聚疫情，許多人感到擔憂並出現過度焦慮。\n\n"
            "根據疾病管制署通函，自費MMR疫苗應優先提供高風險族群接種。"
            "台灣幼兒MMR接種率高，1981年前出生者多數已具抗體，大規模流行風險相對較低。\n\n"
            "心理調適建議：\n"
            "1. 定期參考官方資訊，避免過度搜尋網路\n"
            "2. 維持必要防疫習慣，無症狀時日常防護即可\n"
            "3. 保持規律作息、適度運動、與親友互動以舒緩壓力\n"
            "4. 強烈焦慮時尋求專業協助\n\n"
            "做好日常衛生與自我調適能維護身心健康，建議關注正確訊息共同守護安心。"
        ),
        "date": "2/10",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#文章",
    },
    {
        "title": "心理師為什麼不直接回答我的問題？",
        "author_id": "郭慧珍 藝術治療師/諮商心理師",
        "category": "心理衛教文章",
        "image_url": "https://static.wixstatic.com/media/71d48f_b84c4feb8cf74c22987b5f5caebc949d~mv2.jpg",
        "summary": "",
        "content": (
            "心理師不直接回答問題的四個主要原因：\n\n"
            "## 1. 心理師的有限性\n"
            "心理師需要充分理解個案及問題脈絡後才能提供解答，"
            "因此會提出更多澄清性問題。\n\n"
            "## 2. 避免主客異位\n"
            "涉及心理師私人資訊或立場的問題不會直接回答，"
            "因為諮商空間應以個案為主角。\n\n"
            "## 3. 維持你的主體性\n"
            "諮商是合作過程，心理師協助個案成為自己的主人，"
            "不強迫接受意見（危機或違法風險除外），透過對話讓個案自己找到答案。\n\n"
            "## 4. 促進你的成長\n"
            "在對話歷程中，個案會加深自我覺察，"
            "發展更敏銳的洞察力與多元解決問題能力。"
        ),
        "date": "2/21",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#心理諮商 #諮商心理師 #藝術治療 #心理成長 #心理諮商FAQ #諮商室的對話 #心理健康",
    },
    {
        "title": "如何分辨安全的心理成長課程？避免心理操控的陷阱",
        "author_id": "陳瑜慧 藝術治療師",
        "category": "心理衛教文章",
        "image_url": "https://static.wixstatic.com/media/71d48f_a2d0d41fddc34c829d532e82af9ea739~mv2.jpg",
        "summary": "",
        "content": (
            "有些心理成長課程可能潛藏操控風險。以下是四個警訊模式：\n\n"
            "1. 打擊參與者自我價值感\n"
            "2. 在團體中強迫揭露個人創傷\n"
            "3. 製造壓力讓人持續留在課程中\n"
            "4. 設計無止盡的付費升級機制\n\n"
            "## 安全的心理成長環境應該：\n"
            "尊重個人自主權，不會強迫參與；讓你在任何時候都可以說不。\n\n"
            "## 替代方案建議：\n"
            "- 一對一諮商（持照心理師）\n"
            "- 藝術治療\n"
            "- 正念練習\n"
            "- 實證心理學書籍"
        ),
        "date": "2/15",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#心理成長 #心靈課程風險 #心理諮商和LGAT不同 #情緒操控 #PUA #煤氣燈效應 #心靈課程 #LGAT #心理操縱 #高壓課程",
    },
    {
        "title": "🌸 花一點時間，為自己｜母親節永生花插花體驗課 🌸",
        "author_id": "",
        "category": "活動",
        "image_url": "https://static.wixstatic.com/media/71d48f_e41abe3ade9e4e2b99da03b6d8700eb8~mv2.jpg",
        "summary": "",
        "content": (
            "邀請忙碌的你，靜靜為自己插一束花，把日子過得柔軟一點。\n\n"
            "## 課程資訊\n"
            "- 講師：惟一老師（AFA美國花藝設計學院講師、NFD日本花藝設計師協會認證）\n"
            "- 場次：5月2日（五）、5月3日（六），下午 1:30–2:30\n"
            "- 人數：每場限 6–8 人\n"
            "- 費用：限時優惠 1,280 元（原價 1,680 元），含專業指導、高品質花材與包裝\n"
            "- 地點：台北市南港區研究院路一段99號2樓之103\n"
            "- 報名截止：4月28日\n\n"
            "## 聯絡資訊\n"
            "- 電話：02-66057103\n"
            "- Email：huasin.apcc@gmail.com\n"
            "- 報名連結：https://huasin.pse.is/class11405"
        ),
        "date": "4/21",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#花一點時間為自己 #母親節花藝課 #永生花手作 #永生花體驗 #花藝療癒 #給自己的溫柔時光 #為自己盛開一次 #日常的療癒儀式 #自我照顧練習 #慢慢生活 #華昕藝心 #藝心時光 #華昕活動 #南港",
    },
    {
        "title": "你的色彩旅程：從童年偏好到職場定位的蛻變之路(好評加開場)(已額滿）",
        "author_id": "劉浩維 諮商心理師/職涯諮詢師",
        "category": "活動",
        "image_url": "https://static.wixstatic.com/media/71d48f_d30ddaa4e50f4ca4850d851440767a32~mv2.jpg",
        "summary": "",
        "content": (
            "由華昕藝心心理諮商所與本色形象共同舉辦。\n\n"
            "## 活動資訊\n"
            "- 時間：2025年6月14日（六）13:00–16:00\n"
            "- 地點：台北市南港區研究院路一段99號2樓之103\n"
            "- 費用：600元（原價800元）\n"
            "- 報名截止：5月31日\n\n"
            "## 主題內容\n"
            "1. 個人色彩風格探索\n"
            "2. 色彩提升專業形象\n"
            "3. 個人品牌色彩指南建立\n\n"
            "## 講師\n"
            "- 劉浩維｜諮商心理師/華昕藝心心理諮商所副所長/職涯諮詢師\n"
            "- Emma｜本色形象負責人/造型師/JPCA高階色彩顧問\n"
            "- 熙熙｜JPCA認證色彩講師/高階顧問/22型風格定位"
        ),
        "date": "4/21",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#劉浩維諮商心理師 #色彩風格分析 #穿搭心理學 #專業形象打造 #藝心時光 #色彩心理學 #華昕藝心 #自我成長 #職場穿搭",
    },
    {
        "title": "「脆弱時，給自己一個愛的抱抱」",
        "author_id": "李育珊 諮商心理師",
        "category": "心理衛教文章",
        "image_url": "https://static.wixstatic.com/media/71d48f_5d004faae8844123827b4afe048eb413~mv2.jpg",
        "summary": "",
        "content": (
            "介紹蝴蝶擁抱法——一種簡單而有效的自我安撫技術。\n\n"
            "這項方法源自眼動減敏與歷程更新治療（EMDR），"
            "透過生理上的雙側刺激，讓我們得以自我安撫，降低不安與焦慮的反應。\n\n"
            "## 步驟\n"
            "1. 將雙手交叉置於肩膀處\n"
            "2. 閉眼或看向鼻尖\n"
            "3. 輪流輕拍左右肩膀，搭配深沉呼吸\n"
            "4. 持續直至感到平靜\n\n"
            "安慰與安全感並不是只能向外尋求，透過此方法可自我救援。\n\n"
            "如果有持續的憂鬱、焦慮等情緒，建議尋求心理師協助。"
        ),
        "date": "5/29",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#蝴蝶擁抱 #情緒自我照顧 #自我安撫 #心理健康 #心理諮商 #心理師陪你走一段路 #心理療癒小練習 #身心靈照顧 #給自己一個擁抱 #焦慮舒緩 #日常情緒照顧",
    },
    {
        "title": "114臺北市原住民心理健康支持補助方案",
        "author_id": "",
        "category": "最新消息",
        "image_url": "https://static.wixstatic.com/media/71d48f_9f46fe8a39e94f43a28bb8be92ef4d7f~mv2.jpg",
        "summary": "",
        "content": (
            "都市生活步調快、壓力大，對於來到台北的原住民朋友，可能帶來適應上的挑戰。\n\n"
            "## 支持領域\n"
            "- 都市適應\n"
            "- 文化認同與傳承\n"
            "- 家庭與人際壓力\n"
            "- 職場挑戰與偏見\n"
            "- 情緒與心理健康\n\n"
            "## 補助資格\n"
            "設籍臺北市連續四個月以上之原住民\n\n"
            "## 補助內容\n"
            "每人每年最多補助6次，每次最高補助新台幣1,600元（需自行給付諮商費用差額）\n\n"
            "## 預約方式\n"
            "填寫預約表單並加入官方Line，諮商當日需出示原住民身分證明\n\n"
            "## 聯絡資訊\n"
            "- 電話：02-66057103\n"
            "- 官方LINE：@008qpdbt\n"
            "- 地址：115台北市南港區研究院路一段99號2樓之103"
        ),
        "date": "3/10",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#心理健康 #原住民 #原住民心理健康 #臺北市原住民 #心理支持 #壓力調適 #情緒支持 #都市原住民 #職場挑戰 #文化認同 #心理諮商補助 #臺北市政府",
    },
    {
        "title": "助人者的療癒時光—社工／照服員心理支持方案—",
        "author_id": "",
        "category": "最新消息",
        "image_url": "https://static.wixstatic.com/media/71d48f_4b4e44fcccc247cbaa9ad8363b28f98c~mv2.jpg",
        "summary": "",
        "content": (
            "針對現職社會工作師／社工員／照顧服務員提供心理諮商支持方案。\n\n"
            "## 服務規則\n"
            "- 每人限6次\n"
            "- 每次費用：1,600元（50分鐘）\n"
            "- 超過次數按原價計費\n"
            "- 服務期限：至114年12月31日\n\n"
            "## 預約流程\n"
            "1. 填寫預約表單並勾選該方案\n"
            "2. 加入官方LINE：@008qpdbt\n"
            "3. 電話初談，預計3-5個工作天內安排心理師\n"
            "4. 須提供工作證明文件（名片、工作證或在職證明）\n\n"
            "注意：服務心理師視中心安排為主，恕無法指定心理師。"
        ),
        "date": "3/25",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#社工 #社工師 #社工員 #照顧服 #支持方案 #南港心理諮商所 #南港諮商 #南港心理",
    },
    {
        "title": "15-45歲青壯世代心理健康支持方案，4-6月新額度出來了即日起開放預約!!",
        "author_id": "",
        "category": "最新消息",
        "image_url": "https://static.wixstatic.com/media/71d48f_2c68a7718e3248b8916723bbe42da783~mv2.jpg",
        "summary": "",
        "content": (
            "本方案提供15至45歲青壯世代全額補助心理諮商，最多3次。\n\n"
            "## 方案詳情\n"
            "- 補助對象：15-45歲\n"
            "- 補助次數：最多3次\n"
            "- 費用：全額補助\n"
            "- 補助期限：即日起至114年12月31日\n\n"
            "## 申請方式\n"
            "填寫預約表單並加入官方LINE告知姓名。\n"
            "名額有限，採分批次安排，依申請順位分配。\n\n"
            "## 聯絡資訊\n"
            "- 電話：02-66057103\n"
            "- Email：huasin.apcc@gmail.com\n"
            "- LINE：@008qpdbt\n"
            "- 地址：台北市南港區研究院路一段99號2樓之103（南港展覽館5號出口步行5分鐘）"
        ),
        "date": "3/29",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#心理健康 #心理諮商 #免費心理諮商 #15到45歲 #青壯世代 #華昕藝心心理諮商所 #華昕藝心 #心理健康支持方案 #南港心理諮商 #南港展覽館 #汐止心理諮商 #中研院",
    },
    {
        "title": "📣家長親職講座｜注意力不足過動症（ADHD）",
        "author_id": "張芯華 臨床心理師",
        "category": "活動",
        "image_url": "https://static.wixstatic.com/media/71d48f_a3af2aa3293c4bfa87871c6193c896c4~mv2.png",
        "summary": "",
        "content": (
            "針對有ADHD學齡前或學齡期孩子的家長舉辦的親職講座。\n\n"
            "講師將協助家長認識注意力不足過動症的成因與行為心理機制，"
            "並傳授日常可行的陪伴技巧。\n\n"
            "## 活動詳情\n"
            "- 時間：9月21日（日）上午 10:00–11:00\n"
            "- 對象：ADHD學齡前或學齡期孩子之家長\n"
            "- 費用：每人300元\n"
            "- 人數：3–10人（未滿3人不開班）\n"
            "- 地點：華昕藝心心理諮商所團體室，台北市南港區研究院路一段99號2樓之103\n\n"
            "## 報名方式\n"
            "完成匯款後，加入官方LINE @008qpdbt 告知相關資訊\n"
            "截止日期：9月18日"
        ),
        "date": "9/7",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#ADHD #注意力不足過動症 #親職講座 #正向教養 #親子關係 #家長支持 #心理師陪你同行 #華昕藝心 #親子心語系列 #南港活動 #張芯華臨床心理師 #兒童藝術治療 #遊戲治療 #南港心理諮商所",
    },
    {
        "title": "2025 華昕藝心｜實習心理師公益諮商方案正式上線",
        "author_id": "",
        "category": "最新消息",
        "image_url": "https://static.wixstatic.com/media/71d48f_0b4e479141ab4ec0a0b9f2f860685a53~mv2.jpg",
        "summary": "",
        "content": (
            "華昕藝心推出實習心理師公益諮商方案，讓心理諮商成為一段能讓人安心啟程的旅程。\n\n"
            "## 服務對象\n"
            "12歲以上兒童、青少年與成人\n\n"
            "## 服務期間\n"
            "即日起至115年6月\n\n"
            "## 實習心理師\n"
            "詹雅婷（國立台北護理健康大學生死健康心理諮商系碩士班）\n\n"
            "## 預約方式\n"
            "加入LINE官方帳號（ID：@008qpdbt）並傳送訊息\n\n"
            "## 注意事項\n"
            "- 每次50分鐘\n"
            "- 須承諾至少6次諮商\n"
            "- 諮商過程全程錄音供督導使用"
        ),
        "date": "9/7",
        "active": "TRUE",
        "is_featured": "FALSE",
        "hashtags": "#華昕藝心 #心理諮商 #實習心理師 #南港心理諮商所 #華昕藝心心理諮商所 #實習生 #藝術治療 #南港展覽館 #研究院路",
    },
]


def get_sheet():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet(SHEET_TAB)


def existing_titles(sheet) -> set[str]:
    records = sheet.get_all_records()
    return {str(r.get("title", "")).strip() for r in records if r.get("title")}


def next_id(sheet) -> int:
    records = sheet.get_all_records()
    if not records:
        return 1
    ids = [int(r["Id"]) for r in records if str(r.get("Id", "")).strip().isdigit()]
    return max(ids) + 1 if ids else 1


def main():
    print("=== 連接 Google Sheet ===")
    sheet = get_sheet()
    done = existing_titles(sheet)
    print(f"Sheet 中已有 {len(done)} 篇文章")

    current_id = next_id(sheet)
    new_count = 0

    for art in ARTICLES:
        title = art["title"].strip()
        if title in done:
            print(f"  跳過（已存在）：{title[:45]}")
            continue

        row = [
            current_id,
            title,
            art["author_id"],
            art["category"],
            art["image_url"],
            art["summary"],
            art["content"],
            art["date"],
            art["active"],
            art["is_featured"],
            art["hashtags"],
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        print(f"  ✓ 已寫入 (Id={current_id})：{title[:45]}")
        current_id += 1
        new_count += 1

    print(f"\n=== 完成！新增 {new_count} 篇文章到 Sheet ===")


if __name__ == "__main__":
    main()
