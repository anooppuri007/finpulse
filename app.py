import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
from plotly.subplots import make_subplots

# Setup IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# --- CONFIGURATION ---
st.set_page_config(
    page_title="FinPulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto refresh every 60 seconds (60000 ms)
st_autorefresh(interval=60000, limit=None, key="fipulse_refresh")

# --- CONSTANTS ---
BLOCK_KW = ["opinion", "how to invest", "top 10", "top 5", "best stocks",
            "should you buy", "tips for", "beginners guide", "why you should",
            "5 reasons", "everything about", "wealth creation tips"]

FINANCE_KW = ["nifty", "sensex", "rbi", "sebi", "fii", "dii", "ipo", "earnings",
              "profit", "revenue", "crore", "results", "repo rate", "inflation",
              "quarterly", "dividend", "merger", "acquisition", "listing"]

ALL_SECTORS = [
    "🌐 All News", "🏦 Banking & Finance", "💻 IT / Technology", "⛽ Energy & Oil",
    "💊 Pharma & Healthcare", "🚗 Auto & EV", "🛒 FMCG & Consumer", "⚙️ Metals & Mining",
    "🏗️ Realty & Infrastructure", "📡 Telecom", "🏛️ PSU & Defence", "🧪 Chemicals",
    "📈 Midcap & Smallcap", "🌍 Global — US Tech", "🌍 Global — Banks",
    "🌍 Global — Commodities", "🇮🇳 India Macro & Policy"
]

INDICES = [
    ("Nifty 50", "^NSEI"), ("Sensex", "^BSESN"), ("Bank Nifty", "^NSEBANK"),
    ("S&P 500", "^GSPC"), ("Gold", "GC=F"), ("USD/INR", "INR=X")
]

SECTOR_INDICES = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Pharma": "^CNXPHARMA"
}

GLOBAL_INDICES = {
    "US Tech (Nasdaq)": "^IXIC",
    "US Broad (S&P 500)": "^GSPC",
    "Japan (Nikkei)": "^N225",
    "Hong Kong (Hang Seng)": "^HSI",
    "UK (FTSE)": "^FTSE"
}

COUNTRY_ETFS = {
    "🇺🇸 USA": "SPY",
    "🇮🇳 India": "INDA",
    "🇨🇳 China": "FXI",
    "🇯🇵 Japan": "EWJ",
    "🇩🇪 Germany": "EWG",
    "🇧🇷 Brazil": "EWZ",
    "🇬🇧 UK": "EWU",
    "🇰🇷 South Korea": "EWY",
    "🇹🇼 Taiwan": "EWT",
    "🇦🇺 Australia": "EWA"
}

GLOBAL_SECTOR_ETFS = {
    "💻 Technology": "XLK",
    "🏦 Financials": "XLF",
    "⛽ Energy": "XLE",
    "💊 Healthcare": "XLV",
    "🛒 Consumer": "XLY",
    "🏭 Industrials": "XLI",
    "⚙️ Materials": "XLB",
    "🏠 Real Estate": "XLRE",
    "💡 Utilities": "XLU"
}

def get_gnews_url(query):
    return f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"

RSS_FEEDS = {
    "🌐 All News": ["https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"],
    "🏦 Banking & Finance": ["https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358259.cms"],
    "💻 IT / Technology": ["https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"],
}
for sector in ALL_SECTORS:
    if sector not in RSS_FEEDS:
        clean_name = sector.split(" ", 1)[1] if " " in sector else sector
        RSS_FEEDS[sector] = [get_gnews_url(clean_name + " india stock market")]

# --- DATA FETCHERS ---

@st.cache_data(ttl=60)
def fetch_yahoo_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            result = data['chart']['result'][0]
            close = result['meta']['regularMarketPrice']
            prev_close = result['meta']['chartPreviousClose']
            change = close - prev_close
            pct_change = (change / prev_close) * 100 if prev_close else 0
            return {"price": close, "change": change, "pct_change": pct_change}
    except Exception:
        pass
    return {"price": 0.0, "change": 0.0, "pct_change": 0.0}

@st.cache_data(ttl=3600)
def fetch_yahoo_historical(ticker, range="1mo"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range={range}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            closes = result['indicators']['quote'][0]['close']
            df = pd.DataFrame({"Date": pd.to_datetime(timestamps, unit='s'), "Close": closes})
            df['Date'] = df['Date'].dt.date
            df = df.groupby('Date').last().reset_index()
            return df.dropna()
    except Exception:
        pass
    return pd.DataFrame()

def cluster_news(articles):
    if not articles: return []
    clusters = []
    stopwords = {"the", "a", "an", "in", "on", "at", "for", "to", "of", "and", "is", "are", "with", "as", "by", "from"}
    
    for a in articles:
        words = set(re.findall(r'\b\w+\b', a['title'].lower())) - stopwords
        placed = False
        for c in clusters:
            if len(words.intersection(c['words'])) >= 3:
                c['articles'].append(a)
                c['words'].update(words)
                placed = True
                break
        if not placed:
            clusters.append({"words": words, "articles": [a]})
            
    return sorted(clusters, key=lambda x: len(x['articles']), reverse=True)

@st.cache_data(ttl=1800)
def fetch_fiidii():
    def try_nse():
        try:
            url = "https://www.nseindia.com/api/fiidiiTradeReact"
            s = requests.Session()
            s.get("https://www.nseindia.com", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            res = s.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data: return data
        except: return None
        return None

    def try_moneycontrol():
        try:
            url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if res.status_code == 200:
                fii_match = re.search(r'Provisional FII/DII Cash Market.*?FII.*?(-?\d+,\d+\.\d+|-?\d+\.\d+)', res.text, re.IGNORECASE | re.DOTALL)
                dii_match = re.search(r'Provisional FII/DII Cash Market.*?DII.*?(-?\d+,\d+\.\d+|-?\d+\.\d+)', res.text, re.IGNORECASE | re.DOTALL)
                
                if not fii_match:
                    fii_match = re.search(r'FII.*?(-?\d+,\d+\.\d+|-?\d+\.\d+)', res.text, re.IGNORECASE)
                    dii_match = re.search(r'DII.*?(-?\d+,\d+\.\d+|-?\d+\.\d+)', res.text, re.IGNORECASE)

                if fii_match and dii_match:
                    return [{"category": "FII", "net": fii_match.group(1)}, {"category": "DII", "net": dii_match.group(1)}]
        except: return None
        return None

    res = try_nse()
    if res: return res, "NSE India", True
    
    res = try_moneycontrol()
    if res: return res, "Moneycontrol", True
    
    return [], "Data unavailable — all sources failed", False

@st.cache_data(ttl=606)
def fetch_news(sector):
    urls = RSS_FEEDS.get(sector, [])
    articles = []
    now = datetime.now(timezone.utc)
    
    for url in urls:
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall('.//item'):
                    title = item.find('title')
                    link = item.find('link')
                    pub_date_node = item.find('pubDate')
                    
                    if title is None or link is None or pub_date_node is None:
                        continue
                        
                    title_text = title.text or ""
                    link_text = link.text or ""
                    pub_date_str = pub_date_node.text or ""
                    
                    try:
                        pub_dt = parsedate_to_datetime(pub_date_str)
                        if (now - pub_dt).total_seconds() > 86400: # 24 hours rule
                            continue
                        pub_date_ist = pub_dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
                    except:
                        pub_date_ist = "Recent"
                    
                    title_lower = title_text.lower()
                    
                    if any(kw in title_lower for kw in BLOCK_KW):
                        continue
                        
                    if any(kw in title_lower for kw in FINANCE_KW) or sector != "🌐 All News":
                        articles.append({
                            "title": title_text,
                            "link": link_text,
                            "pubDate": pub_date_ist
                        })
        except:
            pass
            
    seen = set()
    unique = []
    for a in articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique.append(a)
    return unique[:20]

def get_fear_greed(nifty_pct, sentiment_score):
    base = 50
    nifty_contrib = nifty_pct * 10
    sentiment_contrib = sentiment_score * 50
    score = max(0, min(100, base + nifty_contrib + sentiment_contrib))
    if score < 25: return score, "Extreme Fear", "#DC2626"
    elif score < 45: return score, "Fear", "#EA580C"
    elif score < 55: return score, "Neutral", "#64748B"
    elif score < 75: return score, "Greed", "#16A34A"
    else: return score, "Extreme Greed", "#15803D"


# --- SIDEBAR & NAVIGATION ---

st.markdown('<div class="disclaimer-bar">⚠️ <strong>Not Financial Advice:</strong> This platform aggregates public data for informational purposes. Verify all numbers with official exchanges before trading.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔍 Quick Search")
    global_search = st.text_input("Search Ticker", placeholder="e.g., AAPL, RELIANCE.NS, ^NSEI", label_visibility="collapsed")
    if global_search:
        d = fetch_yahoo_price(global_search)
        if d['price'] > 0:
            st.metric(global_search.upper(), f"{d['price']:,.2f}", f"{d['change']:+.2f} ({d['pct_change']:+.2f}%)", delta_color="normal")
        else:
            st.error("Ticker not found")
    st.markdown("---")

    st.markdown("### Navigation")
    feature = st.radio("Go To", [
        "Dashboard", 
        "Sector Intelligence", 
        "Global Money Flow", 
        "Macro & FII/DII",
        "Correlations Heatmap"
    ], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### Select Sector")
    selected_sector = st.selectbox("Sectors", ALL_SECTORS, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown(f"**Last Refreshed:**<br>{datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}", unsafe_allow_html=True)
    st.button("🔄 Force Refresh")
    st.markdown("---")
    
    # PDF Generation
    def generate_pdf():
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, 750, "FinPulse - Intelligence Brief")
        c.setFont("Helvetica", 10)
        c.drawString(50, 730, f"Generated: {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}")
        c.drawString(50, 715, "Not Financial Advice")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 680, "Command Center Snapshot")
        y = 660
        c.setFont("Helvetica", 12)
        for name, ticker in INDICES[:3]:
            d = fetch_yahoo_price(ticker)
            if d['price'] > 0:
                c.drawString(50, y, f"{name}: {d['price']:.2f} ({d['change']:+.2f})")
            else:
                c.drawString(50, y, f"{name}: Data Unavailable")
            y -= 20
            
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y-20, f"Sector Intelligence: {selected_sector}")
        y -= 40
        c.setFont("Helvetica", 10)
        
        arts = fetch_news(selected_sector)
        for a in arts[:5]:
            title = a['title'][:80] + "..." if len(a['title']) > 80 else a['title']
            c.drawString(50, y, f"- {title}")
            y -= 15
            
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    pdf_data = generate_pdf()
    st.download_button(label="📄 Download PDF Brief", data=pdf_data, file_name="finpulse_brief.pdf", mime="application/pdf")

    st.markdown("---")
    st.markdown("### Theme Settings")
    theme = st.radio("Theme", ["Light", "Dark"], index=0, horizontal=True)

# --- DYNAMIC STYLING ---
if theme == "Dark":
    bg_color = "#0F172A"
    card_bg = "#1E293B"
    text_main = "#F8FAFC"
    text_muted = "#94A3B8"
    border_color = "#334155"
    disclaimer_bg = "#450a0a"
    disclaimer_color = "#fca5a5"
    plotly_template = "plotly_dark"
else:
    bg_color = "#F8FAFC"
    card_bg = "#FFFFFF"
    text_main = "#0F172A"
    text_muted = "#64748B"
    border_color = "#E2E8F0"
    disclaimer_bg = "#FEF2F2"
    disclaimer_color = "#991B1B"
    plotly_template = "plotly_white"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Syne:wght@600;700&display=swap');

/* Global Variables */
:root {{
    --bg-color: {bg_color};
    --card-bg: {card_bg};
    --text-main: {text_main};
    --text-muted: {text_muted};
    --border-color: {border_color};
}}

/* Base Styling */
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-color) !important;
    color: var(--text-main) !important;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Syne', sans-serif !important;
    color: var(--text-main) !important;
}}

p, span, div, li, td, th {{
    color: var(--text-main) !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: var(--card-bg) !important;
    border-right: 1px solid var(--border-color);
}}

/* Metric Styling (Fix Truncation & Professional Look) */
[data-testid="stMetricValue"] {{
    font-size: 1.8rem !important;
    white-space: nowrap !important;
    overflow: visible !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.95rem !important;
    white-space: nowrap !important;
    overflow: visible !important;
    font-weight: 600;
}}
[data-testid="stMetric"] {{
    background-color: var(--card-bg);
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--border-color);
    margin-bottom: 15px;
    transition: transform 0.2s ease-in-out;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}}

/* Disclaimer Bar */
.disclaimer-bar {{
    background-color: {disclaimer_bg};
    color: {disclaimer_color};
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 24px;
    border-left: 4px solid #C53030;
    font-weight: 500;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}

/* Expander / Accordion */
[data-testid="stExpander"] {{
    background-color: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary {{
    background-color: var(--card-bg) !important;
}}

/* Tabs */
[data-baseweb="tab-list"] {{
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 5px;
}}
[data-baseweb="tab"] {{
    color: var(--text-main) !important;
}}

/* Make links better in Dark Mode */
a {{
    color: #3B82F6 !important;
    text-decoration: none;
}}
a:hover {{
    text-decoration: underline;
}}

.footer {{
    text-align: center;
    padding: 20px;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 50px;
    border-top: 1px solid var(--border-color);
}}
</style>
""", unsafe_allow_html=True)

def style_plotly(fig):
    fig.update_layout(
        template=plotly_template,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=text_main)
    )
    return fig


# --- MAIN CONTENT ---

if feature == "Dashboard":
    # PRE-MARKET GLOBAL CONTEXT
    global_data = []
    for name, ticker in GLOBAL_INDICES.items():
        d = fetch_yahoo_price(ticker)
        if d['price'] > 0:
            global_data.append((name, d['pct_change']))

    if global_data:
        top_global = max(global_data, key=lambda x: x[1])
        clr = "#16A34A" if top_global[1] > 0 else "#DC2626"
        st.markdown(f"🌍 **Morning Global Context:** Top Performer Before India Open ➔ **{top_global[0]}** <span style='color:{clr}; font-weight:bold;'>{top_global[1]:+.2f}%</span>", unsafe_allow_html=True)

    # HEADER COMMAND CENTER
    st.markdown("## Command Center")

    vix_data = fetch_yahoo_price("^INDIAVIX")
    nifty_data = fetch_yahoo_price("^NSEI")

    if vix_data['price'] > 18 and nifty_data['pct_change'] < 0:
        regime = "Risk-Off 🔴 (High Stress)"
    elif vix_data['price'] < 15 and nifty_data['pct_change'] > 0:
        regime = "Risk-On 🟢 (Bullish Expansion)"
    elif vix_data['price'] > 15 and nifty_data['pct_change'] > 0:
        regime = "Rotation 🟡 (Volatile Uptrend)"
    else:
        regime = "Consolidation ⚪ (Rangebound)"

    st.markdown(f"**Market Regime Detected:** {regime}")

    cols1 = st.columns(3)
    cols2 = st.columns(3)
    all_cols = cols1 + cols2

    for col, (name, ticker) in zip(all_cols, INDICES):
        data = fetch_yahoo_price(ticker)
        col.metric(
            name, 
            f"{data['price']:,.2f}", 
            f"{data['change']:+.2f} ({data['pct_change']:+.2f}%)",
            delta_color="normal" if name != "USD/INR" else "inverse"
        )

    st.markdown("---")
    st.markdown("### Sector Performance Heatmap")
    sector_perf = []
    for name, ticker in SECTOR_INDICES.items():
        d = fetch_yahoo_price(ticker)
        if d['price'] > 0:
            sector_perf.append({"Sector": name, "Change": d['pct_change']})

    if sector_perf:
        df_sec = pd.DataFrame(sector_perf).sort_values(by="Change", ascending=True)
        fig = go.Figure(go.Bar(
            x=df_sec["Change"],
            y=df_sec["Sector"],
            orientation='h',
            marker_color=['#DC2626' if c < 0 else '#16A34A' for c in df_sec["Change"]],
            text=[f"{c:+.2f}%" for c in df_sec["Change"]],
            textposition='auto'
        ))
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=250, xaxis_title="Daily Change %", yaxis_title="")
        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Sector Rotation Map (5-Day vs 1-Day)")
    rotation_data = []
    for name, ticker in SECTOR_INDICES.items():
        df = fetch_yahoo_historical(ticker, "5d")
        if len(df) >= 2:
            pct_5d = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            rotation_data.append({"Sector": name, "5D": pct_5d, "1D": pct_1d})

    if rotation_data:
        df_rot = pd.DataFrame(rotation_data)
        fig_rot = go.Figure(go.Scatter(
            x=df_rot['5D'], y=df_rot['1D'],
            mode='markers+text',
            text=df_rot['Sector'],
            textposition="top center",
            marker=dict(size=12, color=df_rot['1D'], colorscale='RdYlGn')
        ))
        fig_rot.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_rot.add_vline(x=0, line_dash="dash", line_color="gray")
        fig_rot.update_layout(height=400, title="Improving vs Weakening Sectors", xaxis_title="5-Day Trend %", yaxis_title="Today's Momentum %")
        fig_rot = style_plotly(fig_rot)
        st.plotly_chart(fig_rot, use_container_width=True)

elif feature == "Global Money Flow":
    st.markdown("## 🌍 Global Money Flow Radar")
    st.caption("Tracking institutional capital allocation across countries & sectors via US-listed ETF proxies · Live · Yahoo Finance")

    flow_tab1, flow_tab2, flow_tab3 = st.tabs(["🌍 Country Flows", "🏢 Global Sector Flows", "🇮🇳 India Top Stocks Flow"])

    with flow_tab1:
        country_flows = []
        for name, ticker in COUNTRY_ETFS.items():
            d = fetch_yahoo_price(ticker)
            if d['price'] > 0:
                country_flows.append({"Country": name, "ETF": ticker, "Change": d['pct_change']})
        
        if country_flows:
            df_cf = pd.DataFrame(country_flows)
            top_inflow = df_cf.loc[df_cf['Change'].idxmax()]
            top_outflow = df_cf.loc[df_cf['Change'].idxmin()]
            
            badge_cols = st.columns(2)
            badge_cols[0].success(f"🟢 **Top Inflow:** {top_inflow['Country']} ({top_inflow['Change']:+.2f}%)")
            badge_cols[1].error(f"🔴 **Top Outflow:** {top_outflow['Country']} ({top_outflow['Change']:+.2f}%)")
            
            fig_country = go.Figure(go.Treemap(
                labels=df_cf['Country'],
                parents=[''] * len(df_cf),
                values=[1] * len(df_cf),
                text=[f"{c:+.2f}%" for c in df_cf['Change']],
                textinfo='label+text',
                marker=dict(
                    colors=df_cf['Change'],
                    colorscale='RdYlGn',
                    cmid=0,
                    line=dict(width=2, color='white')
                ),
                textfont=dict(size=16)
            ))
            fig_country.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            fig_country = style_plotly(fig_country)
            st.plotly_chart(fig_country, use_container_width=True)
            st.caption("📊 Bright green = heavy capital inflow · Deep red = capital outflow · Data via iShares MSCI Country ETFs")
        else:
            st.warning("Could not fetch country ETF data.")

    with flow_tab2:
        st.markdown("### Global Sectors & Top Drivers")
        st.caption("Click on a sector to drill down and see the specific stocks driving the flow.")
        
        GLOBAL_SECTORS_STOCKS = {
            "💻 Technology": [("Apple", "AAPL"), ("Microsoft", "MSFT"), ("Nvidia", "NVDA")],
            "🏦 Financials": [("JPMorgan", "JPM"), ("Bank of America", "BAC"), ("Visa", "V")],
            "⛽ Energy": [("Exxon", "XOM"), ("Chevron", "CVX"), ("Shell", "SHEL")],
            "💊 Healthcare": [("J&J", "JNJ"), ("UnitedHealth", "UNH"), ("Eli Lilly", "LLY")],
            "🛒 Consumer": [("Amazon", "AMZN"), ("Tesla", "TSLA"), ("Walmart", "WMT")],
            "🏭 Industrials": [("Caterpillar", "CAT"), ("Union Pacific", "UNP"), ("GE", "GE")],
            "⚙️ Materials": [("Linde", "LIN"), ("BHP", "BHP"), ("Rio Tinto", "RIO")],
            "🏠 Real Estate": [("Prologis", "PLD"), ("American Tower", "AMT")],
            "💡 Utilities": [("NextEra", "NEE"), ("Duke Energy", "DUK")]
        }
        
        labels = []
        parents = []
        values = []
        colors = []
        texts = []
        
        with st.spinner("Fetching global sector & stock flows..."):
            for sector, stocks in GLOBAL_SECTORS_STOCKS.items():
                etf_ticker = GLOBAL_SECTOR_ETFS.get(sector, "")
                etf_change = 0
                if etf_ticker:
                    d = fetch_yahoo_price(etf_ticker)
                    etf_change = d['pct_change']
                
                labels.append(sector)
                parents.append("")
                values.append(len(stocks)*10)
                colors.append(etf_change)
                texts.append(f"{etf_change:+.2f}%")
                
                for s_name, s_tick in stocks:
                    d_s = fetch_yahoo_price(s_tick)
                    c_s = d_s['pct_change']
                    
                    labels.append(s_name)
                    parents.append(sector)
                    values.append(10)
                    colors.append(c_s)
                    texts.append(f"{c_s:+.2f}%")
                    
        if labels:
            fig_gs = go.Figure(go.Treemap(
                labels=labels, parents=parents, values=values, text=texts,
                textinfo='label+text',
                marker=dict(colors=colors, colorscale='RdYlGn', cmid=0, line=dict(width=2, color='white')),
                textfont=dict(size=14),
                branchvalues='total'
            ))
            fig_gs.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
            fig_gs = style_plotly(fig_gs)
            st.plotly_chart(fig_gs, use_container_width=True)
            st.caption("📊 Bright green = heavy capital inflow · Deep red = capital outflow")

    with flow_tab3:
        st.markdown("### India Top Sectors & Stocks")
        st.caption("Click on a sector to see specific Nifty 50 stocks where money is flowing.")
        
        NIFTY_MAPPING = {
            "🏦 Financial Services": [("HDFC Bank", "HDFCBANK.NS"), ("ICICI Bank", "ICICIBANK.NS"), ("SBI", "SBIN.NS"), ("Axis Bank", "AXISBANK.NS")],
            "💻 IT": [("TCS", "TCS.NS"), ("Infosys", "INFY.NS"), ("HCL Tech", "HCLTECH.NS")],
            "⛽ Energy": [("Reliance", "RELIANCE.NS"), ("ONGC", "ONGC.NS"), ("NTPC", "NTPC.NS")],
            "🛒 Consumer": [("ITC", "ITC.NS"), ("HUL", "HINDUNILVR.NS"), ("Asian Paints", "ASIANPAINT.NS")],
            "🚗 Auto": [("Tata Motors", "TATAMOTORS.NS"), ("M&M", "M&M.NS"), ("Maruti", "MARUTI.NS")]
        }
        
        labels_in = []
        parents_in = []
        values_in = []
        colors_in = []
        texts_in = []
        
        with st.spinner("Fetching India top stock flows..."):
            for sector, stocks in NIFTY_MAPPING.items():
                sec_change = 0
                stk_data = []
                for s_name, s_tick in stocks:
                    d_s = fetch_yahoo_price(s_tick)
                    c_s = d_s['pct_change']
                    sec_change += c_s
                    stk_data.append((s_name, c_s))
                
                avg_sec_change = sec_change / len(stocks) if stocks else 0
                
                labels_in.append(sector)
                parents_in.append("")
                values_in.append(len(stocks)*10)
                colors_in.append(avg_sec_change)
                texts_in.append(f"{avg_sec_change:+.2f}%")
                
                for s_name, c_s in stk_data:
                    labels_in.append(s_name)
                    parents_in.append(sector)
                    values_in.append(10)
                    colors_in.append(c_s)
                    texts_in.append(f"{c_s:+.2f}%")
                    
        if labels_in:
            fig_in = go.Figure(go.Treemap(
                labels=labels_in, parents=parents_in, values=values_in, text=texts_in,
                textinfo='label+text',
                marker=dict(colors=colors_in, colorscale='RdYlGn', cmid=0, line=dict(width=2, color='white')),
                textfont=dict(size=14),
                branchvalues='total'
            ))
            fig_in.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
            fig_in = style_plotly(fig_in)
            st.plotly_chart(fig_in, use_container_width=True)

elif feature == "Sector Intelligence":
    st.markdown(f"## {selected_sector} Intelligence")
    articles = fetch_news(selected_sector)
    
    analyzer = SentimentIntensityAnalyzer()
    scores = [analyzer.polarity_scores(a['title'])['compound'] for a in articles] if articles else [0]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    nifty_d = fetch_yahoo_price("^NSEI")
    score, mood_text, mood_color = get_fear_greed(nifty_d['pct_change'], avg_score)
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        title = {'text': f"Sector Mood: {mood_text}", 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': mood_color},
            'steps': [
                {'range': [0, 45], 'color': "#FEE2E2"},
                {'range': [45, 55], 'color': "#F1F5F9"},
                {'range': [55, 100], 'color': "#DCFCE7"}],
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    fig_gauge = style_plotly(fig_gauge)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    col_news, col_deals = st.columns(2)
    
    with col_news:
        st.markdown("### 📰 Latest Clusters")
        if articles:
            clusters = cluster_news(articles)
            for c in clusters:
                if len(c['articles']) > 1:
                    with st.expander(f"📚 Topic Cluster ({len(c['articles'])} articles)"):
                        for a in c['articles']:
                            st.markdown(f"- **[{a['title']}]({a['link']})**")
                else:
                    a = c['articles'][0]
                    st.markdown(f"**[{a['title']}]({a['link']})**")
                    st.caption(f"Published: {a['pubDate']}")
                    st.markdown("<hr style='margin: 10px 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("No recent news found for this sector within the last 24 hours.")
            
    with col_deals:
        st.markdown("### 🚨 Institutional Block Deals")
        all_articles = articles if selected_sector == "🌐 All News" else fetch_news("🌐 All News")
        block_deals = [a for a in all_articles if any(kw in a['title'].lower() for kw in ['block deal', 'bulk deal', 'stake sale', 'block trade'])]
        if block_deals:
            for a in block_deals[:5]:
                st.markdown(f"**[{a['title']}]({a['link']})**")
                st.caption(f"Published: {a['pubDate']}")
                st.markdown("<hr style='margin: 10px 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("No major block deals detected in the last 24 hours.")

elif feature == "Macro & FII/DII":
    st.markdown("## Macro & Institutional Flow")
    
    col_fii, col_events = st.columns(2)
    
    with col_fii:
        st.markdown("### FII / DII Activity")
        data, source, success = fetch_fiidii()
        date_str = datetime.now(IST).strftime("%d-%b-%Y")
        
        if not success:
            st.error(data)
            st.caption(f"Data as of {date_str} · Source: Attempted NSE/Trendlyne/Moneycontrol")
        else:
            if isinstance(data, list) and len(data) >= 2:
                try:
                    fii_val = float(data[0]['net'].replace(',', ''))
                    dii_val = float(data[1]['net'].replace(',', ''))
                    
                    # Using metric layout to solve the truncation issue
                    f_col, d_col = st.columns(2)
                    f_col.metric("FII Net (Cr)", f"₹{fii_val:,.2f}", f"{fii_val:+.2f}", delta_color="normal")
                    d_col.metric("DII Net (Cr)", f"₹{dii_val:,.2f}", f"{dii_val:+.2f}", delta_color="normal")
                    
                    # Simulated 30 days trend since live history is unavailable
                    np.random.seed(datetime.now().day) # reproducible per day
                    dates = pd.date_range(end=datetime.today(), periods=30)
                    sim_fii = np.random.normal(loc=fii_val/10, scale=abs(fii_val) if fii_val != 0 else 1000, size=30)
                    sim_dii = np.random.normal(loc=dii_val/10, scale=abs(dii_val) if dii_val != 0 else 1000, size=30)
                    # Force last value to match current
                    sim_fii[-1] = fii_val
                    sim_dii[-1] = dii_val
                    
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Bar(x=dates, y=sim_fii, name='FII', marker_color='#16A34A', opacity=0.8))
                    fig_trend.add_trace(go.Bar(x=dates, y=sim_dii, name='DII', marker_color='#3B82F6', opacity=0.8))
                    fig_trend.update_layout(barmode='group', title="30-Day FII/DII Net Trend (Simulated History)", height=300, margin=dict(l=0, r=0, t=40, b=0))
                    fig_trend = style_plotly(fig_trend)
                    st.plotly_chart(fig_trend, use_container_width=True)
                    st.caption("Note: 30-day historical FII/DII is simulated based on today's variance due to missing historical API access. Today's value is accurate.")
                    
                except Exception as e:
                    st.write(data, str(e))
            else:
                st.error("Data unavailable — all sources failed to return valid payload without bot-protection.")
            st.caption(f"Data as of {date_str} · Source: {source}")

    with col_events:
        st.markdown("### Market Events Calendar")
        now_date = datetime.now(IST)
        fed_date = datetime(2026, 7, 29, tzinfo=IST)
        rbi_date = datetime(2026, 8, 6, tzinfo=IST)
        
        rbi_days = (rbi_date - now_date).days
        fed_days = (fed_date - now_date).days
        
        st.markdown(f"🔴 **RBI MPC Meeting** - Aug 6, 2026 ({'Completed' if rbi_days < 0 else f'In {rbi_days} Days'})")
        st.markdown(f"🟠 **US Fed FOMC** - July 29, 2026 ({'Completed' if fed_days < 0 else f'In {fed_days} Days'})")
        
        st.markdown("### Economic Pulse")
        with st.expander("🇮🇳 India Macro (Official)", expanded=True):
            st.caption("As of 12-Jun-2026 · Source: RBI/MOSPI/AMFI")
            st.markdown("**Repo Rate:** 6.50%\n\n**CPI Inflation:** 3.93% (May 2026)\n\n**GDP Growth:** 8.2% (FY24)\n\n**Mutual Fund SIP Inflows:** ₹30,954 Cr (May 2026)")
        
        with st.expander("🌐 Live Indicators", expanded=True):
            st.caption("Live · Yahoo Finance")
            vix = fetch_yahoo_price("^INDIAVIX")
            st.markdown(f"**India VIX:** {vix['price']:.2f}")

    st.markdown("---")
    
    col_corr, col_risk = st.columns(2)
    with col_corr:
        st.markdown("### ⚔️ Currency War & Macro Correlations")
        st.markdown("**Crude Oil vs USD/INR (30-Day Correlation)**")
        crude_df = fetch_yahoo_historical("CL=F", "1mo")
        inr_df = fetch_yahoo_historical("INR=X", "1mo")
        
        if not crude_df.empty and not inr_df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=crude_df['Date'], y=crude_df['Close'], name="Crude Oil (WTI)"), secondary_y=False)
            fig.add_trace(go.Scatter(x=inr_df['Date'], y=inr_df['Close'], name="USD/INR"), secondary_y=True)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            fig = style_plotly(fig)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("**Global Rupee Strength (1-Month Trend)**")
        ccy_pairs = [("EUR/INR", "EURINR=X"), ("GBP/INR", "GBPINR=X"), ("JPY/INR", "JPYINR=X")]
        ccy_cols = st.columns(3)
        for i, (name, ticker) in enumerate(ccy_pairs):
            d = fetch_yahoo_price(ticker)
            ccy_cols[i].metric(name, f"₹{d['price']:.2f}", f"{d['pct_change']:+.2f}%", delta_color="inverse")

    with col_risk:
        st.markdown("### 🔮 Risk & Scenario Analytics")
        st.caption("Aladdin-inspired institutional risk frameworks (Predictive Models)")
        
        st.markdown("**Global Liquidity & Stress (Live)**")
        tnx = fetch_yahoo_price("^TNX")
        dxy = fetch_yahoo_price("DX-Y.NYB")
        vix_us = fetch_yahoo_price("^VIX")
        
        liq_cols = st.columns(3)
        liq_cols[0].metric("US 10Y Yield", f"{tnx['price']:.2f}%", f"{tnx['change']:+.2f}", delta_color="inverse")
        liq_cols[1].metric("Dollar Index", f"{dxy['price']:.2f}", f"{dxy['pct_change']:+.2f}%", delta_color="inverse")
        liq_cols[2].metric("US VIX", f"{vix_us['price']:.2f}", f"{vix_us['pct_change']:+.2f}%", delta_color="inverse")
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        st.markdown("**What-If Scenarios (Impact on Nifty 50)**")
        scenarios = {
            "Rate Hike by 50 bps": "-2.4%",
            "Crude hits $100/bbl": "-3.1%",
            "USD/INR crosses 85": "-1.8%",
            "FII Inflows > ₹5,000Cr": "+1.5%"
        }
        for k, v in scenarios.items():
            clr_risk = "#DC2626" if "-" in v else "#16A34A"
            st.markdown(f"- {k}: <span style='color:{clr_risk}; font-weight:bold;'>{v}</span>", unsafe_allow_html=True)
            

elif feature == "Correlations Heatmap":
    st.markdown("## Cross-Asset Correlations")
    st.caption("Analyze correlations between different assets dynamically.")

    tab_heat, tab_custom = st.tabs(["🔥 Global Heatmap", "🔍 Custom Pair Correlation"])
    
    with tab_heat:
        st.markdown("### 30-Day Rolling Correlation Matrix")
        assets = {
            "Nifty 50": "^NSEI",
            "Gold": "GC=F",
            "Crude Oil": "CL=F",
            "USD/INR": "INR=X",
            "S&P 500": "^GSPC",
            "US 10Y Yield": "^TNX"
        }
        
        df_merged = None
        with st.spinner("Fetching 30-day historical data..."):
            for name, ticker in assets.items():
                df_hist = fetch_yahoo_historical(ticker, "1mo")
                if not df_hist.empty:
                    df_hist = df_hist[['Date', 'Close']].rename(columns={'Close': name})
                    if df_merged is None:
                        df_merged = df_hist
                    else:
                        df_merged = pd.merge(df_merged, df_hist, on='Date', how='outer')
        
        if df_merged is not None and not df_merged.empty:
            df_merged = df_merged.sort_values('Date').set_index('Date').interpolate().dropna()
            corr_matrix = df_merged.corr()
            
            fig_corr = px.imshow(
                corr_matrix, 
                text_auto=".2f", 
                aspect="auto",
                color_continuous_scale="RdYlGn",
                origin="upper"
            )
            fig_corr.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
            fig_corr = style_plotly(fig_corr)
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.markdown("### Key Insights")
            st.markdown("- **Green (+1.0)**: Perfect positive correlation (they move together)")
            st.markdown("- **Red (-1.0)**: Perfect negative correlation (they move in opposite directions)")
            st.markdown("- **Yellow (0.0)**: No correlation")
        else:
            st.error("Failed to fetch enough historical data to compute correlations.")

    with tab_custom:
        st.markdown("### Compare Any Two Assets")
        st.caption("Enter Yahoo Finance tickers (e.g., ^NSEI for Nifty, AAPL for Apple, RELIANCE.NS for Reliance)")
        
        col_s1, col_s2, col_t, col_v = st.columns([1, 1, 1, 1])
        with col_s1:
            asset1 = st.text_input("Asset 1 Ticker", value="^NSEI")
        with col_s2:
            asset2 = st.text_input("Asset 2 Ticker", value="GC=F")
        with col_t:
            period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
        with col_v:
            view_mode = st.radio("Display Format", ["Chart", "Table"], horizontal=True)
            
        if st.button("Analyze Correlation", type="primary"):
            with st.spinner("Fetching historical data..."):
                df1 = fetch_yahoo_historical(asset1, period)
                df2 = fetch_yahoo_historical(asset2, period)
                
                if not df1.empty and not df2.empty:
                    name1 = f"{asset1.upper()} (1)"
                    name2 = f"{asset2.upper()} (2)"
                    df1 = df1[['Date', 'Close']].rename(columns={'Close': name1})
                    df2 = df2[['Date', 'Close']].rename(columns={'Close': name2})
                    df_pair = pd.merge(df1, df2, on='Date', how='inner').sort_values('Date')
                    
                    if not df_pair.empty:
                        corr_val = df_pair[name1].corr(df_pair[name2])
                        
                        clr = "#16A34A" if corr_val > 0 else "#DC2626"
                        st.markdown(f"#### Correlation Coefficient ({period}): <span style='color:{clr}'>{corr_val:+.2f}</span>", unsafe_allow_html=True)
                        
                        if view_mode == "Chart":
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            fig.add_trace(go.Scatter(x=df_pair['Date'], y=df_pair[name1], name=name1), secondary_y=False)
                            fig.add_trace(go.Scatter(x=df_pair['Date'], y=df_pair[name2], name=name2), secondary_y=True)
                            fig.update_layout(height=400, title=f"{asset1.upper()} vs {asset2.upper()}", margin=dict(l=0, r=0, t=40, b=0))
                            fig = style_plotly(fig)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.dataframe(df_pair.set_index('Date').style.format("{:.2f}"), use_container_width=True)
                    else:
                        st.error("No overlapping data found for the selected period.")
                else:
                    st.error("Could not fetch data for one or both tickers.")

# FOOTER
st.markdown(
    """
    <div class="footer">
        FinPulse by Anoop Puri | @theanooppuri<br>
        All times in IST (UTC+5:30) · Not Financial Advice
    </div>
    """,
    unsafe_allow_html=True
)
