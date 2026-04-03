import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import math
import warningsimport streamlit as st
import pandas as pd
import plotly.express as px
import requests
import math
import warnings
import re
import streamlit.components.v1 as components
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# --- 인증키 설정 ---
EXIM_AUTH_KEY = "oka2HI3dbkqWZbblzHnDXYr4M53HhAL6" 
BOK_AUTH_KEY = "Y14PHW4YRQMCGRI92WAD"

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="AI 물가예측 프로그램")

# 2. 디자인 설정
st.markdown("""
    <style>
    .stApp { background-color: #F9F9F7; }
    html, body, [class*="css"], h1, h2, h3, h4, p, span, label {
        color: #000000 !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    div[data-testid="stRadio"] label p { 
        font-size: 24px !important; 
        font-weight: 800 !important; 
        color: #000000 !important; 
    }
    .unified-card {
        background-color: #E7F3FE !important; padding: 25px !important;
        border-radius: 12px !important; border-left: 8px solid #007BFF !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important; margin-bottom: 35px !important;
        width: 100%;
    }
    .yellow-table { border-collapse: collapse; text-align: center; width: 100%; }
    .yellow-table th, .yellow-table td { 
        padding: 20px 45px; border: 1px solid #E6E0A4; 
        font-size: 20px !important; color: #000000 !important; 
        white-space: nowrap !important;
    }
    .yellow-table th { background-color: #FDF17C; font-weight: bold; }
    .news-link { color: #007BFF !important; text-decoration: none; font-weight: 600; white-space: nowrap !important; }
    
    div[data-testid="stStatusWidget"] {
        display: flex; justify-content: center; align-items: center;
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 9999;
    }
    div[data-testid="stStatusWidget"] div { font-size: 28px !important; font-weight: 800 !important; color: #007BFF !important; }

    .footer {
        text-align: center; padding: 20px; font-size: 14px; color: #666666 !important;
        border-top: 1px solid #ddd; margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. API 로직
def get_exchange_rate(authkey):
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    def fetch_rate(date):
        url = f"https://www.koreaexim.go.kr/site/program/financial/exchangeJSON?authkey={authkey}&searchdate={date}&data=AP01"
        try:
            res = requests.get(url, verify=False, timeout=5)
            if res.status_code == 200:
                for item in res.json():
                    if item['cur_unit'] == 'USD': return item['deal_bas_r']
            return None
        except: return None
    curr = fetch_rate(today)
    prev = fetch_rate(yesterday)
    if curr:
        try:
            c_val = float(curr.replace(',', ''))
            p_val = float(prev.replace(',', '')) if prev else c_val
            diff = c_val - p_val
            sign = "▲" if diff > 0 else "▼" if diff < 0 else "-"
            return f"{curr}원 ({sign}{abs(diff):.1f})"
        except: return f"{curr}원"
    return "연결 대기"

def get_bok_base_rate(authkey):
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{authkey}/json/kr/1/2/722Y001/D/20260101/20261231/0101000/"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            rows = res.json()['StatisticSearch']['row']
            curr = float(rows[0]['DATA_VALUE'])
            prev = float(rows[1]['DATA_VALUE']) if len(rows) > 1 else curr
            diff = curr - prev
            sign = "▲" if diff > 0 else "▼" if diff < 0 else "-"
            return f"{curr}% ({sign}{abs(diff):.2f})"
        return "조회 대기"
    except: return "확인 불가"

def get_realtime_news(query):
    client_id = "ln148XZ9IeyGlRln6t0e"
    client_secret = "xoHOWw4BfT"
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=sim"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get('items', []) if res.status_code == 200 else []
    except: return []

def get_exact_press(item_obj):
    link = item_obj.get('originallink', item_obj.get('link', ''))
    press_dict = {'hankyung.com': '한국경제', 'mk.co.kr': '매일경제', 'yna.co.kr': '연합뉴스', 'chosun.com': '조선일보', 'joins.com': '중앙일보', 'donga.com': '동아일보'}
    for domain, name in press_dict.items():
        if domain in link: return name
    return "경제신문"

# --- 화면 실행 ---
with st.spinner('실시간 경제 지표 및 자재 데이터를 분석 중입니다...'):
    usd_rate = get_exchange_rate(EXIM_AUTH_KEY)
    bok_rate = get_bok_base_rate(BOK_AUTH_KEY)

st.markdown(f"<div style='text-align:right;'><span style='color:#007BFF; font-weight:bold;'>💱 실시간 환율: {usd_rate} | 🏦 한국은행 기준금리: {bok_rate}</span></div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#007BFF;'>🏗️ AI 물가예측 프로그램</h2>", unsafe_allow_html=True)

item_choice = st.radio("", ["레미콘", "철근", "알루미늄판"], horizontal=True, index=1)

if item_choice == "철근":
    prices = [880000, 880000, 870000, 870000, 880000, 880000, 900000, 895000, 870000, 850000, 840000, 830000, 820000, 840000, 850000, 820000, 820000, 810000, 790000, 800000, 780000, 770000, 800000, 815000, 815000, 855000]
    dates = ['24.04', '24.05', '24.06', '24.07', '24.08', '24.09', '24.10', '24.11', '24.12', '25.01', '25.02', '25.03', '25.04', '25.05', '25.06', '25.07', '25.08', '25.09', '25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
    ai_summary = "공급망 이슈 및 기준금리 변동 기조를 반영할 때, 26년 상반기 철근 가격은 반등 추세가 지속될 것으로 예측됩니다."
    img_path, kw, label_name = "이형철근.png", "철근 가격", "철근가격"
    y_min, y_max = 600000, 1000000
elif item_choice == "레미콘":
    prices = [80000, 82000, 84000, 86000, 88000, 90000, 92000, 95000]
    dates = ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
    ai_summary = "시멘트 원가 상승과 유류비 변동 추이를 분석한 결과, 레미콘 가격은 완만한 우상향 곡선을 그릴 것으로 전망됩니다."
    img_path, kw, label_name = "레미콘.png", "레미콘 시황", "레미콘가격"
    y_min, y_max = 0, 130000
else:
    prices = [6100, 6300, 6400, 6600, 6800, 7260, 7460, 7600]
    dates = ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
    ai_summary = "LME 재고 상황과 글로벌 공급망 리스크를 반영하여, 알루미늄판 가격의 단기적 변동성이 높을 것으로 예측됩니다."
    img_path, kw, label_name = "알루미늄판.png", "알루미늄판 시황", "알루미늄가격"
    y_min, y_max = 0, 10000

df = pd.DataFrame({'날짜': dates, '가격': prices})

c1, c2 = st.columns([1, 1.5], gap="large")
with c1:
    st.markdown(f'<div class="unified-card"><h4>📋 {item_choice} 실황 이미지</h4>', unsafe_allow_html=True)
    try: st.image(img_path)
    except: st.error("이미지 없음")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div class="unified-card"><h4>📈 {item_choice} 최근 6개월 가격 추이</h4>', unsafe_allow_html=True)
    fig = px.bar(df.tail(6), x='날짜', y='가격', text='가격')
    fig.update_traces(
        marker_color=['#B0C4DE']*5 + ['#FF8C00'], 
        texttemplate='%{text:,.0f}', 
        textfont=dict(size=22, color='#000000'),
        textposition='outside'
    )
    # y축 제목 겹침 해결을 위해 왼쪽 여백(l=100) 및 standoff 추가
    fig.update_layout(
        yaxis=dict(range=[y_min, y_max], tickfont=dict(size=18, color='#000000'), title=dict(font=dict(color='#000000'), text="가격", standoff=20)),
        xaxis=dict(type='category', tickfont=dict(size=18, color='#000000'), title=dict(font=dict(color='#000000'), text="날짜")),
        margin=dict(t=50, b=50, l=100, r=20), height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        bargap=0.4
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f'<div class="unified-card"><h4>📊 {item_choice} 상세 데이터 현황</h4>', unsafe_allow_html=True)
html_df = df.set_index('날짜').T
t_th = "".join([f"<th>{c}</th>" for c in html_df.columns])
t_td = "".join([f"<tr><td><b>{idx}</b></td>" + "".join([f"<td>{int(v) if isinstance(v, (int, float)) else v:,}</td>" for v in row]) + "</tr>" for idx, row in html_df.iterrows()])

# 데이터 로딩 시 맨 오른쪽(최신 금액)이 보이도록 scrollLeft 설정 추가
components.html(f"""
    <style>
    .scroll-container {{ display: flex; align-items: center; gap: 10px; }}
    .table-wrapper {{ width: 100%; overflow-x: auto; background-color: #FFF9C4; border: 1px solid #E6E0A4; scroll-behavior: smooth; }}
    .nav-btn {{ background-color: #007BFF; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; cursor: pointer; font-size: 24px; font-weight: bold; }}
    .yellow-table {{ min-width: 3500px; border-collapse: collapse; text-align: center; font-family: sans-serif; }}
    .yellow-table th, .yellow-table td {{ padding: 15px 30px; border: 1px solid #E6E0A4; font-size: 18px; color: black; }}
    .yellow-table th {{ background-color: #FDF17C; }}
    .table-wrapper::-webkit-scrollbar {{ height: 14px; display: block !important; }}
    .table-wrapper::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 10px; }}
    .table-wrapper::-webkit-scrollbar-thumb {{ background: #888; border-radius: 10px; }}
    </style>
    <div class="scroll-container">
        <button class="nav-btn" onmousedown="scrollT(-40)" onmouseup="stopS()" onmouseleave="stopS()"> < </button>
        <div id="scroll-box" class="table-wrapper">
            <table class="yellow-table">
                <thead><tr><th>구분</th>{t_th}</tr></thead>
                <tbody>{t_td}</tbody>
            </table>
        </div>
        <button class="nav-btn" onmousedown="scrollT(40)" onmouseup="stopS()" onmouseleave="stopS()"> > </button>
    </div>
    <script>
    var timer;
    var container = document.getElementById('scroll-box');
    
    // 페이지 로드 시 맨 오른쪽으로 자동 스크롤
    setTimeout(function() {{
        container.scrollLeft = container.scrollWidth;
    }}, 100);

    function scrollT(speed) {{ timer = setInterval(function(){{ container.scrollLeft += speed; }}, 20); }}
    function stopS() {{ clearInterval(timer); }}
    </script>
""", height=240)
st.markdown('</div>', unsafe_allow_html=True)

c3, c4 = st.columns([1, 1.5], gap="large")
with c3:
    st.markdown(f'<div class="unified-card"><h4>🤖 AI 시황 및 통계 분석</h4><p style="font-size:19px;"><b>분석 의견:</b> {ai_summary}</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="unified-card"><h4>📰 실시간 시장 뉴스 브리핑</h4>', unsafe_allow_html=True)
    news_list = get_realtime_news(item_choice)
    if news_list:
        n_html = "<table class='yellow-table' style='font-size:16px;'><thead><tr><th style='width:150px;'>핵심 단어</th><th>뉴스 요약</th><th style='width:150px;'>언론사</th></tr></thead><tbody>"
        for n in news_list:
            clean_t = n['title'].replace('<b>','').replace('</b>','')
            words = clean_t.split()
            keyword = words[0] if words else "뉴스"
            press = get_exact_press(n)
            n_html += f"<tr><td style='font-weight:bold; color:#007BFF; white-space:nowrap;'>#{keyword[:4]}</td><td style='text-align:left; white-space:nowrap;'><a href='{n['link']}' class='news-link' target='_blank'>{clean_t}</a></td><td style='font-weight:bold; white-space:nowrap;'>{press}</td></tr>"
        st.markdown(n_html + "</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="footer">
        <b>Data Sources & API Provided by:</b><br>
        환율 정보: 한국수출입은행 (Korea Exim Bank) | 
        경제 지표: 한국은행 경제통계시스템 (ECOS) | 
        시장 뉴스: 네이버 뉴스 검색 API (Naver Open API)
    </div>
""", unsafe_allow_html=True)
import re
import streamlit.components.v1 as components
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# --- 인증키 설정 ---
EXIM_AUTH_KEY = "oka2HI3dbkqWZbblzHnDXYr4M53HhAL6" 
BOK_AUTH_KEY = "Y14PHW4YRQMCGRI92WAD"

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="AI 물가예측 프로그램")

# 2. 디자인 설정
st.markdown("""
    <style>
    .stApp { background-color: #F9F9F7; }
    html, body, [class*="css"], h1, h2, h3, h4, p, span, label {
        color: #000000 !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    div[data-testid="stRadio"] label p { 
        font-size: 24px !important; 
        font-weight: 800 !important; 
        color: #000000 !important; 
    }
    .unified-card {
        background-color: #E7F3FE !important; padding: 25px !important;
        border-radius: 12px !important; border-left: 8px solid #007BFF !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important; margin-bottom: 35px !important;
        width: 100%;
    }
    .yellow-table { border-collapse: collapse; text-align: center; width: 100%; }
    .yellow-table th, .yellow-table td { 
        padding: 20px 45px; border: 1px solid #E6E0A4; 
        font-size: 20px !important; color: #000000 !important; 
        white-space: nowrap !important;
    }
    .yellow-table th { background-color: #FDF17C; font-weight: bold; }
    .news-link { color: #007BFF !important; text-decoration: none; font-weight: 600; white-space: nowrap !important; }
    
    /* 로딩 메시지 중앙 정렬 및 크기 확대 */
    div[data-testid="stStatusWidget"] {
        display: flex;
        justify-content: center;
        align-items: center;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999;
    }
    div[data-testid="stStatusWidget"] div {
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #007BFF !important;
    }

    .footer {
        text-align: center;
        padding: 20px;
        font-size: 14px;
        color: #666666 !important;
        border-top: 1px solid #ddd;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. API 로직
def get_exchange_rate(authkey):
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    def fetch_rate(date):
        url = f"https://www.koreaexim.go.kr/site/program/financial/exchangeJSON?authkey={authkey}&searchdate={date}&data=AP01"
        try:
            res = requests.get(url, verify=False, timeout=5)
            if res.status_code == 200:
                for item in res.json():
                    if item['cur_unit'] == 'USD': return item['deal_bas_r']
            return None
        except: return None
    curr = fetch_rate(today)
    prev = fetch_rate(yesterday)
    if curr:
        try:
            c_val = float(curr.replace(',', ''))
            p_val = float(prev.replace(',', '')) if prev else c_val
            diff = c_val - p_val
            sign = "▲" if diff > 0 else "▼" if diff < 0 else "-"
            return f"{curr}원 ({sign}{abs(diff):.1f})"
        except: return f"{curr}원"
    return "연결 대기"

def get_bok_base_rate(authkey):
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{authkey}/json/kr/1/2/722Y001/D/20260101/20261231/0101000/"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            rows = res.json()['StatisticSearch']['row']
            curr = float(rows[0]['DATA_VALUE'])
            prev = float(rows[1]['DATA_VALUE']) if len(rows) > 1 else curr
            diff = curr - prev
            sign = "▲" if diff > 0 else "▼" if diff < 0 else "-"
            return f"{curr}% ({sign}{abs(diff):.2f})"
        return "조회 대기"
    except: return "확인 불가"

def get_realtime_news(query):
    client_id = "ln148XZ9IeyGlRln6t0e"; client_secret = "xoHOWw4BT"
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=sim"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": "xoHOWw4BfT"}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get('items', []) if res.status_code == 200 else []
    except: return []

def get_exact_press(item_obj):
    link = item_obj.get('originallink', item_obj.get('link', ''))
    press_dict = {'hankyung.com': '한국경제', 'mk.co.kr': '매일경제', 'yna.co.kr': '연합뉴스', 'chosun.com': '조선일보', 'joins.com': '중앙일보', 'donga.com': '동아일보'}
    for domain, name in press_dict.items():
        if domain in link: return name
    return "경제신문"

# --- 화면 실행 ---
with st.spinner('실시간 경제 지표 및 자재 데이터를 분석 중입니다...'):
    usd_rate = get_exchange_rate(EXIM_AUTH_KEY)
    bok_rate = get_bok_base_rate(BOK_AUTH_KEY)

st.markdown(f"<div style='text-align:right;'><span style='color:#007BFF; font-weight:bold;'>💱 실시간 환율: {usd_rate} | 🏦 한국은행 기준금리: {bok_rate}</span></div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#007BFF;'>🏗️ AI 물가예측 프로그램</h2>", unsafe_allow_html=True)

item_choice = st.radio("", ["레미콘", "철근", "알루미늄판"], horizontal=True, index=1)

if item_choice == "철근":
    prices = [880000, 880000, 870000, 870000, 880000, 880000, 900000, 895000, 870000, 850000, 840000, 830000, 820000, 840000, 850000, 820000, 820000, 810000, 790000, 800000, 780000, 770000, 800000, 815000, 815000, 855000]
    dates = ['24.04', '24.05', '24.06', '24.07', '24.08', '24.09', '24.10', '24.11', '24.12', '25.01', '25.02', '25.03', '25.04', '25.05', '25.06', '25.07', '25.08', '25.09', '25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
    ai_summary = "공급망 이슈 및 기준금리 변동 기조를 반영할 때, 26년 상반기 철근 가격은 반등 추세가 지속될 것으로 예측됩니다."
    img_path, kw, label_name = "이형철근.png", "철근 가격", "철근가격"
    y_min, y_max = 600000, 1000000
elif item_choice == "레미콘":
    prices = [80000, 82000, 84000, 86000, 88000, 90000, 92000, 95000]
    dates = ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
    ai_summary = "시멘트 원가 상승과 유류비 변동 추이를 분석한 결과, 레미콘 가격은 완만한 우상향 곡선을 그릴 것으로 전망됩니다."
    img_path, kw, label_name = "레미콘.png", "레미콘 시황", "레미콘가격"
    y_min, y_max = 0, 130000
else:
    prices = [6100, 6300, 6400, 6600, 6800, 7260, 7460, 7600]
    dates = ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
    ai_summary = "LME 재고 상황과 글로벌 공급망 리스크를 반영하여, 알루미늄판 가격의 단기적 변동성이 높을 것으로 예측됩니다."
    img_path, kw, label_name = "알루미늄판.png", "알루미늄판 시황", "알루미늄가격"
    y_min, y_max = 0, 10000

# 데이터프레임 생성 및 그래프용 데이터 추출
df = pd.DataFrame({'날짜': dates, '가격': prices})
df_tail = df.tail(6).copy()

c1, c2 = st.columns([1, 1.5], gap="large")
with c1:
    st.markdown(f'<div class="unified-card"><h4>📋 {item_choice} 실황 이미지</h4>', unsafe_allow_html=True)
    try: st.image(img_path)
    except: st.error("이미지 없음")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div class="unified-card"><h4>📈 {item_choice} 최근 6개월 가격 추이</h4>', unsafe_allow_html=True)
    # 막대그래프 강제 복구 로직
    fig = px.bar(df_tail, x='날짜', y='가격', text='가격')
    fig.update_traces(
        marker_color=['#B0C4DE']*5 + ['#FF8C00'], 
        texttemplate='%{text:,.0f}', 
        textfont=dict(size=22, color='#000000'),
        textposition='outside'
    )
    fig.update_layout(
        yaxis=dict(range=[y_min, y_max], tickfont=dict(size=18, color='#000000'), title=dict(font=dict(color='#000000'), text="가격")),
        xaxis=dict(type='category', tickfont=dict(size=18, color='#000000'), title=dict(font=dict(color='#000000'), text="날짜")),
        margin=dict(t=50, b=50, l=10, r=10), height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        bargap=0.4
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f'<div class="unified-card"><h4>📊 {item_choice} 상세 데이터 현황</h4>', unsafe_allow_html=True)
html_df = df.set_index('날짜').T
t_th = "".join([f"<th>{c}</th>" for c in html_df.columns])
t_td = "".join([f"<tr><td><b>{idx}</b></td>" + "".join([f"<td>{int(v) if isinstance(v, (int, float)) else v:,}</td>" for v in row]) + "</tr>" for idx, row in html_df.iterrows()])

components.html(f"""
    <style>
    .scroll-container {{ display: flex; align-items: center; gap: 10px; }}
    .table-wrapper {{ width: 100%; overflow-x: auto; background-color: #FFF9C4; border: 1px solid #E6E0A4; }}
    .nav-btn {{ background-color: #007BFF; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; cursor: pointer; font-size: 24px; font-weight: bold; }}
    .yellow-table {{ min-width: 3500px; border-collapse: collapse; text-align: center; font-family: sans-serif; }}
    .yellow-table th, .yellow-table td {{ padding: 15px 30px; border: 1px solid #E6E0A4; font-size: 18px; color: black; }}
    .yellow-table th {{ background-color: #FDF17C; }}
    .table-wrapper::-webkit-scrollbar {{ height: 14px; display: block !important; }}
    .table-wrapper::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 10px; }}
    .table-wrapper::-webkit-scrollbar-thumb {{ background: #888; border-radius: 10px; }}
    </style>
    <div class="scroll-container">
        <button class="nav-btn" onmousedown="scrollT(-40)" onmouseup="stopS()" onmouseleave="stopS()"> < </button>
        <div id="scroll-box" class="table-wrapper">
            <table class="yellow-table">
                <thead><tr><th>구분</th>{t_th}</tr></thead>
                <tbody>{t_td}</tbody>
            </table>
        </div>
        <button class="nav-btn" onmousedown="scrollT(40)" onmouseup="stopS()" onmouseleave="stopS()"> > </button>
    </div>
    <script>
    var timer;
    function scrollT(speed) {{ timer = setInterval(function(){{ document.getElementById('scroll-box').scrollLeft += speed; }}, 20); }}
    function stopS() {{ clearInterval(timer); }}
    </script>
""", height=240)
st.markdown('</div>', unsafe_allow_html=True)

c3, c4 = st.columns([1, 1.5], gap="large")
with c3:
    st.markdown(f'<div class="unified-card"><h4>🤖 AI 시황 및 통계 분석</h4><p style="font-size:19px;"><b>분석 의견:</b> {ai_summary}</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="unified-card"><h4>📰 실시간 시장 뉴스 브리핑</h4>', unsafe_allow_html=True)
    news_list = get_realtime_news(item_choice)
    if news_list:
        n_html = "<table class='yellow-table' style='font-size:16px;'><thead><tr><th style='width:150px;'>핵심 단어</th><th>뉴스 요약</th><th style='width:150px;'>언론사</th></tr></thead><tbody>"
        for n in news_list:
            clean_t = n['title'].replace('<b>','').replace('</b>','')
            words = clean_t.split()
            keyword = words[0] if words else "뉴스"
            press = get_exact_press(n)
            n_html += f"<tr><td style='font-weight:bold; color:#007BFF; white-space:nowrap;'>#{keyword[:4]}</td><td style='text-align:left; white-space:nowrap;'><a href='{n['link']}' class='news-link' target='_blank'>{clean_t}</a></td><td style='font-weight:bold; white-space:nowrap;'>{press}</td></tr>"
        st.markdown(n_html + "</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="footer">
        <b>Data Sources & API Provided by:</b><br>
        환율 정보: 한국수출입은행 (Korea Exim Bank) | 
        경제 지표: 한국은행 경제통계시스템 (ECOS) | 
        시장 뉴스: 네이버 뉴스 검색 API (Naver Open API)
    </div>
""", unsafe_allow_html=True)
