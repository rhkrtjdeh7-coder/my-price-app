import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import math
import warnings
import re
import streamlit.components.v1 as components

warnings.filterwarnings("ignore")

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="자재 가격 예측 시스템")

# 2. 디자인 설정 (기존 레이아웃 및 폰트 고정)
st.markdown("""
    <style>
    .stApp { background-color: #F9F9F7; }
    
    html, body, [class*="css"], h1, h2, h3, h4, p, span, label {
        color: #000000 !important;
        font-family: 'Pretendard', sans-serif !important;
    }

    /* 상단 메뉴 UI */
    div[data-testid="stRadio"] label p {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #000000 !important;
    }

    .unified-card {
        background-color: #E7F3FE !important; 
        padding: 25px !important;
        border-radius: 12px !important;
        border-left: 8px solid #007BFF !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        margin-bottom: 35px !important;
        width: 100%;
    }

    .stImage > img {
        height: 450px !important;
        width: auto !important;
        margin: 0 auto;
        display: block;
        border-radius: 8px;
        object-fit: contain !important;
    }

    /* 노란색 테이블 공통 스타일 */
    .yellow-table {
        border-collapse: collapse;
        color: #000000 !important;
        text-align: center;
        width: 100%;
    }
    .yellow-table th, .yellow-table td {
        padding: 20px 45px;
        border: 1px solid #E6E0A4;
        white-space: nowrap;
        font-size: 20px !important; /* 글자 크기 고정 */
    }
    .yellow-table th { background-color: #FDF17C; font-weight: bold; }
    
    .news-link { color: #007BFF !important; text-decoration: none; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 3. 뉴스 로직 (한 단어 키워드 고정)
def get_exact_press(item):
    link = item.get('originallink', item.get('link', ''))
    press_dict = {'hankyung.com': '한국경제', 'mk.co.kr': '매일경제', 'yna.co.kr': '연합뉴스', 'chosun.com': '조선일보', 'joins.com': '중앙일보', 'donga.com': '동아일보', 'sedaily.com': '서울경제', 'mt.co.kr': '머니투데이', 'edaily.co.kr': '이데일리', 'fnnews.com': '파이낸셜뉴스'}
    for domain, name in press_dict.items():
        if domain in link: return name
    return "경제 전문지"

def extract_single_keyword(title):
    clean = re.sub(r'<[^>]+>', '', title)
    clean = re.sub(r'[^가-힣a-zA-Z\s]', '', clean)
    words = [w for w in clean.split() if len(w) >= 2]
    return f"#{words[0]}" if words else f"#{item}"

def get_realtime_news(query):
    client_id = "ln148XZ9IeyGlRln6t0e"; client_secret = "xoHOWw4BfT"
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=sim"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get('items', []) if res.status_code == 200 else []
    except: return []

# 4. 데이터 및 철근 Y축 설정 (건드리지 않음)
st.markdown("<div style='text-align:center; margin-bottom:10px;'><h2 style='color:#007BFF;'>🏗️ 자재 선택</h2></div>", unsafe_allow_html=True)
item = st.radio("", ["레미콘", "철근", "알루미늄판"], horizontal=True, index=1)

if item == "철근":
    prices = [1050000, 1030000, 1020000, 1000000, 980000, 960000, 950000, 930000, 980000, 950000, 920000, 890000, 850000, 820000, 780000, 750000, 740000, 730000, 720000, 710000, 700000, 810000, 830000, 850000]
    dates = ['24. 5.', '24. 6.', '24. 7.', '24. 8.', '24. 9.', '24. 10.', '24. 11.', '24. 12.', '25. 1.', '25. 2.', '25. 3.', '25. 4.', '25. 5.', '25. 6.', '25. 7.', '25. 8.', '25. 9.', '25. 10.', '25. 11.', '25. 12.', '26. 1.', '26. 2.', '26. 3.', '26. 4.(예측)']
    ai_summary = "철근 시장은 26. 1월 저점 이후 공급망 인상 여파로 최근 3개월간 반등세가 뚜렷합니다."
    img_path, kw, label_name = "이형철근.png", "철근 가격 시황", "철근가격"
    y_min, y_max = 600000, 1000000 # 철근 Y축 최대값 1,000,000 고정
elif item == "레미콘":
    # 레미콘 과거 데이터 대폭 추가
    prices = [80000, 81200, 82500, 83000, 84500, 86000, 88000, 89500, 90000, 91000, 92000, 93000, 94000, 95000]
    dates = ['24. 5.', '24. 7.', '24. 9.', '24. 11.', '25. 1.', '25. 3.', '25. 5.', '25. 7.', '25. 9.', '25. 11.', '26. 1.', '26. 2.', '26. 3.', '26. 4.(예측)']
    ai_summary = "레미콘 가격은 원자재 비용 상승과 건설 성수기 진입 여파로 우상향 흐름이 유지될 전망입니다."
    img_path, kw, label_name = "레미콘.png", "레미콘 가격", "레미콘가격"
    y_min, y_max = 0, 130000
elif item == "알루미늄판":
    # 알루미늄판 과거 데이터 대폭 추가
    prices = [5800, 5950, 6100, 6300, 6200, 6400, 6600, 6800, 6620, 6450, 7260, 7360, 7460]
    dates = ['24. 5.', '24. 7.', '24. 9.', '24. 11.', '25. 1.', '25. 3.', '25. 5.', '25. 7.', '25. 9.', '25. 11.', '26. 1.', '26. 2.', '26. 3.(예측)']
    ai_summary = "알루미늄판은 글로벌 공급망 불안정과 에너지 단가 상승으로 인해 높은 변동성이 예상됩니다."
    img_path, kw, label_name = "알루미늄판.png", "알루미늄판 가격", "알루미늄판가격"
    y_min, y_max = 0, 10000

df = pd.DataFrame({'날짜': dates, label_name: prices})

# 5. 상단 섹션
c1, c2 = st.columns([1, 1.5], gap="large")
with c1:
    st.markdown(f'<div class="unified-card"><h4>📋 {item} 실황 이미지</h4>', unsafe_allow_html=True)
    try: st.image(img_path)
    except: st.error("이미지 없음")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div class="unified-card"><h4>📈 {item} 가격 추이 및 AI 예측</h4>', unsafe_allow_html=True)
    fig = px.bar(df.tail(6), x='날짜', y=label_name, text=label_name)
    fig.update_traces(marker_color=['#B0C4DE']*5 + ['#FF8C00'], textposition='outside', 
                      texttemplate='%{text:,.0f}', textfont=dict(color='#000000', size=22))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title=dict(text="날짜", font=dict(size=22, color="#000000")), tickfont=dict(size=18, color="#000000")),
        yaxis=dict(title=dict(text="가격", font=dict(size=22, color="#000000")), range=[y_min, y_max], tickfont=dict(size=18, color="#000000")),
        margin=dict(t=50, b=50, l=60, r=40), height=450 
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 상세 데이터 현황 (테이블 스크롤)
st.markdown(f'<div class="unified-card"><h4>📊 {item} 상세 데이터 현황</h4>', unsafe_allow_html=True)

html_df = df.set_index('날짜').T
table_content = "".join([f"<th>{c}</th>" for c in html_df.columns])
rows_content = ""
for idx, row in html_df.iterrows():
    rows_content += f"<tr><td><b>{idx}</b></td>" + "".join([f"<td>{int(v):,}</td>" for v in row]) + "</tr>"

components.html(f"""
    <style>
    .scroll-outer-container {{ display: flex; align-items: center; gap: 10px; width: 100%; }}
    .table-scroll-wrapper {{ width: 100%; overflow-x: auto; background-color: #FFF9C4; border: 1px solid #E6E0A4; }}
    .nav-btn {{ background-color: #007BFF; color: white; border: none; border-radius: 50%; width: 55px; height: 55px; cursor: pointer; font-size: 28px; display: flex; align-items: center; justify-content: center; user-select: none; }}
    .yellow-table {{ min-width: 3500px; border-collapse: collapse; text-align: center; font-family: sans-serif; }}
    .yellow-table th, .yellow-table td {{ padding: 20px 45px; border: 1px solid #E6E0A4; white-space: nowrap; font-size: 20px; color: black; }}
    .yellow-table th {{ background-color: #FDF17C; font-weight: bold; }}
    </style>
    <div class="scroll-outer-container">
        <button class="nav-btn" onmousedown="startScroll(-1)" onmouseup="stopScroll()" onmouseleave="stopScroll()"> < </button>
        <div id="data-table-container" class="table-scroll-wrapper">
            <table class="yellow-table">
                <thead><tr><th>구분</th>{table_content}</tr></thead>
                <tbody>{rows_content}</tbody>
            </table>
        </div>
        <button class="nav-btn" onmousedown="startScroll(1)" onmouseup="stopScroll()" onmouseleave="stopScroll()"> > </button>
    </div>
    <script>
    var scrollInterval;
    function startScroll(direction) {{
        var container = document.getElementById('data-table-container');
        scrollInterval = setInterval(function() {{
            container.scrollLeft += direction * 25;
        }}, 30);
    }}
    function stopScroll() {{
        clearInterval(scrollInterval);
    }}
    </script>
""", height=220)
st.markdown('</div>', unsafe_allow_html=True)

# 7. 하단 뉴스 및 AI 시황 요약
c3, c4 = st.columns([1, 1.5], gap="large")
with c3:
    st.markdown(f'<div class="unified-card"><h4>🤖 AI 시황 요약</h4><p style="font-size: 20px; font-weight:600; color:#000000;">{ai_summary}</p></div>', unsafe_allow_html=True)

with c4:
    st.markdown('<div class="unified-card"><h4>📰 실시간 시장 뉴스 브리핑</h4>', unsafe_allow_html=True)
    news_list = get_realtime_news(kw)
    if news_list:
        news_html = "<div style='overflow-x:auto;'><table class='yellow-table' style='min-width: 100%; background-color:#FFF9C4;'><thead><tr><th style='width:220px;'>핵심 키워드</th><th>뉴스 요약</th><th style='width:220px;'>제공 기관</th></tr></thead><tbody>"
        for n in news_list:
            src = get_exact_press(n)
            keyword = extract_single_keyword(n['title'])
            news_html += f"<tr><td style='color:#007BFF; font-weight:bold;'>{keyword}</td><td style='text-align:left;'><a href=\"{n['link']}\" target='_blank' class='news-link'>{n['title'].replace('<b>','').replace('</b>','')}</a></td><td style='color:black; font-weight:bold;'>{src}</td></tr>"
        news_html += "</tbody></table></div>"
        st.markdown(news_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
