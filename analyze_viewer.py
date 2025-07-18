#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
サイト分析結果ビューアー
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path

def load_analysis_data():
    """分析データを読み込み"""
    try:
        with open('site_analysis.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("site_analysis.json ファイルが見つかりません。先に analyze_sites.py を実行してください。")
        return []

def main():
    st.title("不動産会社サイト分析結果ビューアー")
    
    data = load_analysis_data()
    if not data:
        return
    
    # 基本統計
    st.header("📊 基本統計")
    total_sites = len(data)
    successful_sites = len([d for d in data if "error" not in d])
    error_sites = total_sites - successful_sites
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総サイト数", total_sites)
    with col2:
        st.metric("成功", successful_sites)
    with col3:
        st.metric("エラー", error_sites)
    
    # キーワード出現頻度
    st.header("🔍 キーワード出現頻度")
    keyword_stats = {}
    for result in data:
        if "error" not in result and "keywords_found" in result:
            for category in result["keywords_found"]:
                keyword_stats[category] = keyword_stats.get(category, 0) + 1
    
    if keyword_stats:
        keyword_df = pd.DataFrame([
            {"キーワード": k, "出現回数": v, "出現率": f"{v/successful_sites*100:.1f}%"}
            for k, v in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(keyword_df, use_container_width=True)
    
    # サイト詳細
    st.header("🏢 サイト詳細")
    
    # 成功したサイトのみ表示
    successful_data = [d for d in data if "error" not in d]
    
    for i, site in enumerate(successful_data):
        with st.expander(f"{i+1}. {site['title']} ({site['url']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**基本情報**")
                st.write(f"タイトル: {site['title']}")
                st.write(f"テーブル数: {len(site['tables'])}")
                st.write(f"dl要素数: {len(site['dl_elements'])}")
                
                if site['keywords_found']:
                    st.write("**見つかったキーワード**")
                    for category, words in site['keywords_found'].items():
                        st.write(f"- {category}: {', '.join(words)}")
            
            with col2:
                if site['text_samples']:
                    st.write("**住所サンプル**")
                    for sample in site['text_samples'][:2]:
                        st.write(f"- {sample}")
            
            # テーブル構造の表示
            if site['tables']:
                st.write("**テーブル構造**")
                for j, table in enumerate(site['tables']):
                    with st.expander(f"テーブル {j+1}"):
                        table_df = pd.DataFrame(table)
                        st.dataframe(table_df, use_container_width=True)
            
            # dl構造の表示
            if site['dl_elements']:
                st.write("**dl構造**")
                for j, dl in enumerate(site['dl_elements']):
                    with st.expander(f"dl要素 {j+1}"):
                        dl_df = pd.DataFrame(dl)
                        st.dataframe(dl_df, use_container_width=True)
    
    # エラーサイト
    if error_sites > 0:
        st.header("❌ エラーサイト")
        error_data = [d for d in data if "error" in d]
        for site in error_data:
            st.write(f"- {site['url']}: {site['error']}")
    
    # パターン分析
    st.header("🎯 パターン分析")
    
    # テーブル構造のパターン
    table_patterns = {}
    for site in successful_data:
        for table in site['tables']:
            for row in table:
                key = row['key']
                table_patterns[key] = table_patterns.get(key, 0) + 1
    
    if table_patterns:
        st.write("**テーブルでよく使われるキー**")
        pattern_df = pd.DataFrame([
            {"キー": k, "出現回数": v}
            for k, v in sorted(table_patterns.items(), key=lambda x: x[1], reverse=True)[:20]
        ])
        st.dataframe(pattern_df, use_container_width=True)
    
    # dl構造のパターン
    dl_patterns = {}
    for site in successful_data:
        for dl in site['dl_elements']:
            for row in dl:
                key = row['key']
                dl_patterns[key] = dl_patterns.get(key, 0) + 1
    
    if dl_patterns:
        st.write("**dl要素でよく使われるキー**")
        dl_pattern_df = pd.DataFrame([
            {"キー": k, "出現回数": v}
            for k, v in sorted(dl_patterns.items(), key=lambda x: x[1], reverse=True)[:20]
        ])
        st.dataframe(dl_pattern_df, use_container_width=True)

if __name__ == "__main__":
    main() 