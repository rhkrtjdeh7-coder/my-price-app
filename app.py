AI 물가예측 프로그램 최종 통합 코드
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import math
import warnings
import re
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

warnings.filterwarnings("ignore")

--- 인증키 설정 ---
EXIM_AUTH_KEY = "oka2HI3dbkqWZbblzHnDXYr4M53HhAL6"
CUSTOMS_AUTH_KEY = "e9d7f51fb8b79a747bb7996f6c4110b3103b747df6a5c9496c2a67374ab08e72"
BOK_AUTH_KEY = "Y14PHW4YRQMCGRI92WAD"

1. 페이지 설정
st.set_page_config(layout="wide", page_title="AI 물가예측 프로그램")

2. 디자인 설정
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
}
.yellow-table { border-collapse: collapse; text-align: center; width: 100%; }
.yellow-table th, .yellow-table td {
padding: 20px 45px; border: 1px solid #E6E0A4;
font-size: 20px !important; color: #000000 !important;
}
.yellow-table th { background-color: #FDF17C; font-weight: bold; }
.news-link { color: #007BFF !important; text-decoration: none; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

3. API 로직
def get_exchange_rate(authkey):
today = datetime.now().strftime('%Y%m%d')
url = f"https://www.koreaexim.go.kr/site/program/financial/exchangeJSON?authkey={authkey}&searchdate={today}&data=AP01"
try:
res = requests.get(url, verify=False, timeout=5)
if res.status_code == 200:
for item in res.json():
if item['cur_unit'] == 'USD': return item['deal_bas_r']
return "연결 대기"
except: return "확인 불가"

def get_bok_base_rate(authkey):
url = f"https://ecos.bok.or.kr/api/StatisticSearch/{authkey}/json/kr/1/1/722Y001/D/20260101/20261231/0101000/"
try:
res = requests.get(url, timeout=5)
if res.status_code == 200:
return res.json()['StatisticSearch']['row'][0]['DATA_VALUE']
return "조회 대기"
except: return "확인 불가"

def get_customs_trade_data(authkey, hs_code):
last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y%m')
url = f"http://openapi.customs.go.kr/openapi/service/newTradestatistics/getNewTradestatisticsList?serviceKey={authkey}&searchBgnDe={last_month}&searchEndDe={last_month}&searchItemCd={hs_code}"
try:
res = requests.get(url, timeout=5)
if res.status_code == 200:
root = ET.fromstring(res.text)
item_node = root.find('.//item')
if item_node is not None:
return f"{float(item_node.find('impWeight').text):,.0f}kg / ${float(item_node.find('impPrice').text):,.0f}"
return "데이터 없음"
except: return "조회 실패"

def get_realtime_news(query):
client_id = "ln148XZ9IeyGlRln6t0e"; client_secret = "xoHOWw4BfT"
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

--- 화면 실행 ---
usd_rate = get_exchange_rate(EXIM_AUTH_KEY)
bok_rate = get_bok_base_rate(BOK_AUTH_KEY)

st.markdown(f"<div style='text-align:right;'><span style='color:#007BFF; font-weight:bold;'>💱 환율: {usd_rate}원 | 🏦 기준금리: {bok_rate}%</span></div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#007BFF;'>🏗️ AI 물가예측 프로그램</h2>", unsafe_allow_html=True)

item_choice = st.radio("", ["레미콘", "철근", "알루미늄판"], horizontal=True, index=1)

if item_choice == "철근":
prices = [880000, 880000, 870000, 870000, 880000, 880000, 900000, 895000, 870000, 850000, 840000, 830000, 820000, 840000, 850000, 820000, 820000, 810000, 790000, 800000, 780000, 770000, 800000, 815000, 835000, 855000]
dates = ['24.04', '24.05', '24.06', '24.07', '24.08', '24.09', '24.10', '24.11', '24.12', '25.01', '25.02', '25.03', '25.04', '25.05', '25.06', '25.07', '25.08', '25.09', '25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
ai_summary = "철근 가격은 공급망 이슈로 인해 26년 초부터 다시 반등 추세에 있습니다."
img_path, kw, label_name, hs_code = "이형철근.png", "철근 가격", "철근가격", "721420"
y_min, y_max = 600000, 1000000
elif item_choice == "레미콘":
prices = [80000, 82000, 84000, 86000, 88000, 90000, 92000, 95000]
dates = ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
ai_summary = "레미콘은 시멘트 가격 인상 압박으로 완만한 상승세가 예상됩니다."
img_path, kw, label_name, hs_code = "레미콘.png", "레미콘 시황", "레미콘가격", "382450"
y_min, y_max = 0, 130000
else:
prices = [6100, 6300, 6400, 6600, 6800, 7260, 7460, 7600]
dates = ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05(예측)']
ai_summary = "알루미늄판은 글로벌 공급 부족으로 변동성이 심화되고 있습니다."
img_path, kw, label_name, hs_code = "알루미늄판.png", "알루미늄판 시황", "알루미늄가격", "760611"
y_min, y_max = 0, 10000

df = pd.DataFrame({'날짜': dates, label_name: prices})
trade_data = get_customs_trade_data(CUSTOMS_AUTH_KEY, hs_code)

c1, c2 = st.columns([1, 1.5], gap="large")
with c1:
st.markdown(f'<div class="unified-card"><h4>📋 {item_choice} 실황 이미지</h4>', unsafe_allow_html=True)
try: st.image(img_path)
except: st.error("이미지 없음")
st.markdown('</div>', unsafe_allow_html=True)

with c2:
st.markdown(f'<div class="unified-card"><h4>📈 {item_choice} 최근 6개월 가격 추이</h4>', unsafe_allow_html=True)
fig = px.bar(df.tail(6), x='날짜', y=label_name, text=label_name)
fig.update_traces(
marker_color=['#B0C4DE']*5 + ['#FF8C00'],
texttemplate='%{text:,.0f}',
textfont=dict(size=22, color='#000000'),
textposition='outside'
)
fig.update_layout(
yaxis=dict(range=[y_min, y_max], tickfont=dict(size=18, color='#000000'), title=dict(font=dict(color='#000000'), text="가격")),
xaxis=dict(tickfont=dict(size=18, color='#000000'), title=dict(font=dict(color='#000000'), text="날짜")),
margin=dict(t=50, b=50), height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
bargap=0.4
)
st.plotly_chart(fig, use_container_width=True)
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
.yellow-table {{ min-width: 3200px; border-collapse: collapse; text-align: center; font-family: sans-serif; }}
.yellow-table th, .yellow-table td {{ padding: 15px 30px; border: 1px solid #E6E0A4; font-size: 18px; color: black; }}
.yellow-table th {{ background-color: #FDF17C; }}
</style>
<div class="scroll-container">
<button class="nav-btn" onmousedown="scrollT(-30)" onmouseup="stopS()" onmouseleave="stopS()"> < </button>
<div id="scroll-box" class="table-wrapper">
<table class="yellow-table">
<thead><tr><th>구분</th>{t_th}</tr></thead>
<tbody>{t_td}</tbody>
</table>
</div>
<button class="nav-btn" onmousedown="scrollT(30)" onmouseup="stopS()" onmouseleave="stopS()"> > </button>
</div>
<script>
var timer;
function scrollT(speed) {{ timer = setInterval(function(){{ document.getElementById('scroll-box').scrollLeft += speed; }}, 20); }}
function stopS() {{ clearInterval(timer); }}
</script>
""", height=220)
st.markdown('</div>', unsafe_allow_html=True)

c3, c4 = st.columns([1, 1.5], gap="large")
with c3:
st.markdown(f"""
<div class="unified-card">
<h4>🤖 AI 시황 및 통계 분석</h4>
<p style='font-size:19px;'><b>분석 의견:</b> {ai_summary}</p>
<hr>
<p style='font-size:18px; color:#007BFF;'><b>📦 관세청 전월 수입 실적:</b> {trade_data}</p>
</div>
""", unsafe_allow_html=True)
with c4:
st.markdown('<div class="unified-card"><h4>📰 실시간 시장 뉴스 브리핑</h4>', unsafe_allow_html=True)
news_list = get_realtime_news(kw)
if news_list:
n_html = "<table class='yellow-table' style='font-size:16px;'><thead><tr><th style='width:150px;'>핵심 단어</th><th>뉴스 요약</th><th style='width:150px;'>언론사</th></tr></thead><tbody>"
for n in news_list:
clean_t = n['title'].replace('<b>','').replace('</b>','')
words = clean_t.split()
keyword = words[0] if words else "뉴스"
press = get_exact_press(n)
n_html += f"<tr><td style='font-weight:bold; color:#007BFF;'>#{keyword[:4]}</td><td style='text-align:left;'><a href='{n['link']}' class='news-link' target='_blank'>{clean_t}</a></td><td style='font-weight:bold;'>{press}</td></tr>"
st.markdown(n_html + "</tbody></table>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
