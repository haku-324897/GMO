import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

ADDRESS_KEYWORDS = [
    "所在地", "住所", "本社", "Head Office", "Location", "Map", "company-info", "company-profile", "about-section", "access-info", "location-map", "address", "contact-info"
]

KEYWORDS = {
    "営業時間": ["営業時間", "受付時間", "営業日", "open", "business hours"],
    "郵便番号": ["〒", "郵便番号", "zip", "postal"],
    "所在地": ADDRESS_KEYWORDS,
    "定休日": ["定休日", "休業日", "休日", "closed", "休館日"],
    "アクセス": ["アクセス", "access", "交通", "最寄駅"],
    "駐車場": ["駐車場", "parking"],
    "電話番号": ["電話番号", "TEL", "tel.", "電話", "phone"],
    "電話受付時間": ["電話受付時間", "受付時間", "電話受付", "phone reception"],
    "FAX": ["FAX", "fax."],
    "免許番号": ["免許番号", "許可番号", "license", "registration"],
    "設立（西暦）": ["設立", "創業", "設立年月日", "創立", "established", "founded"]
}

ADDRESS_PATTERNS = [
    r"(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)[^\n]*?(市|区|町|村)[^\n]*?\d{1,4}[-－]\d{1,4}([-－]\d{1,4})?[^\n]*?(ビル|号室|F|階|B)?[^\n]*",
    r"[\u4e00-\u9fa5]{2,10}市[\u4e00-\u9fa5]{1,10}区[^\n]*?\d{1,4}[-－]\d{1,4}([-－]\d{1,4})?[^\n]*?(ビル|号室|F|階|B)?[^\n]*",
    r"[\u4e00-\u9fa5]{2,10}市[\u4e00-\u9fa5]{1,10}区[^\n]*?\d{1,4}番\d{1,4}号[^\n]*",
    r"[\u4e00-\u9fa5]{2,10}区[\u4e00-\u9fa5]{1,10}[^\n]*?\d{1,4}[-－]\d{1,4}([-－]\d{1,4})?[^\n]*?(ビル|号室|F|階|B)?[^\n]*",
    r"[\u4e00-\u9fa5]{2,10}区[\u4e00-\u9fa5]{1,10}[^\n]*?\d{1,4}番\d{1,4}号[^\n]*",
]

def extract_by_keywords(lines, keywords, value_pattern=None, after_line=0):
    for i, line in enumerate(lines):
        if any(k in line for k in keywords):
            for offset in range(after_line+1):
                idx = i + offset
                if idx < len(lines):
                    target = lines[idx]
                    if value_pattern:
                        m = re.search(value_pattern, target)
                        if m:
                            return m.group().strip()
                    else:
                        val = re.sub('|'.join(keywords), '', target).strip(' :：')
                        if val:
                            return val
    return ""

def get_company_info(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': url,
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = text.split("\n")
    except Exception as e:
        return {"エラー": f"取得できませんでした: {e}"}

    # 郵便番号
    zip_code = extract_by_keywords(lines, KEYWORDS["郵便番号"], r"〒?\d{3}-\d{4}", after_line=1)
    if not zip_code:
        zip_match = re.search(r"〒?\d{3}-\d{4}", text)
        zip_code = zip_match.group() if zip_match else ""

    # 所在地
    address = ""
    for i, line in enumerate(lines):
        if any(k in line for k in KEYWORDS["所在地"]):
            # 直後の行が郵便番号なら、その次の行を住所とする
            if i + 1 < len(lines) and re.match(r"^〒?\d{3}-\d{4}", lines[i+1].strip()):
                if i + 2 < len(lines):
                    address_candidate = lines[i+2].strip()
                    for pat in ADDRESS_PATTERNS:
                        addr_match = re.search(pat, address_candidate)
                        if addr_match:
                            address = addr_match.group().strip()
                            break
                if address:
                    break
            else:
                candidate = line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not any(k in next_line for k in KEYWORDS["所在地"]):
                        candidate += next_line
                if i + 2 < len(lines):
                    next2_line = lines[i + 2].strip()
                    if next2_line and not any(k in next2_line for k in KEYWORDS["所在地"]):
                        candidate += next2_line
                for pat in ADDRESS_PATTERNS:
                    addr_match = re.search(pat, candidate)
                    if addr_match:
                        address = addr_match.group().strip()
                        break
                if address:
                    break
    if not address:
        for pat in ADDRESS_PATTERNS:
            addr_match = re.search(pat, text)
            if addr_match:
                address = addr_match.group().strip()
                break

    # 電話番号
    tel = extract_by_keywords(lines, KEYWORDS["電話番号"], r"\d{2,4}-\d{2,4}-\d{3,4}", after_line=1)
    if not tel:
        tel_match = re.search(r"(tel\.|TEL|電話番号)[^\d]*(\d{2,4}-\d{2,4}-\d{3,4})", text, re.IGNORECASE)
        tel = tel_match.group(2) if tel_match else ""

    # FAX
    fax = extract_by_keywords(lines, KEYWORDS["FAX"], r"\d{2,4}-\d{2,4}-\d{3,4}", after_line=1)
    if not fax:
        fax_match = re.search(r"(fax\.|FAX)[^\d]*(\d{2,4}-\d{2,4}-\d{3,4})", text, re.IGNORECASE)
        fax = fax_match.group(2) if fax_match else ""

    # 営業時間
    time = extract_by_keywords(lines, KEYWORDS["営業時間"], r"\d{1,2}:\d{2}[～~\-]\d{1,2}:\d{2}", after_line=1)
    if not time:
        time_match = re.search(r"\d{1,2}:\d{2}[～~\-]\d{1,2}:\d{2}", text)
        time = time_match.group() if time_match else ""

    # 電話受付時間
    tel_time = extract_by_keywords(lines, KEYWORDS["電話受付時間"], r"\d{1,2}:\d{2}[～~\-]\d{1,2}:\d{2}", after_line=1)
    if not tel_time:
        tel_time = time  # fallback

    # 定休日
    holiday = extract_by_keywords(lines, KEYWORDS["定休日"], None, after_line=1)
    if not holiday:
        holiday_match = re.search(r"(GW|年末年始|夏季休業|定休日)[^\n]*", text)
        holiday = holiday_match.group() if holiday_match else ""

    # アクセス
    access = extract_by_keywords(lines, KEYWORDS["アクセス"], None, after_line=2)

    # 駐車場
    parking = extract_by_keywords(lines, KEYWORDS["駐車場"], None, after_line=2)

    # 免許番号
    license_num = extract_by_keywords(lines, KEYWORDS["免許番号"], r"\d{1,4}号", after_line=2)
    if not license_num:
        license_match = re.search(r"(免許番号|許可番号)[^\d]*(\d{1,4}号)", text)
        license_num = license_match.group(2) if license_match else ""

    # 設立（西暦）
    established = extract_by_keywords(lines, KEYWORDS["設立（西暦）"], r"\d{4}年", after_line=2)
    if not established:
        est_match = re.search(r"(設立|創業|創立)[^\d]*(\d{4})年", text)
        established = est_match.group(2) + "年" if est_match else ""

    info = {
        "URL": url,
        "営業時間": time,
        "郵便番号": zip_code,
        "所在地": address,
        "定休日": holiday,
        "アクセス": access,
        "駐車場": parking,
        "電話番号": tel,
        "電話受付時間": tel_time,
        "FAX": fax,
        "免許番号": license_num,
        "設立（西暦）": established
    }
    return info

def extract_address_from_table(soup):
    # 1. 本社・本店（本社所在地・本店所在地）を最優先
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(separator=" ", strip=True)
                val = re.sub(r"\[.*?\]|GoogleMAP|【.*?】", "", val)
                if any(k in key for k in ["本社", "本店", "本店所在地", "本社所在地"]):
                    matches = []
                    for pat in ADDRESS_PATTERNS:
                        matches += re.findall(pat, val)
                    if matches:
                        return matches[0][0] if isinstance(matches[0], tuple) else matches[0]
    # 2. 次に「所在地」「住所」など
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(separator=" ", strip=True)
                val = re.sub(r"\[.*?\]|GoogleMAP|【.*?】", "", val)
                if any(k in key for k in ["所在地", "住所"]):
                    matches = []
                    for pat in ADDRESS_PATTERNS:
                        matches += re.findall(pat, val)
                    if matches:
                        return matches[0][0] if isinstance(matches[0], tuple) else matches[0]
    # 3. テーブルで取れなければ、テキスト全体を行ごとに走査
    text = soup.get_text(separator="\n", strip=True)
    lines = text.split("\n")
    for line in lines:
        for pat in ADDRESS_PATTERNS:
            addr_match = re.search(pat, line)
            if addr_match:
                return addr_match.group().strip()
    # さらに「所在地」キーワード行の2～3行後まで連結してパターンマッチ
    for i, line in enumerate(lines):
        if any(k in line for k in ["所在地", "住所", "本社", "本店"]):
            candidate = ""
            for offset in range(1, 4):
                idx = i + offset
                if idx < len(lines):
                    candidate += lines[idx].strip()
            for pat in ADDRESS_PATTERNS:
                addr_match = re.search(pat, candidate)
                if addr_match:
                    return addr_match.group().strip()
    return ""

st.title("会社情報 自動抽出ツール（複数URL対応・会社概要ページ推奨）")
st.markdown(
    """
    <style>
    .block-container, .main, .css-18e3th9, .css-1d391kg {
        max-width: 100vw !important;
        width: 100vw !important;
        padding-left: 2vw !important;
        padding-right: 2vw !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

urls_text = st.text_area(
    "会社のWebサイトURLを改行区切りで入力してください（例: https://victory-gp.jp/）",
    height=200
)

if urls_text:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    results = []
    for url in urls:
        info = get_company_info(url)
        results.append(info)
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)
