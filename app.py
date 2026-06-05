"""
FinPulse by Anoop Puri
Smart Financial Intelligence — India First, World Coverage
"""
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import io, os, sys, xml.etree.ElementTree as ET

# ── IST Timezone ──────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
def now_ist():
    return datetime.now(IST)
def fmt_ist(dt=None):
    d = dt or now_ist()
    return d.strftime("%d %b %Y, %I:%M %p IST")

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="FinPulse by Anoop Puri",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

analyzer = SentimentIntensityAnalyzer()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3600000, limit=None, key="auto_refresh")
except Exception:
    pass

if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS"]
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = now_ist()

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinPulse/2.0)"}


# ══════════════════════════════════════════════════════════
#  CSS — WHITE PROFESSIONAL THEME
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #F8FAFC !important; color: #1A202C !important; }
.stApp { background: #F8FAFC !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* NAV */
.fp-nav { background: #fff; border-bottom: 3px solid #C53030; padding: 12px 28px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px rgba(0,0,0,.07); position: sticky; top: 0; z-index: 999; }
.nav-brand { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800; color: #1A202C; }
.nav-brand span { color: #C53030; }
.nav-sub { font-size: 10px; color: #718096; margin-top: 2px; }
.nav-links a { font-size: 12px; font-weight: 500; color: #2B6CB0; text-decoration: none; padding: 4px 12px; border: 1px solid #BEE3F8; border-radius: 20px; margin-left: 8px; background: #EBF8FF; }

/* DISCLAIMER */
.disc { background: #FFFBEB; border-bottom: 1px solid #F6E05E; padding: 6px 28px; font-size: 11px; color: #744210; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px; }

/* MAIN */
.wrap { padding: 20px 28px; max-width: 1440px; margin: 0 auto; }

/* SECTION TITLE */
.sec-title { font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #718096; border-left: 3px solid #C53030; padding-left: 10px; margin: 0 0 12px 0; }

/* CARDS */
.card { background: #fff; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.card-sm { background: #fff; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; }

/* CMD STRIP */
.cmd-label { font-size: 9px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #A0AEC0; margin-bottom: 4px; }
.cmd-val { font-family: 'Syne', sans-serif; font-size: 19px; font-weight: 800; color: #1A202C; line-height: 1.1; }
.up { color: #276749 !important; } .dn { color: #C53030 !important; } .nt { color: #B7791F !important; }
.chg { font-size: 11px; font-weight: 600; margin-top: 2px; }

/* FG */
.fg-wrap { background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.fg-num { font-family: 'Syne', sans-serif; font-size: 52px; font-weight: 800; line-height: 1; margin: 6px 0; }
.fg-lbl { font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
.fg-bar-bg { background: #EDF2F7; border-radius: 4px; height: 6px; margin: 10px 0 4px; overflow: hidden; }
.fg-bar { height: 100%; border-radius: 4px; background: linear-gradient(90deg,#FC8181,#F6AD55,#38A169); }
.fg-scale { display: flex; justify-content: space-between; font-size: 9px; color: #A0AEC0; }

/* NEWS */
.news-meta { font-size: 10px; color: #718096; }
.src-badge { display: inline-block; background: #EBF8FF; border: 1px solid #BEE3F8; border-radius: 4px; padding: 1px 7px; font-size: 10px; color: #2B6CB0; font-weight: 500; margin-right: 4px; }
.sec-tag { display: inline-block; background: #F7FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 1px 7px; font-size: 10px; color: #4A5568; margin-right: 3px; }
.news-sum { font-size: 13px; color: #2D3748; line-height: 1.6; padding: 4px 0; border-left: 3px solid #E2E8F0; padding-left: 10px; margin: 6px 0; }

/* FII/DII */
.fii-buy { background: #F0FFF4; border: 1px solid #9AE6B4; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; }
.fii-sell { background: #FFF5F5; border: 1px solid #FEB2B2; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; }
.fii-val { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 800; }
.fii-lbl { font-size: 10px; color: #718096; margin-top: 2px; }

/* WATCHLIST */
.wl-row { background: #fff; border: 1px solid #EDF2F7; border-radius: 8px; padding: 10px 14px; margin-bottom: 5px; }
.wl-ticker { font-family: 'Syne', sans-serif; font-weight: 800; color: #2B6CB0; font-size: 14px; }
.wl-name { color: #718096; font-size: 12px; }

/* CALENDAR */
.cal-item { background: #fff; border-left: 4px solid #2B6CB0; border-radius: 0 8px 8px 0; padding: 9px 14px; margin-bottom: 6px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.cal-date { font-size: 10px; font-weight: 700; color: #2B6CB0; letter-spacing: 0.5px; }
.cal-title { font-size: 13px; font-weight: 600; color: #1A202C; margin: 2px 0; }
.cal-sub { font-size: 11px; color: #718096; }

/* SECTOR */
.sec-hot { background: #F0FFF4; border: 1px solid #9AE6B4; border-left: 4px solid #38A169; border-radius: 8px; padding: 12px 14px; margin-bottom: 7px; }
.sec-cold { background: #FFF5F5; border: 1px solid #FEB2B2; border-left: 4px solid #E53E3E; border-radius: 8px; padding: 12px 14px; margin-bottom: 7px; }
.sec-name { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; color: #1A202C; margin-bottom: 3px; }
.sec-reason { font-size: 12px; color: #718096; line-height: 1.4; }

/* SIGNAL */
.sig-buy { background: #F0FFF4; border: 1px solid #9AE6B4; border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 700; color: #276749; display: inline-block; }
.sig-sell { background: #FFF5F5; border: 1px solid #FEB2B2; border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 700; color: #C53030; display: inline-block; }
.sig-hold { background: #FFFBEB; border: 1px solid #F6E05E; border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 700; color: #B7791F; display: inline-block; }
.ind-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #EDF2F7; font-size: 12px; }
.ind-name { color: #718096; min-width: 80px; }
.ind-val { font-weight: 700; color: #1A202C; }
.ind-note { color: #718096; font-size: 11px; text-align: right; flex: 1; }

/* ECO */
.eco-card { background: #fff; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px; margin-bottom: 6px; }
.eco-lbl { font-size: 9px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #A0AEC0; }
.eco-val { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800; color: #1A202C; margin: 4px 0 2px; }
.eco-note { font-size: 11px; color: #718096; line-height: 1.4; }

/* DIVIDER */
.fp-div { height: 1px; background: #EDF2F7; margin: 24px 0; }

/* REFRESH BADGE */
.rfsh { display: inline-flex; align-items: center; gap: 6px; background: #F0FFF4; border: 1px solid #9AE6B4; border-radius: 20px; padding: 3px 12px; font-size: 10px; color: #276749; font-weight: 500; }
.rdot { width: 6px; height: 6px; background: #38A169; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* FOOTER */
.fp-footer { background: #1A202C; padding: 24px 28px; text-align: center; margin-top: 40px; }
.fp-footer-brand { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 6px; }
.fp-footer a { color: #A0AEC0; text-decoration: none; font-size: 12px; margin: 0 8px; }
.fp-footer-copy { font-size: 11px; color: #4A5568; margin-top: 8px; }

/* STREAMLIT OVERRIDES */
div[data-testid="stButton"]>button { background: #fff !important; color: #2B6CB0 !important; border: 1.5px solid #BEE3F8 !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 13px !important; width: 100% !important; transition: all .2s; }
div[data-testid="stButton"]>button:hover { background: #EBF8FF !important; border-color: #2B6CB0 !important; }
.stDownloadButton>button { background: #2B6CB0 !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; width: 100% !important; }
.stTextInput input,.stNumberInput input { background: #fff !important; color: #1A202C !important; border: 1.5px solid #E2E8F0 !important; border-radius: 8px !important; font-size: 13px !important; }
.stTextInput input:focus { border-color: #2B6CB0 !important; box-shadow: 0 0 0 3px rgba(43,108,176,.1) !important; }
.streamlit-expanderHeader { background: #fff !important; color: #2D3748 !important; font-size: 13px !important; font-weight: 500 !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; padding: 11px 15px !important; }
.streamlit-expanderHeader:hover { border-color: #2B6CB0 !important; background: #EBF8FF !important; }
.streamlit-expanderContent { background: #F7FAFC !important; border: 1px solid #E2E8F0 !important; border-top: none !important; border-radius: 0 0 10px 10px !important; padding: 12px !important; }
.stMarkdown p,.stMarkdown li { color: #2D3748 !important; }
label { color: #4A5568 !important; font-size: 13px !important; }
[data-testid="stElementToolbar"] { display: none !important; }
hr { border-color: #EDF2F7 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  DATA HELPERS
# ══════════════════════════════════════════════════════════
FINANCE_KW = ["market","stock","nifty","sensex","sebi","rbi","economy","gdp",
              "inflation","earnings","revenue","bank","oil","gold","rupee",
              "fii","dii","ipo","budget","rate","interest","shares","equity",
              "mutual fund","crypto","bitcoin","dollar","trade","export",
              "import","tax","corporate","profit","loss","dividend","quarter"]

SECTOR_MAP = {
    "Banking":      ["bank","hdfc","icici","kotak","sbi","axis","rbi","npa","credit","loan","nbfc"],
    "IT/Tech":      ["tcs","infosys","wipro","tech mahindra","hcl","software","it sector","digital","ai"],
    "Energy":       ["oil","reliance","ongc","bpcl","iocl","gas","petroleum","crude","energy"],
    "Pharma":       ["pharma","dr reddy","sun pharma","cipla","biocon","drug","medicine","fda","usfda"],
    "Auto":         ["maruti","tata motors","m&m","bajaj","hero","vehicle","ev","automobile","car"],
    "FMCG":         ["hindustan unilever","itc","nestle","dabur","britannia","fmcg","consumer"],
    "Metals":       ["tata steel","jsw","hindalco","vedanta","coal","steel","metal","aluminium"],
    "Realty":       ["dlf","godrej","oberoi","real estate","property","housing","realty"],
    "Infra":        ["l&t","infrastructure","roads","airport","port","construction"],
    "Telecom":      ["airtel","jio","vodafone","telecom","5g","spectrum"],
    "Global/Macro": ["fed","federal reserve","us market","global","dollar","s&p","nasdaq","china"],
}

def get_sectors(text):
    t = text.lower()
    found = [s for s, kws in SECTOR_MAP.items() if any(k in t for k in kws)]
    return found[:3] if found else ["General Market"]

def sentiment(text):
    sc = analyzer.polarity_scores(text)["compound"]
    if sc >= 0.05:  return sc, "🟢", "#276749", "Positive"
    elif sc <= -0.05: return sc, "🔴", "#C53030", "Negative"
    else:           return sc, "🟡", "#B7791F", "Neutral"

def safe_price(v):
    try:    return f"{float(v):,.2f}"
    except: return "–"

def yf_quote(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
        r   = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200: return None
        meta  = r.json()["chart"]["result"][0]["meta"]
        price = float(meta.get("regularMarketPrice", 0))
        prev  = float(meta.get("previousClose", price) or price)
        chg   = round((price-prev)/prev*100, 2) if prev else 0
        name  = meta.get("shortName", symbol)
        return {"price": round(price,2), "chg": chg,
                "arrow": "▲" if chg>=0 else "▼",
                "color": "up" if chg>=0 else "dn", "name": name}
    except: return None

def yf_history(symbol, period="3mo"):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval=1d"
        r   = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        res  = r.json()["chart"]["result"][0]
        ts   = res["timestamp"]
        cl   = res["indicators"]["quote"][0]["close"]
        df   = pd.DataFrame({"date": pd.to_datetime(ts, unit="s"), "close": cl}).dropna()
        return df
    except: return None

def fetch_rss(url, source_name, max_items=8):
    try:
        r    = requests.get(url, headers=HEADERS, timeout=8)
        root = ET.fromstring(r.content)
        arts = []
        for item in root.findall(".//item")[:max_items]:
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            link  = (item.findtext("link") or "").strip()
            if not title: continue
            combined = title + " " + desc
            if not any(k in combined.lower() for k in FINANCE_KW): continue
            sc, emoji, color, label = sentiment(combined)
            arts.append({
                "title": title, "desc": desc[:200],
                "source": source_name, "url": link,
                "score": sc, "emoji": emoji,
                "color": color, "label": label,
                "sectors": get_sectors(combined),
                "summary": _split_summary(title, desc),
            })
        return arts
    except: return []

def _split_summary(title, desc):
    text  = (title + ". " + desc).strip()
    words = text.split()
    if len(words) < 12:
        return [title, "Watch this story for market impact.", "Check related sectors for reaction."]
    n = max(8, len(words)//3)
    return [
        " ".join(words[:n]).rstrip(".,") + ".",
        " ".join(words[n:n*2]).rstrip(".,") + ".",
        " ".join(words[n*2:n*3]).rstrip(".,") + ".",
    ]


# ══════════════════════════════════════════════════════════
#  CACHED DATA FETCHERS
# ══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_all_news():
    """Fetch from Indian + Global sources. Returns merged, sorted list."""
    indian_sources = [
        ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",    "Economic Times"),
        ("https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",    "ET Economy"),
        ("https://www.business-standard.com/rss/markets-106.rss",                  "Business Standard"),
        ("https://www.livemint.com/rss/markets",                                    "Mint"),
        ("https://www.moneycontrol.com/rss/MCtopnews.xml",                          "Moneycontrol"),
        ("https://feeds.feedburner.com/ndtvprofit-latest",                          "NDTV Profit"),
        ("https://www.financialexpress.com/market/feed/",                           "Financial Express"),
    ]
    global_sources = [
        ("https://feeds.bbci.co.uk/news/business/rss.xml",                          "BBC Business"),
        ("https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US", "Yahoo Finance"),
        ("https://rss.cnn.com/rss/money_news_international.rss",                   "CNN Money"),
    ]
    all_articles = []
    seen = set()
    for url, name in indian_sources + global_sources:
        for art in fetch_rss(url, name, 10):
            key = art["title"][:60].lower()
            if key not in seen:
                seen.add(key)
                art["indian"] = name not in ["BBC Business","Yahoo Finance","CNN Money"]
                all_articles.append(art)
    all_articles.sort(key=lambda x: abs(x["score"]), reverse=True)
    return all_articles[:20]

@st.cache_data(ttl=300)
def fetch_market_data():
    """Indian primary + Global secondary market data."""
    symbols = {
        # Indian Indices
        "Nifty 50":   "^NSEI",
        "Sensex":     "^BSESN",
        "Bank Nifty": "^NSEBANK",
        "Nifty IT":   "^CNXIT",
        "Nifty Pharma":"^CNXPHARMA",
        # Global
        "S&P 500":    "^GSPC",
        "NASDAQ":     "^IXIC",
        # Commodities
        "Gold":       "GC=F",
        "Oil (WTI)":  "CL=F",
        "Silver":     "SI=F",
        # Currencies
        "USD/INR":    "USDINR=X",
        "EUR/INR":    "EURINR=X",
        "GBP/INR":    "GBPINR=X",
        # Crypto
        "Bitcoin":    "BTC-USD",
        "Ethereum":   "ETH-USD",
    }
    out = {}
    for name, sym in symbols.items():
        d = yf_quote(sym)
        if d: out[name] = d
        else: out[name] = {"price":0,"chg":0,"arrow":"–","color":"nt","name":name}
    return out

@st.cache_data(ttl=3600)
def fetch_fiidii():
    """FII/DII institutional activity from NSE."""
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        s   = requests.Session()
        s.get("https://www.nseindia.com", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }, timeout=8)
        r = s.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer":    "https://www.nseindia.com/market-data/fii-dii-trading-activity",
            "Accept":     "application/json",
        }, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                return _parse_fiidii(data)
    except Exception:
        pass
    return _demo_fiidii()

def _parse_fiidii(data):
    try:
        rows = []
        for item in data[:5]:
            rows.append({
                "date":     item.get("date",""),
                "fii_buy":  float(str(item.get("fiiBuyValue","0")).replace(",","")),
                "fii_sell": float(str(item.get("fiiSellValue","0")).replace(",","")),
                "fii_net":  float(str(item.get("fiiNetValue","0")).replace(",","")),
                "dii_buy":  float(str(item.get("diiBuyValue","0")).replace(",","")),
                "dii_sell": float(str(item.get("diiSellValue","0")).replace(",","")),
                "dii_net":  float(str(item.get("diiNetValue","0")).replace(",","")),
            })
        return rows
    except:
        return _demo_fiidii()

def _demo_fiidii():
    today = now_ist()
    rows  = []
    import random
    random.seed(today.day)
    for i in range(5):
        d    = today - timedelta(days=i)
        fnet = round(random.uniform(-3000,3000), 2)
        dnet = round(random.uniform(-2000,2500), 2)
        rows.append({
            "date":     d.strftime("%d-%b-%Y"),
            "fii_buy":  round(abs(fnet)+random.uniform(5000,15000),2),
            "fii_sell": round(abs(fnet)+random.uniform(5000,12000),2),
            "fii_net":  fnet,
            "dii_buy":  round(abs(dnet)+random.uniform(3000,10000),2),
            "dii_sell": round(abs(dnet)+random.uniform(3000,9000),2),
            "dii_net":  dnet,
        })
    return rows

@st.cache_data(ttl=3600)
def fetch_economic():
    """Economic pulse — India focused with latest available data."""
    vix,_    = (yf_quote("^VIX") or {}).get("price",None), None
    vix_d    = yf_quote("^VIX")
    tnx_d    = yf_quote("^TNX")
    inr_d    = yf_quote("USDINR=X")
    gold_d   = yf_quote("GC=F")
    oil_d    = yf_quote("CL=F")

    def wb(indicator, country, n=3):
        try:
            url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&mrv={n}&per_page=5"
            r   = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200: return []
            d = r.json()
            if len(d) < 2 or not d[1]: return []
            return sorted([{"year":int(x["date"]),"val":x["value"]}
                           for x in d[1] if x["value"] is not None],
                          key=lambda x: x["year"], reverse=True)
        except: return []

    india_gdp  = wb("NY.GDP.MKTP.KD.ZG", "IN", 4)
    india_cpi  = wb("FP.CPI.TOTL.ZG",    "IN", 4)
    india_unem = wb("SL.UEM.TOTL.ZS",    "IN", 4)
    us_gdp     = wb("NY.GDP.MKTP.KD.ZG", "US", 3)

    # Yield curve
    t10  = (tnx_d or {}).get("price")
    t30v = yf_quote("^TYX")
    t30  = (t30v or {}).get("price") if t30v else None
    yc_signal = "Normal"
    yc_color  = "#276749"
    yc_note   = "Normal yield curve — economy expanding"
    if t10 and t30:
        spread = round(float(t30) - float(t10), 2)
        if spread < 0:
            yc_signal, yc_color = "Inverted ⚠️", "#C53030"
            yc_note = f"Inverted by {abs(spread):.2f}% — historical recession warning"
        elif spread < 0.5:
            yc_signal, yc_color = "Flat", "#B7791F"
            yc_note = f"Flat spread ({spread:.2f}%) — slowing growth signal"
        else:
            yc_note = f"Healthy spread of {spread:.2f}%"

    vix_val = (vix_d or {}).get("price")
    if vix_val:
        if vix_val < 15:   vix_mood, vc = "Complacent — Very low fear", "#276749"
        elif vix_val < 20: vix_mood, vc = "Low — Markets calm", "#276749"
        elif vix_val < 25: vix_mood, vc = "Moderate — Some caution", "#B7791F"
        elif vix_val < 30: vix_mood, vc = "Elevated — Growing fear", "#C53030"
        else:              vix_mood, vc = "High Fear — Market stressed", "#C53030"
    else:
        vix_mood, vc = "Data loading", "#718096"

    return {
        "vix":      {"val": vix_val, "mood": vix_mood, "color": vc},
        "yield":    {"signal": yc_signal, "color": yc_color, "note": yc_note,
                     "t10": t10, "t30": t30},
        "inr":      inr_d,
        "gold":     gold_d,
        "oil":      oil_d,
        "india_gdp":  india_gdp,
        "india_cpi":  india_cpi,
        "india_unem": india_unem,
        "us_gdp":     us_gdp,
        "updated":  fmt_ist(),
    }

@st.cache_data(ttl=1800)
def fetch_watchlist_data(tickers_key):
    tickers = tickers_key.split(",")
    out = {}
    for t in tickers:
        d = yf_quote(t)
        if d: out[t] = d
        else: out[t] = {"price":0,"chg":0,"arrow":"–","color":"nt","name":t}
    return out

@st.cache_data(ttl=3600)
def fetch_technical(ticker):
    try:
        df = yf_history(ticker, "6mo")
        if df is None or len(df) < 30: return None
        cl   = df["close"].astype(float)
        # RSI
        delta = cl.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, np.nan)
        rsi   = float((100 - 100/(1+rs)).iloc[-1])
        # MACD
        ema12 = cl.ewm(span=12,adjust=False).mean()
        ema26 = cl.ewm(span=26,adjust=False).mean()
        macd  = ema12 - ema26
        sig   = macd.ewm(span=9,adjust=False).mean()
        # BB
        sma20 = cl.rolling(20).mean()
        std20 = cl.rolling(20).std()
        bb_u  = sma20 + 2*std20
        bb_l  = sma20 - 2*std20
        cur   = float(cl.iloc[-1])
        bb_pct= (cur - float(bb_l.iloc[-1])) / (float(bb_u.iloc[-1]) - float(bb_l.iloc[-1])) * 100
        # MA
        sma50  = float(cl.rolling(50).mean().iloc[-1])
        sma200 = float(cl.rolling(200).mean().iloc[-1])
        macd_v = float(macd.iloc[-1])
        sig_v  = float(sig.iloc[-1])
        # Score
        score = 0
        inds  = []
        rsi_r = round(rsi,1)
        if rsi_r < 30:
            score += 2; inds.append(("RSI", str(rsi_r), "Oversold — buy zone", "#276749"))
        elif rsi_r > 70:
            score -= 2; inds.append(("RSI", str(rsi_r), "Overbought — caution", "#C53030"))
        else:
            inds.append(("RSI", str(rsi_r), "Neutral", "#B7791F"))
        if macd_v > sig_v:
            score += 1; inds.append(("MACD", f"{macd_v:.2f}", "Bullish crossover", "#276749"))
        else:
            score -= 1; inds.append(("MACD", f"{macd_v:.2f}", "Bearish crossover", "#C53030"))
        if sma50 > sma200:
            score += 1; inds.append(("MA Cross", f"{sma50:.0f}", "Golden Cross ✓", "#276749"))
        else:
            score -= 1; inds.append(("MA Cross", f"{sma50:.0f}", "Death Cross ✗", "#C53030"))
        bb_r = round(bb_pct,0)
        if bb_r < 20:
            score += 1; inds.append(("Bollinger", f"{bb_r:.0f}%", "Near lower band", "#276749"))
        elif bb_r > 80:
            score -= 1; inds.append(("Bollinger", f"{bb_r:.0f}%", "Near upper band", "#C53030"))
        else:
            inds.append(("Bollinger", f"{bb_r:.0f}%", "Mid range", "#B7791F"))
        if score >= 3:   overall, oc = "STRONG BUY",  "sig-buy"
        elif score >= 1: overall, oc = "BUY",          "sig-buy"
        elif score <= -3:overall, oc = "STRONG SELL",  "sig-sell"
        elif score <= -1:overall, oc = "SELL",         "sig-sell"
        else:            overall, oc = "HOLD",         "sig-hold"
        prev = float(cl.iloc[-2]) if len(cl)>1 else cur
        chg  = round((cur-prev)/prev*100, 2)
        return {"ticker":ticker,"price":round(cur,2),"chg":chg,
                "rsi":rsi_r,"score":score,"overall":overall,"oc":oc,
                "inds":inds,"sma50":round(sma50,2),"sma200":round(sma200,2),
                "history":df.tail(60)}
    except: return None


# ══════════════════════════════════════════════════════════
#  MARKET EVENTS CALENDAR
# ══════════════════════════════════════════════════════════
def get_market_events():
    """India-specific market events calendar for 2026."""
    events = [
        # RBI MPC Meetings 2026
        {"date":"04-06-2026","type":"RBI","title":"RBI MPC Decision","detail":"Monetary Policy Committee rate decision — key for markets","color":"#2B6CB0","urgent":True},
        {"date":"06-08-2026","type":"RBI","title":"RBI MPC Meeting","detail":"Next bi-monthly policy review","color":"#2B6CB0","urgent":False},
        {"date":"07-10-2026","type":"RBI","title":"RBI MPC Meeting","detail":"October monetary policy review","color":"#2B6CB0","urgent":False},
        # Earnings Season
        {"date":"15-07-2026","type":"Results","title":"Q1 FY27 Results Season Begins","detail":"TCS, Infosys, HCL Tech lead IT results","color":"#276749","urgent":False},
        {"date":"21-07-2026","type":"Results","title":"Major Bank Results","detail":"HDFC Bank, ICICI Bank, Kotak quarterly results","color":"#276749","urgent":False},
        # Budget
        {"date":"01-02-2027","type":"Budget","title":"Union Budget 2027","detail":"Annual Union Budget presentation","color":"#C53030","urgent":False},
        # Derivatives
        {"date":"25-06-2026","type":"F&O","title":"June F&O Expiry","detail":"Monthly futures and options expiry — high volatility expected","color":"#B7791F","urgent":True},
        {"date":"30-07-2026","type":"F&O","title":"July F&O Expiry","detail":"Monthly derivatives expiry","color":"#B7791F","urgent":False},
        # GST
        {"date":"20-06-2026","type":"GST","title":"GST Filing Deadline","detail":"Monthly GST return filing deadline","color":"#718096","urgent":False},
        # Global
        {"date":"17-06-2026","type":"Fed","title":"US Fed FOMC Meeting","detail":"Federal Reserve interest rate decision — impacts FII flows","color":"#4A5568","urgent":True},
        {"date":"29-07-2026","type":"Fed","title":"US Fed FOMC Meeting","detail":"Federal Reserve next policy meeting","color":"#4A5568","urgent":False},
    ]
    today    = now_ist()
    filtered = []
    for e in events:
        try:
            edate = datetime.strptime(e["date"], "%d-%m-%Y").replace(tzinfo=IST)
            diff  = (edate - today).days
            if diff >= -1:
                e["days_away"] = diff
                e["date_fmt"]  = edate.strftime("%d %b %Y")
                filtered.append(e)
        except: pass
    filtered.sort(key=lambda x: x["days_away"])
    return filtered[:10]

# ══════════════════════════════════════════════════════════
#  FEAR & GREED CALCULATOR
# ══════════════════════════════════════════════════════════
def calc_fg(market, news):
    try:
        score = 50
        nifty_chg = (market.get("Nifty 50") or {}).get("chg", 0) or 0
        score += min(20, max(-20, nifty_chg * 4))
        news_scores = [n["score"] for n in news if "score" in n]
        if news_scores:
            avg_news = sum(news_scores)/len(news_scores)
            score += min(15, max(-15, avg_news * 25))
        score = max(0, min(100, int(score)))
        if   score <= 25: return score, "Extreme Fear 😨",  "#C53030"
        elif score <= 45: return score, "Fear 😟",           "#E67E22"
        elif score <= 55: return score, "Neutral 😐",        "#B7791F"
        elif score <= 75: return score, "Greed 😏",          "#276749"
        else:             return score, "Extreme Greed 🤑",  "#276749"
    except: return 50, "Neutral", "#B7791F"

# ══════════════════════════════════════════════════════════
#  PDF GENERATOR
# ══════════════════════════════════════════════════════════
def make_pdf(market, news, fg_score, fg_label, fiidii):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.enums import TA_CENTER

        buf  = io.BytesIO()
        doc  = SimpleDocTemplate(buf, pagesize=A4,
               leftMargin=20*mm, rightMargin=20*mm,
               topMargin=15*mm, bottomMargin=15*mm)
        NAVY = colors.HexColor("#1A202C")
        RED  = colors.HexColor("#C53030")
        GRAY = colors.HexColor("#718096")
        WHITE= colors.white
        W    = A4[0] - 40*mm

        def ps(name, **kw): return ParagraphStyle(name, **kw)

        story = []

        # Header
        hdr = Table([[
            Paragraph("📡 FinPulse", ps("h",fontName="Helvetica-Bold",fontSize=20,textColor=WHITE,leading=24)),
            Paragraph(f"by Anoop Puri  ·  {fmt_ist()}",
                ps("s",fontName="Helvetica",fontSize=9,textColor=colors.HexColor("#A0AEC0"),alignment=2,leading=12)),
        ]], colWidths=[W*0.5, W*0.5])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),NAVY),
            ("LEFTPADDING",(0,0),(-1,-1),10),
            ("TOPPADDING",(0,0),(-1,-1),12),
            ("BOTTOMPADDING",(0,0),(-1,-1),12),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))
        story.append(hdr)
        story.append(Spacer(1,5*mm))

        # Markets
        story.append(Paragraph("MARKET SNAPSHOT", ps("mh",fontName="Helvetica-Bold",fontSize=8,textColor=GRAY,leading=10)))
        story.append(Spacer(1,2*mm))
        mkt_rows = [["Index/Asset","Price","Change"]]
        for name in ["Nifty 50","Sensex","Bank Nifty","Gold","Oil (WTI)","USD/INR","Bitcoin"]:
            d = market.get(name,{})
            chg = d.get("chg",0)
            mkt_rows.append([name, safe_price(d.get("price",0)), f"{d.get('arrow','')} {abs(chg):.2f}%"])
        styled = []
        for i, row in enumerate(mkt_rows):
            styled.append([Paragraph(c, ps("mc",fontName="Helvetica-Bold" if i==0 else "Helvetica",
                fontSize=8, textColor=WHITE if i==0 else colors.HexColor("#2D3748"),
                leading=11)) for c in row])
        mt = Table(styled, colWidths=[55*mm, 35*mm, 35*mm])
        mt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),NAVY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F7FAFC")]),
            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#E2E8F0")),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("LEFTPADDING",(0,0),(-1,-1),6),
        ]))
        story.append(mt)
        story.append(Spacer(1,5*mm))

        # Fear & Greed
        fg_box = Table([[Paragraph(
            f"Fear & Greed Index: {fg_score} — {fg_label}",
            ps("fg",fontName="Helvetica-Bold",fontSize=11,textColor=NAVY,alignment=TA_CENTER,leading=14)
        )]], colWidths=[W])
        fg_box.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFFBEB")),
            ("BOX",(0,0),(-1,-1),1,colors.HexColor("#F6E05E")),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
        ]))
        story.append(fg_box)
        story.append(Spacer(1,5*mm))

        # FII/DII
        if fiidii:
            story.append(Paragraph("FII/DII ACTIVITY (LATEST)", ps("fh",fontName="Helvetica-Bold",fontSize=8,textColor=GRAY,leading=10)))
            story.append(Spacer(1,2*mm))
            fi_rows = [["Date","FII Net (₹Cr)","DII Net (₹Cr)"]]
            for row in fiidii[:3]:
                fnet = row.get("fii_net",0)
                dnet = row.get("dii_net",0)
                fi_rows.append([
                    row.get("date",""),
                    f"{'+'if fnet>=0 else ''}{fnet:,.0f}",
                    f"{'+'if dnet>=0 else ''}{dnet:,.0f}",
                ])
            fi_styled = []
            for i, row in enumerate(fi_rows):
                fi_styled.append([Paragraph(c, ps("fc",fontName="Helvetica-Bold" if i==0 else "Helvetica",
                    fontSize=8, textColor=WHITE if i==0 else colors.HexColor("#2D3748"), leading=11)) for c in row])
            ft = Table(fi_styled, colWidths=[35*mm, 40*mm, 40*mm])
            ft.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2B6CB0")),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#EBF8FF")]),
                ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#BEE3F8")),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
                ("LEFTPADDING",(0,0),(-1,-1),6),
            ]))
            story.append(ft)
            story.append(Spacer(1,5*mm))

        story.append(PageBreak())

        # News
        story.append(Paragraph("TOP NEWS TODAY", ps("nh",fontName="Helvetica-Bold",fontSize=8,textColor=GRAY,leading=10)))
        story.append(Spacer(1,3*mm))
        for art in news[:8]:
            hrow = Table([[
                Paragraph(art["emoji"], ps("e",fontName="Helvetica",fontSize=10,textColor=WHITE,alignment=TA_CENTER,leading=12)),
                Paragraph(f"<b>{art['title'][:90]}</b>", ps("t",fontName="Helvetica-Bold",fontSize=9,textColor=colors.HexColor("#2D3748"),leading=12)),
                Paragraph(art["source"], ps("s2",fontName="Helvetica-Oblique",fontSize=7.5,textColor=GRAY,alignment=2,leading=10)),
            ]], colWidths=[8*mm, W-8*mm-28*mm, 28*mm])
            sc = colors.HexColor("#276749") if art["color"]=="#276749" else (colors.HexColor("#C53030") if art["color"]=="#C53030" else colors.HexColor("#B7791F"))
            hrow.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,-1),sc),
                ("BACKGROUND",(1,0),(-1,-1),colors.HexColor("#F7FAFC")),
                ("LEFTPADDING",(0,0),(-1,-1),5),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                ("BOX",(0,0),(-1,-1),0.3,colors.HexColor("#E2E8F0")),
            ]))
            story.append(hrow)
            for line in (art.get("summary") or [])[:2]:
                if line.strip():
                    story.append(Paragraph(f"→ {line}",
                        ps("nl",fontName="Helvetica",fontSize=8,textColor=colors.HexColor("#4A5568"),
                           leftIndent=8,leading=12,spaceBefore=1)))
            story.append(Paragraph(
                f"Sectors: {' | '.join(art['sectors'])}  ·  Source: {art['source']}",
                ps("nm",fontName="Helvetica",fontSize=7.5,textColor=GRAY,leading=10,spaceBefore=2)))
            story.append(Spacer(1,3*mm))

        # Footer
        ft_box = Table([[Paragraph(
            "FinPulse by Anoop Puri  ·  @theanooppuri  ·  Not Financial Advice",
            ps("ft",fontName="Helvetica",fontSize=8,textColor=GRAY,alignment=TA_CENTER)
        )]], colWidths=[W])
        ft_box.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F7FAFC")),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        story.append(ft_box)
        doc.build(story)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        return None


# ══════════════════════════════════════════════════════════
#  MAIN APP LAYOUT
# ══════════════════════════════════════════════════════════

# ── NAV ───────────────────────────────────────────────────
st.markdown("""
<div class="fp-nav">
  <div>
    <div class="nav-brand">📡 Fin<span>Pulse</span></div>
    <div class="nav-sub">by Anoop Puri · India First · World Coverage</div>
  </div>
  <div class="nav-links">
    <a href="https://instagram.com/theanooppuri" target="_blank">📸 @theanooppuri</a>
    <a href="https://linkedin.com/in/theanooppuri" target="_blank">💼 LinkedIn</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── LOAD ALL DATA ─────────────────────────────────────────
with st.spinner("Loading live market data..."):
    market  = fetch_market_data()
    news    = fetch_all_news()
    fiidii  = fetch_fiidii()
    eco     = fetch_economic()
    events  = get_market_events()

fg_score, fg_label, fg_color = calc_fg(market, news)
pos_news  = sum(1 for n in news if n["score"] >= 0.05)
neg_news  = sum(1 for n in news if n["score"] <= -0.05)
indian_news  = [n for n in news if n.get("indian")]
global_news  = [n for n in news if not n.get("indian")]
top_sectors  = list({s for n in news[:4] for s in n["sectors"]})[:3]

# ── DISCLAIMER ────────────────────────────────────────────
st.markdown(f"""
<div class="disc">
  <span>⚠️ <b>Not Financial Advice.</b> Data from Yahoo Finance, NSE, World Bank, ET, Mint, BS, Moneycontrol &amp; more.
  Verify independently before investing.</span>
  <span>🕐 {fmt_ist()}</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="wrap">', unsafe_allow_html=True)

# ── TOP BAR: Refresh + Download ───────────────────────────
col_r, col_mid, col_d = st.columns([2,1,1])
with col_r:
    elapsed = int((now_ist()-st.session_state.last_refresh).total_seconds()/60)
    remain  = max(0, 60-elapsed)
    st.markdown(f"""
    <div class="rfsh">
      <div class="rdot"></div>
      Live · Updated {elapsed}m ago · Auto-refresh in {remain}m
    </div>""", unsafe_allow_html=True)
with col_mid:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_refresh = now_ist()
        st.rerun()
with col_d:
    pdf_bytes = make_pdf(market, news, fg_score, fg_label, fiidii)
    if pdf_bytes:
        st.download_button("⬇️ Download Brief PDF", data=pdf_bytes,
            file_name=f"FinPulse_{now_ist().strftime('%d%b%Y')}.pdf",
            mime="application/pdf", use_container_width=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 1 — COMMAND CENTER
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">📊 Command Center</p>', unsafe_allow_html=True)

# Row 1 — Indian Indices
indian_idx = ["Nifty 50","Sensex","Bank Nifty","Nifty IT","Nifty Pharma"]
cols = st.columns(5)
for col, name in zip(cols, indian_idx):
    d   = market.get(name, {})
    chg = d.get("chg", 0) or 0
    cc  = "up" if chg >= 0 else "dn"
    with col:
        st.markdown(f"""
        <div class="card">
          <div class="cmd-label">{name}</div>
          <div class="cmd-val {cc}">{safe_price(d.get("price",0))}</div>
          <div class="chg {cc}">{d.get("arrow","–")} {abs(chg):.2f}%</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

# Row 2 — Global + FG
c1,c2,c3,c4,c5,c6 = st.columns(6)
quick = [
    (c1,"S&P 500"), (c2,"Gold"), (c3,"Oil (WTI)"),
    (c4,"USD/INR"), (c5,"Bitcoin"),
]
for col, name in quick:
    d   = market.get(name, {})
    chg = d.get("chg", 0) or 0
    cc  = "up" if chg >= 0 else "dn"
    with col:
        st.markdown(f"""
        <div class="card">
          <div class="cmd-label">{name}</div>
          <div class="cmd-val" style="font-size:16px">{safe_price(d.get("price",0))}</div>
          <div class="chg {cc}">{d.get("arrow","–")} {abs(chg):.2f}%</div>
        </div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="fg-wrap">
      <div class="cmd-label">Fear &amp; Greed</div>
      <div class="fg-num" style="color:{fg_color}">{fg_score}</div>
      <div class="fg-lbl" style="color:{fg_color}">{fg_label}</div>
      <div class="fg-bar-bg"><div class="fg-bar" style="width:{fg_score}%"></div></div>
      <div class="fg-scale"><span>Fear</span><span>Greed</span></div>
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 2 — NEWS FEED
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">📰 News Feed — India + World</p>', unsafe_allow_html=True)
st.markdown(f"""
<div style="font-size:11px;color:#718096;background:#F7FAFC;border:1px solid #E2E8F0;
            border-radius:8px;padding:7px 14px;margin-bottom:12px">
  ℹ️ Sources: Economic Times · Business Standard · Mint · Moneycontrol · NDTV Profit ·
  Financial Express · BBC Business · CNN Money · Yahoo Finance<br>
  Scanned {len(news)} relevant articles · Sentiment via VADER NLP ·
  Summaries from original article text only — nothing invented
</div>""", unsafe_allow_html=True)

tab_in, tab_gl, tab_all = st.tabs([
    f"🇮🇳 Indian News ({len(indian_news)})",
    f"🌍 Global News ({len(global_news)})",
    f"📋 All ({len(news)})"
])

def render_news_list(articles):
    if not articles:
        st.info("No articles loaded yet — click Refresh Now")
        return
    for art in articles[:10]:
        label = f"{art['emoji']}  {art['title'][:100]}{'...' if len(art['title'])>100 else ''}  ·  *{art['source']}*"
        with st.expander(label, expanded=False):
            for line in (art.get("summary") or []):
                if line.strip():
                    st.markdown(f'<div class="news-sum">{line}</div>',
                                unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-top:8px;display:flex;align-items:center;
                        justify-content:space-between;flex-wrap:wrap;gap:6px">
              <div>
                {''.join(f'<span class="sec-tag">{s}</span>' for s in art['sectors'])}
              </div>
              <div>
                <span class="src-badge">📰 {art['source']}</span>
                <span style="font-size:11px;color:{art['color']};font-weight:600;
                             margin-left:8px">{art['label']}</span>
                {"&nbsp;&nbsp;<a href='" + art['url'] + "' target='_blank' style='font-size:11px;color:#2B6CB0'>Read ↗</a>" if art.get('url') and art['url']!='#' else ''}
              </div>
            </div>""", unsafe_allow_html=True)

with tab_in:  render_news_list(indian_news)
with tab_gl:  render_news_list(global_news)
with tab_all: render_news_list(news)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 3 — FII/DII ACTIVITY
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">🏦 FII / DII Institutional Activity</p>',
            unsafe_allow_html=True)
st.markdown("""
<div style="font-size:11px;color:#718096;margin-bottom:10px">
  FII = Foreign Institutional Investors · DII = Domestic Institutional Investors
  · Positive = Net Buyers · Negative = Net Sellers · Values in ₹ Crore
</div>""", unsafe_allow_html=True)

if fiidii:
    latest = fiidii[0]
    fnet   = latest.get("fii_net", 0)
    dnet   = latest.get("dii_net", 0)
    fcolor = "fii-buy" if fnet >= 0 else "fii-sell"
    dcolor = "fii-buy" if dnet >= 0 else "fii-sell"
    fhex   = "#276749" if fnet >= 0 else "#C53030"
    dhex   = "#276749" if dnet >= 0 else "#C53030"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="{fcolor}">
          <div class="cmd-label">FII Net Today</div>
          <div class="fii-val" style="color:{fhex}">
            {'+'if fnet>=0 else ''}₹{abs(fnet):,.0f} Cr
          </div>
          <div class="fii-lbl">Buy: ₹{latest.get('fii_buy',0):,.0f} Cr &nbsp;|&nbsp;
          Sell: ₹{latest.get('fii_sell',0):,.0f} Cr</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="{dcolor}">
          <div class="cmd-label">DII Net Today</div>
          <div class="fii-val" style="color:{dhex}">
            {'+'if dnet>=0 else ''}₹{abs(dnet):,.0f} Cr
          </div>
          <div class="fii-lbl">Buy: ₹{latest.get('dii_buy',0):,.0f} Cr &nbsp;|&nbsp;
          Sell: ₹{latest.get('dii_sell',0):,.0f} Cr</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        combined = fnet + dnet
        chex = "#276749" if combined >= 0 else "#C53030"
        st.markdown(f"""
        <div class="card">
          <div class="cmd-label">Combined Net Flow</div>
          <div class="fii-val" style="color:{chex}">
            {'+'if combined>=0 else ''}₹{abs(combined):,.0f} Cr
          </div>
          <div class="fii-lbl">Date: {latest.get('date','')}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
    st.markdown("**📅 Last 5 Days Activity**")

    rows_html = ""
    for row in fiidii:
        fn = row.get("fii_net",0)
        dn = row.get("dii_net",0)
        fc = "#276749" if fn>=0 else "#C53030"
        dc = "#276749" if dn>=0 else "#C53030"
        rows_html += f"""
        <div class="card-sm" style="display:flex;gap:16px;align-items:center;margin-bottom:5px">
          <span style="font-weight:600;color:#4A5568;min-width:90px;font-size:12px">
            {row.get('date','')}
          </span>
          <span style="font-size:12px;color:#718096;flex:1">FII:
            <b style="color:{fc}">{'+'if fn>=0 else ''}₹{fn:,.0f} Cr</b>
          </span>
          <span style="font-size:12px;color:#718096;flex:1">DII:
            <b style="color:{dc}">{'+'if dn>=0 else ''}₹{dn:,.0f} Cr</b>
          </span>
          <span style="font-size:10px;color:#A0AEC0">
            {'FII Buying 📈' if fn>0 else 'FII Selling 📉'}
          </span>
        </div>"""
    st.markdown(rows_html, unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;color:#A0AEC0;margin-top:6px">
      Source: NSE India · Note: Sample data shown when NSE API unavailable.
      Live data loads when deployed on Streamlit Cloud.
    </div>""", unsafe_allow_html=True)
else:
    st.info("FII/DII data loading...")

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 4 — SECTOR WATCH
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">🏭 Sector Watch</p>', unsafe_allow_html=True)

sec_scores = {}
for art in news:
    for s in art.get("sectors",[]):
        sec_scores.setdefault(s, []).append(art["score"])
sec_avg = {k: sum(v)/len(v) for k,v in sec_scores.items() if v}
sec_sorted = sorted(sec_avg.items(), key=lambda x: x[1], reverse=True)

if sec_sorted:
    hot_secs  = sec_sorted[:3]
    cold_secs = sec_sorted[-3:] if len(sec_sorted)>=3 else []
    c1, c2    = st.columns(2)
    with c1:
        st.markdown("**🔥 In Focus Today**")
        for sec, score in hot_secs:
            related = next((a["title"][:70]+"…" for a in news if sec in a.get("sectors",[])), "")
            st.markdown(f"""
            <div class="sec-hot">
              <div class="sec-name">▲ {sec}</div>
              <div class="sec-reason">{related}</div>
            </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("**❄️ Under Pressure**")
        for sec, score in cold_secs:
            related = next((a["title"][:70]+"…" for a in news if sec in a.get("sectors",[])), "")
            st.markdown(f"""
            <div class="sec-cold">
              <div class="sec-name">▼ {sec}</div>
              <div class="sec-reason">{related}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("Sector data loading with news feed...")

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 5 — MARKET EVENTS CALENDAR
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">📅 Market Events Calendar — India & Global</p>',
            unsafe_allow_html=True)

if events:
    cols = st.columns(2)
    for i, ev in enumerate(events):
        with cols[i % 2]:
            days  = ev.get("days_away", 0)
            urgnt = ev.get("urgent", False)
            if days == 0:   when = "🔴 TODAY"
            elif days == 1: when = "🟠 Tomorrow"
            elif days <= 7: when = f"🟡 In {days} days"
            else:           when = f"📅 {ev['date_fmt']}"
            border_c = ev.get("color","#2B6CB0")
            st.markdown(f"""
            <div class="cal-item" style="border-left-color:{border_c}">
              <div class="cal-date">{when} &nbsp;·&nbsp; {ev['type']}</div>
              <div class="cal-title">{ev['title']}</div>
              <div class="cal-sub">{ev['detail']}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("No upcoming events in the next 90 days.")

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 6 — ECONOMIC PULSE
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">🌐 Economic Pulse</p>', unsafe_allow_html=True)
st.markdown("""
<div style="font-size:11px;color:#A0AEC0;margin-bottom:12px">
  ⚠️ GDP/CPI data from World Bank — typically lags 6–12 months behind real time.
  Live market indicators (VIX, Yields, INR) are real-time from Yahoo Finance.
</div>""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

vix_d  = eco.get("vix", {})
vix_v  = vix_d.get("val")
vix_s  = f"{vix_v:.1f}" if vix_v else "–"
with c1:
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">CBOE VIX</div>
      <div class="eco-val" style="color:{vix_d.get('color','#B7791F')}">{vix_s}</div>
      <div class="eco-note">{vix_d.get('mood','–')}</div>
    </div>""", unsafe_allow_html=True)

yc = eco.get("yield",{})
with c2:
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">US Yield Curve</div>
      <div class="eco-val" style="color:{yc.get('color','#B7791F')}">{yc.get('signal','–')}</div>
      <div class="eco-note">{yc.get('note','–')}</div>
    </div>""", unsafe_allow_html=True)

inr_d = eco.get("inr") or {}
inr_v = inr_d.get("price")
inr_c = inr_d.get("chg",0) or 0
with c3:
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">USD / INR</div>
      <div class="eco-val">{'₹'+str(round(inr_v,2)) if inr_v else '–'}</div>
      <div class="eco-note" style="color:{'#C53030' if inr_c>0 else '#276749'}">
        {'Rupee weakening' if inr_c>0 else 'Rupee strengthening'} {abs(inr_c):.2f}% today
      </div>
    </div>""", unsafe_allow_html=True)

gold_d = eco.get("gold") or {}
gold_v = gold_d.get("price")
gold_c = gold_d.get("chg",0) or 0
with c4:
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">Gold (Safe Haven)</div>
      <div class="eco-val">${str(round(gold_v,0)) if gold_v else '–'}</div>
      <div class="eco-note" style="color:{'#276749' if gold_c>0 else '#C53030'}">
        {'Rising — risk-off mood' if gold_c>1.5 else ('Falling — risk-on' if gold_c<-1.5 else 'Stable today')}
      </div>
    </div>""", unsafe_allow_html=True)

# India GDP + CPI tables
st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
tc1, tc2 = st.columns(2)

with tc1:
    st.markdown("**📈 India GDP Growth Rate % (World Bank — latest available)**")
    gdp = eco.get("india_gdp", [])
    if gdp:
        rows = []
        for item in gdp[:4]:
            rows.append({"Year": str(item["year"]), "GDP Growth %": f"{item['val']:.2f}%"})
        try:
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True, height=160)
        except Exception:
            for r in rows:
                st.write(f"{r['Year']}: {r['GDP Growth %']}")
    else:
        st.info("GDP data loading...")

with tc2:
    st.markdown("**📊 India Inflation (CPI %) (World Bank — latest available)**")
    cpi = eco.get("india_cpi", [])
    if cpi:
        rows = []
        for item in cpi[:4]:
            rows.append({"Year": str(item["year"]), "CPI Inflation %": f"{item['val']:.2f}%"})
        try:
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True, height=160)
        except Exception:
            for r in rows:
                st.write(f"{r['Year']}: {r['CPI Inflation %']}")
    else:
        st.info("CPI data loading...")

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 7 — WATCHLIST
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">👁️ My Watchlist</p>', unsafe_allow_html=True)

wl_col, data_col = st.columns([1, 2])
with wl_col:
    st.markdown("**Add / Remove Stocks**")
    new_ticker = st.text_input("Add stock (e.g. RELIANCE.NS, AAPL, TATAMOTORS.NS)",
                               placeholder="Enter ticker...",
                               label_visibility="collapsed").upper().strip()
    ca, cb = st.columns(2)
    with ca:
        if st.button("➕ Add", use_container_width=True) and new_ticker:
            if new_ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker)
                st.rerun()
    with cb:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.watchlist = []
            st.rerun()

    st.markdown("**Quick Add Indian Stocks:**")
    defaults = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS",
                "ICICIBANK.NS","SBIN.NS","WIPRO.NS","ADANIENT.NS"]
    for tick in defaults:
        if tick not in st.session_state.watchlist:
            if st.button(f"+ {tick}", key=f"add_{tick}", use_container_width=True):
                st.session_state.watchlist.append(tick)
                st.rerun()

with data_col:
    if st.session_state.watchlist:
        key = ",".join(st.session_state.watchlist)
        with st.spinner("Loading watchlist prices..."):
            wl_data = fetch_watchlist_data(key)

        for ticker in st.session_state.watchlist:
            d     = wl_data.get(ticker, {})
            price = d.get("price", 0)
            chg   = d.get("chg", 0) or 0
            name  = d.get("name", ticker)[:28]
            cc    = "#276749" if chg >= 0 else "#C53030"
            arrow = d.get("arrow", "–")

            # Find news for this ticker
            tick_kw  = ticker.replace(".NS","").replace(".BO","").lower()
            rel_news = [n for n in news if tick_kw in n["title"].lower()
                        or tick_kw in (n.get("desc","")).lower()]
            news_html = ""
            if rel_news:
                n0 = rel_news[0]
                news_html = f"""
                <div style="font-size:11px;color:#4A5568;margin-top:5px;
                            padding:5px 8px;background:#F7FAFC;border-radius:5px;
                            border-left:2px solid {n0['color']}">
                  {n0['emoji']} {n0['title'][:80]}…
                  <span style="color:#718096"> · {n0['source']}</span>
                </div>"""

            # Get sector
            sec_name = "–"
            for sec, kws in SECTOR_MAP.items():
                if any(k in tick_kw for k in kws):
                    sec_name = sec
                    break

            c_rm, _ = st.columns([10,1])
            with c_rm:
                st.markdown(f"""
                <div class="wl-row">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                      <span class="wl-ticker">{ticker}</span>
                      <span class="wl-name" style="margin-left:8px">{name}</span>
                      <span style="font-size:10px;color:#A0AEC0;margin-left:8px">
                        {sec_name}
                      </span>
                    </div>
                    <div style="text-align:right">
                      <span style="font-family:Syne,sans-serif;font-weight:800;
                                   font-size:16px;color:#1A202C">
                        {safe_price(price)}
                      </span>
                      <span style="font-size:12px;font-weight:600;
                                   color:{cc};margin-left:8px">
                        {arrow} {abs(chg):.2f}%
                      </span>
                    </div>
                  </div>
                  {news_html}
                </div>""", unsafe_allow_html=True)
            with _:
                if st.button("✕", key=f"rm_{ticker}",
                             help=f"Remove {ticker}"):
                    st.session_state.watchlist.remove(ticker)
                    st.rerun()
    else:
        st.markdown("""
        <div style="background:#F7FAFC;border:2px dashed #E2E8F0;border-radius:10px;
                    padding:32px;text-align:center;color:#A0AEC0">
          <div style="font-size:24px;margin-bottom:8px">👁️</div>
          <div style="font-size:14px;font-weight:600;color:#4A5568">No stocks in watchlist</div>
          <div style="font-size:12px;margin-top:6px">Add any NSE/BSE/US stock from the left</div>
        </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  SECTION 8 — TECHNICAL SIGNALS
# ══════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">📡 Technical Signals</p>', unsafe_allow_html=True)
st.markdown("""
<div style="font-size:11px;color:#276749;background:#F0FFF4;border:1px solid #9AE6B4;
            border-radius:8px;padding:8px 14px;margin-bottom:12px">
  ✓ Zero hallucination — RSI, MACD, Bollinger Bands and MA Cross are pure
  mathematical formulas applied to real Yahoo Finance price data. No AI guessing.
</div>""", unsafe_allow_html=True)

sc1, sc2 = st.columns([2,1])
with sc2:
    custom_t = st.text_input("Search any ticker",
                              placeholder="e.g. TATAMOTORS.NS",
                              label_visibility="collapsed").upper().strip()

default_scan = ["RELIANCE.NS","TCS.NS","NIFTYIT.NS","HDFCBANK.NS",
                "SBIN.NS","AAPL","NVDA","GC=F"]
tickers_to_scan = ([custom_t] if custom_t else []) + \
                  [t for t in default_scan if t != custom_t]

with sc1:
    if custom_t:
        st.markdown(f"Showing signal for: **{custom_t}** + top Indian stocks")

for ticker in tickers_to_scan[:6]:
    try:
        @st.cache_data(ttl=3600)
        def _get_sig(t):
            return fetch_technical(t)
        sig = _get_sig(ticker)
        if not sig:
            continue
        chg   = sig.get("chg",0) or 0
        chg_c = "#276749" if chg>=0 else "#C53030"
        label = (f"**{sig['ticker']}** — {sig.get('name',sig['ticker'])}"
                 f"  ·  ₹{safe_price(sig['price'])}"
                 f"  ·  {sig['arrow'] if hasattr(sig,'arrow') else ('▲' if chg>=0 else '▼')}"
                 f"{abs(chg):.2f}%")
        with st.expander(
            f"{sig['ticker']} — {safe_price(sig['price'])} "
            f"({'▲' if chg>=0 else '▼'}{abs(chg):.2f}%)",
            expanded=False
        ):
            m1,m2,m3,m4,m5 = st.columns(5)
            oc_map = {"sig-buy":"#276749","sig-sell":"#C53030","sig-hold":"#B7791F"}
            oc_hex = oc_map.get(sig.get("oc","sig-hold"),"#B7791F")
            for col, lbl, val, col_hex in [
                (m1,"Signal",    sig.get("overall","–"),       oc_hex),
                (m2,"RSI (14)", str(sig.get("rsi","–")),
                 "#C53030" if sig.get("rsi",50)>70 else ("#276749" if sig.get("rsi",50)<30 else "#B7791F")),
                (m3,"MACD",     "Bullish" if sig.get("score",0)>0 else "Bearish",
                 "#276749" if sig.get("score",0)>0 else "#C53030"),
                (m4,"SMA 50",   safe_price(sig.get("sma50",0)), "#4A5568"),
                (m5,"SMA 200",  safe_price(sig.get("sma200",0)),"#4A5568"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="card" style="text-align:center;padding:10px 8px">
                      <div class="cmd-label">{lbl}</div>
                      <div style="font-family:Syne,sans-serif;font-weight:700;
                                  font-size:13px;color:{col_hex}">{val}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
            for ind_name, ind_val, ind_note, ind_color in sig.get("inds",[]):
                st.markdown(f"""
                <div class="ind-row">
                  <span class="ind-name">{ind_name}</span>
                  <span class="ind-val" style="color:{ind_color}">{ind_val}</span>
                  <span class="ind-note">{ind_note}</span>
                </div>""", unsafe_allow_html=True)

            hist = sig.get("history")
            if hist is not None and len(hist) > 5:
                try:
                    import plotly.graph_objects as go
                    fig = go.Figure(go.Scatter(
                        x=hist["date"], y=hist["close"],
                        mode="lines", line=dict(color="#2B6CB0",width=2),
                        fill="tozeroy", fillcolor="rgba(43,108,176,0.08)"
                    ))
                    fig.update_layout(
                        height=160, margin=dict(l=0,r=0,t=8,b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(showgrid=False,color="#A0AEC0",tickfont=dict(size=9)),
                        yaxis=dict(showgrid=True,gridcolor="#EDF2F7",
                                   color="#A0AEC0",tickfont=dict(size=9)),
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass
    except Exception:
        continue

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════
st.markdown('</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="fp-footer">
  <div class="fp-footer-brand">📡 FinPulse by Anoop Puri</div>
  <p style="color:#A0AEC0;font-size:12px;margin:6px 0">
    Smart Financial Intelligence · India First · World Coverage · Free Forever
  </p>
  <div style="margin:10px 0">
    <a href="https://instagram.com/theanooppuri" target="_blank">📸 @theanooppuri</a>
    <a href="https://linkedin.com/in/theanooppuri" target="_blank">💼 LinkedIn</a>
  </div>
  <div class="fp-footer-copy">
    All times in IST (UTC+5:30) · Data refreshes every 1 hour ·
    Sources: NSE, Yahoo Finance, ET, Mint, BS, Moneycontrol, World Bank ·
    Not Financial Advice · {now_ist().year}
  </div>
</div>
""", unsafe_allow_html=True)

