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
    r"(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)[^\n]*?(市|区|町|村)[^\n]*?((丁目)?\d{1,4}[-－]?\d{0,4}|\d{1,4}番地?\d{0,4}|[０-９]{1,4}丁目)?[^\n]*?(ビル|号室|F|階|B)?[^\n]*",
    r"[\u4e00-\u9fa5]{2,10}市[\u4e00-\u9fa5]{1,10}区[^\n]*?((丁目)?\d{1,4}[-－]?\d{0,4}|\d{1,4}番地?\d{0,4})[^\n]*?(ビル|号室|F|階|B)?[^\n]*",
    r"[\u4e00-\u9fa5]{2,10}区[\u4e00-\u9fa5]{1,10}[^\n]*?((丁目)?\d{1,4}[-－]?\d{0,4}|\d{1,4}番地?\d{0,4})[^\n]*?(ビル|号室|F|階|B)?[^\n]*",
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
    except Exception as e:
        return {"エラー": f"取得できませんでした: {e}"}

    # 表からのみ所在地を取得
    address = extract_address_from_table(soup)
    return {"URL": url, "所在地": address}

def extract_address_from_table(soup):
    # 1. <dt>所在地</dt> の直後の <dd> を優先
    for dt in soup.find_all("dt"):
        if "所在地" in dt.get_text(strip=True):
            dd = dt.find_next_sibling("dd")
            if dd:
                val = dd.get_text(separator=" ", strip=True)
                for pat in ADDRESS_PATTERNS:
                    addr_match = re.search(pat, val)
                    if addr_match:
                        # 連続した空白（半角・全角）を半角スペース1つにまとめる
                        address = addr_match.group().strip()
                        address = re.sub(r'[ \u3000]+', ' ', address)
                        return address
    # 2. 既存のテーブル抽出ロジック
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(separator=" ", strip=True)
                val = re.sub(r"\[.*?\]|GoogleMAP|【.*?】", "", val)
                if any(k in key for k in ["本社", "本店", "本店所在地", "本社所在地"]):
                    for pat in ADDRESS_PATTERNS:
                        addr_match = re.search(pat, val)
                        if addr_match:
                            # 連続した空白（半角・全角）を半角スペース1つにまとめる
                            address = addr_match.group().strip()
                            address = re.sub(r'[ \u3000]+', ' ', address)
                            return address
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(separator=" ", strip=True)
                val = re.sub(r"\[.*?\]|GoogleMAP|【.*?】", "", val)
                if any(k in key for k in ["所在地", "住所"]):
                    for pat in ADDRESS_PATTERNS:
                        addr_match = re.search(pat, val)
                        if addr_match:
                            # 連続した空白（半角・全角）を半角スペース1つにまとめる
                            address = addr_match.group().strip()
                            address = re.sub(r'[ \u3000]+', ' ', address)
                            return address
    # 3. テーブルやdl以外の「本社住所」「所在地」「住所」キーワードを含むテキストも探索
    keywords = ["本社住所", "所在地", "住所"]
    for tag in soup.find_all(text=True):
        for k in keywords:
            if k in tag:
                # 直後のテキストや兄弟要素も連結してみる
                candidate = tag
                next_sibling = tag.parent.find_next_sibling()
                if next_sibling:
                    candidate += " " + next_sibling.get_text(separator=" ", strip=True)
                candidate = candidate.replace('\n', ' ').replace('\r', ' ')
                for pat in ADDRESS_PATTERNS:
                    addr_match = re.search(pat, candidate)
                    if addr_match:
                        # 連続した空白（半角・全角）を半角スペース1つにまとめる
                        address = addr_match.group().strip()
                        address = re.sub(r'[ \u3000]+', ' ', address)
                        return address
    return ""

st.title("会社所在地 自動抽出ツール（複数URL対応・会社概要ページ推奨）")
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
