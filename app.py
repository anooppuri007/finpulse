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
import xml.etree.ElementTree as ET
import urllib.parse
import io, re, random

# ── IST Timezone ──────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
def now_ist(): return datetime.now(IST)
def fmt_ist(dt=None): return (dt or now_ist()).strftime("%d %b %Y, %I:%M %p IST")

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="FinPulse by Anoop Puri",
                   page_icon="📡", layout="wide",
                   initial_sidebar_state="collapsed")

analyzer = SentimentIntensityAnalyzer()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3600000, limit=None, key="auto_refresh")
except Exception:
    pass

if "sel_sector" not in st.session_state:
    st.session_state.sel_sector = "🌐 All News"
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = now_ist()

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinPulse/2.0; +https://finpulse.streamlit.app)"}

# ══════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#F8FAFC!important;color:#1A202C!important}
.stApp{background:#F8FAFC!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}

/* NAV */
.fp-nav{background:#fff;border-bottom:3px solid #C53030;padding:12px 28px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(0,0,0,.07);position:sticky;top:0;z-index:999}
.nav-brand{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#1A202C}
.nav-brand span{color:#C53030}
.nav-sub{font-size:10px;color:#718096;margin-top:2px}
.nav-links a{font-size:12px;font-weight:500;color:#2B6CB0;text-decoration:none;padding:4px 12px;border:1px solid #BEE3F8;border-radius:20px;margin-left:8px;background:#EBF8FF}

/* DISCLAIMER */
.disc{background:#FFFBEB;border-bottom:1px solid #F6E05E;padding:6px 28px;font-size:11px;color:#744210;display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px}

/* WRAP */
.wrap{padding:20px 28px;max-width:1440px;margin:0 auto}

/* SECTION TITLE */
.sec-title{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#718096;border-left:3px solid #C53030;padding-left:10px;margin:0 0 12px 0}

/* CARDS */
.card{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.card-sm{background:#fff;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px}

/* CMD */
.cmd-label{font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#A0AEC0;margin-bottom:4px}
.cmd-val{font-family:'Syne',sans-serif;font-size:19px;font-weight:800;color:#1A202C;line-height:1.1}
.up{color:#276749!important} .dn{color:#C53030!important} .nt{color:#B7791F!important}
.chg{font-size:11px;font-weight:600;margin-top:2px}

/* FG */
.fg-wrap{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:18px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.fg-num{font-family:'Syne',sans-serif;font-size:52px;font-weight:800;line-height:1;margin:6px 0}
.fg-lbl{font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase}
.fg-bar-bg{background:#EDF2F7;border-radius:4px;height:6px;margin:10px 0 4px;overflow:hidden}
.fg-bar{height:100%;border-radius:4px;background:linear-gradient(90deg,#FC8181,#F6AD55,#68D391)}
.fg-scale{display:flex;justify-content:space-between;font-size:9px;color:#A0AEC0}

/* NEWS */
.src-badge{display:inline-block;background:#EBF8FF;border:1px solid #BEE3F8;border-radius:4px;padding:1px 7px;font-size:10px;color:#2B6CB0;font-weight:500;margin-right:4px}
.sec-tag{display:inline-block;background:#F7FAFC;border:1px solid #E2E8F0;border-radius:4px;padding:1px 7px;font-size:10px;color:#4A5568;margin-right:3px}

/* SECTOR LEFT NAV */
.sec-nav-lbl{font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#A0AEC0;margin-bottom:8px;padding:0 4px}

/* FII/DII */
.fii-buy{background:#F0FFF4;border:1px solid #9AE6B4;border-radius:10px;padding:14px 16px;margin-bottom:6px}
.fii-sell{background:#FFF5F5;border:1px solid #FEB2B2;border-radius:10px;padding:14px 16px;margin-bottom:6px}
.fii-val{font-family:'Syne',sans-serif;font-size:20px;font-weight:800}
.fii-lbl{font-size:10px;color:#718096;margin-top:3px}
.data-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;margin-top:6px}
.live-badge{background:#F0FFF4;color:#276749;border:1px solid #9AE6B4}
.demo-badge{background:#FFFBEB;color:#B7791F;border:1px solid #F6E05E}

/* SECTOR */
.sec-hot{background:#F0FFF4;border:1px solid #9AE6B4;border-left:4px solid #38A169;border-radius:8px;padding:12px 14px;margin-bottom:7px}
.sec-cold{background:#FFF5F5;border:1px solid #FEB2B2;border-left:4px solid #E53E3E;border-radius:8px;padding:12px 14px;margin-bottom:7px}
.sec-name{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#1A202C;margin-bottom:3px}
.sec-reason{font-size:12px;color:#718096;line-height:1.4}

/* CALENDAR */
.cal-item{background:#fff;border-left:4px solid #2B6CB0;border-radius:0 8px 8px 0;padding:9px 14px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.cal-date{font-size:10px;font-weight:700;color:#2B6CB0;letter-spacing:.5px}
.cal-title{font-size:13px;font-weight:600;color:#1A202C;margin:2px 0}
.cal-sub{font-size:11px;color:#718096}

/* ECO */
.eco-card{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:14px;margin-bottom:6px}
.eco-lbl{font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#A0AEC0}
.eco-val{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#1A202C;margin:4px 0 2px}
.eco-note{font-size:11px;color:#718096;line-height:1.4}

/* DIVIDER */
.fp-div{height:1px;background:#EDF2F7;margin:24px 0}

/* REFRESH */
.rfsh{display:inline-flex;align-items:center;gap:6px;background:#F0FFF4;border:1px solid #9AE6B4;border-radius:20px;padding:3px 12px;font-size:10px;color:#276749;font-weight:500}
.rdot{width:6px;height:6px;background:#38A169;border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* FOOTER */
.fp-footer{background:#1A202C;padding:24px 28px;text-align:center;margin-top:40px}
.fp-footer-brand{font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#fff;margin-bottom:6px}
.fp-footer a{color:#A0AEC0;text-decoration:none;font-size:12px;margin:0 8px}
.fp-footer-copy{font-size:11px;color:#4A5568;margin-top:8px}

/* STREAMLIT OVERRIDES */
div[data-testid="stButton"]>button{background:#fff!important;color:#2B6CB0!important;border:1.5px solid #BEE3F8!important;border-radius:8px!important;font-weight:600!important;font-size:13px!important;width:100%!important;transition:all .2s}
div[data-testid="stButton"]>button:hover{background:#EBF8FF!important;border-color:#2B6CB0!important}
.stDownloadButton>button{background:#2B6CB0!important;color:#fff!important;border:none!important;border-radius:8px!important;font-weight:700!important;width:100%!important}
.stTextInput input,.stNumberInput input{background:#fff!important;color:#1A202C!important;border:1.5px solid #E2E8F0!important;border-radius:8px!important;font-size:13px!important}
.stTextInput input:focus{border-color:#2B6CB0!important;box-shadow:0 0 0 3px rgba(43,108,176,.1)!important}
.streamlit-expanderHeader{background:#fff!important;color:#2D3748!important;font-size:13px!important;font-weight:500!important;border:1px solid #E2E8F0!important;border-radius:10px!important;padding:11px 15px!important}
.streamlit-expanderHeader:hover{border-color:#2B6CB0!important;background:#EBF8FF!important}
.streamlit-expanderContent{background:#F7FAFC!important;border:1px solid #E2E8F0!important;border-top:none!important;border-radius:0 0 10px 10px!important;padding:12px!important}
.stMarkdown p,.stMarkdown li{color:#2D3748!important}
label{color:#4A5568!important;font-size:13px!important}
[data-testid="stElementToolbar"]{display:none!important}
hr{border-color:#EDF2F7!important}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════
FINANCE_KW = ["nifty","sensex","sebi","rbi","equity","stock","market","rupee",
               "fii","dii","ipo","budget","repo","inflation","earnings","crore",
               "lakh","quarterly","results","profit","revenue","dividend","bse",
               "nse","percent","%","gdp","economy","interest rate","crude","gold"]

BLOCK_KW = ["opinion","how to invest","top 10","top 5","best stocks to buy",
            "should you buy","things to know","explained","what is","beginners",
            "complete guide","tips for","wealth creation","stock tips","everything about",
            "why you should","5 reasons","10 reasons","here's why","you need to know"]

STRONG_KW = [r"\d+\.?\d*\s*%", r"₹\s*\d+", r"\$\s*\d+",
             r"\d+\s*(crore|lakh|billion|million|cr|mn|bn)",
             "reliance","tcs","infosys","hdfc","icici","sbi","wipro","bajaj",
             "maruti","tata","adani","kotak","axis bank","ongc","bpcl","itc",
             "l&t","sun pharma","dr reddy","cipla","airtel","jio","tesla","apple",
             "nvidia","microsoft","amazon","google","rate cut","rate hike",
             "repo rate","rbi policy","sebi order","quarterly results","q1","q2","q3","q4",
             "net profit","operating profit","revenue grows","revenue declines",
             "ipo launch","ipo opens","listing","fii bought","fii sold",
             "bulk deal","block deal","merger","acquisition","dividend declared",
             "bonus shares","stock split","buyback","sensex rises","sensex falls",
             "nifty gains","nifty drops","all-time high","52-week high","52-week low",
             "circuit","lower circuit","upper circuit","us fed","fomc","rbi governor",
             "trade deficit","forex reserve","inflation data","cpi","iip data"]

SECTOR_MAP = {
    "Banking & Finance":       ["bank","hdfc","icici","kotak","sbi","axis","rbi","nbfc","credit","loan","npa","lending"],
    "IT/Technology":           ["tcs","infosys","wipro","hcl","tech mahindra","software","it sector","digital","ai","cloud"],
    "Energy/Oil":              ["oil","reliance","ongc","bpcl","iocl","gas","petroleum","crude","energy","opec","refinery"],
    "Pharma/Healthcare":       ["pharma","dr reddy","sun pharma","cipla","biocon","drug","fda","usfda","medicine","healthcare"],
    "Auto/EV":                 ["maruti","tata motors","m&m","bajaj","hero","vehicle","ev","automobile","car","electric"],
    "FMCG/Consumer":           ["hindustan unilever","itc","nestle","dabur","britannia","fmcg","consumer"],
    "Metals/Mining":           ["tata steel","jsw","hindalco","vedanta","coal","steel","metal","aluminium","mining"],
    "Realty/Infra":            ["dlf","godrej","real estate","property","housing","realty","infrastructure","roads","l&t"],
    "Telecom":                 ["airtel","jio","vodafone","telecom","5g","spectrum","bharti"],
    "PSU/Defence":             ["psu","public sector","defence","hal","bhel","ntpc","power grid","lic","coal india"],
    "Chemicals":               ["chemical","fertiliser","pidilite","asian paints","agrochemical","specialty"],
    "Global/Macro":            ["fed","federal reserve","us market","global","dollar","s&p","nasdaq","china","europe"],
}

def get_sectors(text):
    t = text.lower()
    return [s for s, kws in SECTOR_MAP.items() if any(k in t for k in kws)][:3] or ["General Market"]

def get_sentiment(text):
    sc = analyzer.polarity_scores(text)["compound"]
    if sc >= 0.05:   return sc, "🟢", "#276749", "Positive"
    elif sc <= -0.05: return sc, "🔴", "#C53030", "Negative"
    else:            return sc, "🟡", "#B7791F", "Neutral"

def safe_price(v):
    try:    return f"{float(v):,.2f}"
    except: return "–"

# ══════════════════════════════════════════════════════════════════════════
#  DATA FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════
def yf_quote(sym):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
        r   = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200: return None
        meta  = r.json()["chart"]["result"][0]["meta"]
        price = float(meta.get("regularMarketPrice", 0))
        prev  = float(meta.get("previousClose", price) or price)
        chg   = round((price - prev) / prev * 100, 2) if prev else 0
        return {"price": round(price, 2), "chg": chg,
                "arrow": "▲" if chg >= 0 else "▼",
                "color": "up" if chg >= 0 else "dn",
                "name":  meta.get("shortName", sym)}
    except: return None

def _split_summary(title, desc):
    text  = (title + ". " + desc).strip()
    words = text.split()
    if len(words) < 12:
        return [title, "Monitor for market impact.", "Check related sectors."]
    n = max(8, len(words) // 3)
    return [" ".join(words[:n]).rstrip(".,") + ".",
            " ".join(words[n:n*2]).rstrip(".,") + ".",
            " ".join(words[n*2:n*3]).rstrip(".,") + "."]

def fetch_rss(url, source, max_items=10):
    arts = []
    try:
        r    = requests.get(url, headers=HEADERS, timeout=8)
        root = ET.fromstring(r.content)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            link  = (item.findtext("link") or "").strip()
            if not title or len(title) < 15: continue
            combined = (title + " " + desc).lower()
            if any(bk in combined for bk in BLOCK_KW): continue
            if not any(k in combined for k in FINANCE_KW): continue
            has_strong = any(
                (re.search(sk, combined) if sk.startswith(r"\d") or sk.startswith(r"₹") or sk.startswith(r"\$")
                 else sk in combined)
                for sk in STRONG_KW
            )
            if not has_strong: continue
            sc, emoji, color, label = get_sentiment(combined)
            arts.append({"title": title, "desc": desc[:250], "source": source,
                         "url": link, "score": sc, "emoji": emoji, "color": color,
                         "label": label, "sectors": get_sectors(combined),
                         "summary": _split_summary(title, desc)})
            if len(arts) >= max_items: break
    except Exception: pass
    return arts

def fetch_gnews(query, label="Google News", max_items=8):
    encoded = urllib.parse.quote(query)
    url = (f"https://news.google.com/rss/search"
           f"?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en")
    arts = fetch_rss(url, label, max_items)
    for a in arts:
        if " - " in a["title"]:
            parts = a["title"].rsplit(" - ", 1)
            a["title"]  = parts[0].strip()
            a["source"] = parts[1].strip() if len(parts) > 1 else label
    return arts

@st.cache_data(ttl=3600)
def fetch_all_news():
    indian = [
        ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "Economic Times"),
        ("https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms", "ET Economy"),
        ("https://www.business-standard.com/rss/markets-106.rss",               "Business Standard"),
        ("https://www.livemint.com/rss/markets",                                 "Mint"),
        ("https://www.moneycontrol.com/rss/MCtopnews.xml",                       "Moneycontrol"),
        ("https://feeds.feedburner.com/ndtvprofit-latest",                       "NDTV Profit"),
        ("https://www.financialexpress.com/market/feed/",                        "Financial Express"),
    ]
    glob = [
        ("https://feeds.bbci.co.uk/news/business/rss.xml",                                  "BBC Business"),
        ("https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",   "Yahoo Finance"),
        ("https://rss.cnn.com/rss/money_news_international.rss",                            "CNN Money"),
    ]
    gnews_queries = [
        "Nifty Sensex India stock market today results",
        "RBI India economy rupee interest rate policy",
        "FII DII India stock market buying selling",
        "India company quarterly results earnings profit",
        "India IPO listing BSE NSE today",
        "crude oil gold dollar impact India rupee",
    ]
    all_arts, seen = [], set()
    for url, name in indian + glob:
        for a in fetch_rss(url, name, 10):
            k = a["title"][:55].lower().strip()
            if k not in seen:
                seen.add(k)
                a["indian"] = name not in ["BBC Business","Yahoo Finance","CNN Money"]
                all_arts.append(a)
    for q in gnews_queries:
        for a in fetch_gnews(q, "Google News", 6):
            k = a["title"][:55].lower().strip()
            if k not in seen:
                seen.add(k)
                a["indian"] = True
                all_arts.append(a)
    all_arts.sort(key=lambda x: abs(x["score"]), reverse=True)
    return all_arts[:30]

@st.cache_data(ttl=1800)
def fetch_sector_news(sector):
    queries = {
        "🏦 Banking & Finance":       "India banking HDFC ICICI SBI RBI repo rate NPA results",
        "💻 IT / Technology":         "India IT TCS Infosys Wipro HCL results deal quarterly",
        "⛽ Energy & Oil":            "India oil energy Reliance ONGC BPCL crude price",
        "💊 Pharma & Healthcare":     "India pharma Sun Pharma Dr Reddy Cipla USFDA results",
        "🚗 Auto & EV":               "India auto Maruti Tata Motors Bajaj M&M EV sales monthly",
        "🛒 FMCG & Consumer":        "India FMCG Hindustan Unilever ITC Nestle Dabur results",
        "⚙️ Metals & Mining":        "India metals Tata Steel JSW Hindalco Vedanta steel coal",
        "🏗️ Realty & Infrastructure":"India realty DLF Godrej Properties real estate housing",
        "📡 Telecom":                 "India telecom Airtel Jio 5G spectrum subscribers ARPU",
        "🏛️ PSU & Defence":          "India PSU defence HAL BEL BHEL NTPC disinvestment",
        "🧪 Chemicals":               "India chemicals fertiliser Pidilite Asian Paints results",
        "📈 Midcap & Smallcap":       "India midcap smallcap BSE NSE rally results",
        "🌍 Global — US Tech":        "US tech Apple Nvidia Microsoft Google AI earnings",
        "🌍 Global — Banks":          "global banks JPMorgan Goldman Fed rate decision",
        "🌍 Global — Commodities":    "crude oil gold silver copper OPEC commodity",
        "🇮🇳 India Macro & Policy":   "India RBI SEBI budget GDP inflation CPI fiscal policy",
    }
    q     = queries.get(sector, f"India {sector.split()[-1]} stock market news")
    arts  = fetch_gnews(q, "Google News", 15)
    base  = fetch_all_news()
    kws   = next((v for k, v in {
        "🏦 Banking & Finance":  ["bank","hdfc","icici","sbi","rbi","nbfc"],
        "💻 IT / Technology":    ["tcs","infosys","wipro","hcl","software","it"],
        "⛽ Energy & Oil":       ["oil","reliance","ongc","bpcl","crude","energy"],
        "💊 Pharma & Healthcare":["pharma","sun pharma","cipla","dr reddy","fda"],
        "🚗 Auto & EV":          ["maruti","tata motors","bajaj","ev","automobile"],
    }.items() if k == sector), [])
    for a in base:
        if any(kw in (a["title"]+" "+a.get("desc","")).lower() for kw in kws):
            arts.append(a)
    seen, unique = set(), []
    for a in arts:
        k = a["title"][:50].lower()
        if k not in seen:
            seen.add(k)
            unique.append(a)
    return sorted(unique, key=lambda x: abs(x["score"]), reverse=True)[:20]

@st.cache_data(ttl=300)
def fetch_market():
    symbols = {
        "Nifty 50":    "^NSEI",   "Sensex":      "^BSESN",
        "Bank Nifty":  "^NSEBANK","Nifty IT":    "^CNXIT",
        "Nifty Pharma":"^CNXPHARMA",
        "S&P 500":     "^GSPC",   "Gold":        "GC=F",
        "Oil (WTI)":   "CL=F",    "USD/INR":     "USDINR=X",
        "Bitcoin":     "BTC-USD", "Silver":      "SI=F",
        "EUR/INR":     "EURINR=X","NASDAQ":      "^IXIC",
    }
    out = {}
    for name, sym in symbols.items():
        d = yf_quote(sym)
        out[name] = d if d else {"price": 0, "chg": 0, "arrow": "–", "color": "nt", "name": name}
    return out

@st.cache_data(ttl=1800)
def fetch_fiidii():
    """Try NSE → Trendlyne → Moneycontrol → demo. Always return (rows, source, as_of, is_live)."""
    r = _try_nse()
    if r: return r
    r = _try_trendlyne()
    if r: return r
    r = _try_moneycontrol()
    if r: return r
    return _demo_fiidii()

def _try_nse():
    try:
        s = requests.Session()
        bh = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
              "Accept-Language":"en-US,en;q=0.9"}
        s.get("https://www.nseindia.com",
              headers={**bh,"Accept":"text/html,application/xhtml+xml"}, timeout=10)
        r = s.get("https://www.nseindia.com/api/fiidiiTradeReact",
                  headers={**bh,"Accept":"application/json",
                           "Referer":"https://www.nseindia.com/market-data/fii-dii-trading-activity"},
                  timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) >= 3:
                rows = []
                for item in data[:30]:
                    def pf(k): return float(str(item.get(k,"0")).replace(",","") or 0)
                    rows.append({"date":item.get("date",""),
                                 "fii_buy":pf("fiiBuyValue"),"fii_sell":pf("fiiSellValue"),
                                 "fii_net":pf("fiiNetValue"),"dii_buy":pf("diiBuyValue"),
                                 "dii_sell":pf("diiSellValue"),"dii_net":pf("diiNetValue")})
                if rows:
                    return rows, "NSE India (nseindia.com)", rows[0]["date"], True
    except Exception: pass
    return None

def _try_trendlyne():
    try:
        r = requests.get("https://trendlyne.com/macro-data/fii-dii-data/",
                         headers=HEADERS, timeout=10)
        if r.status_code == 200 and "FII" in r.text:
            rows = _parse_table_html(r.text)
            if rows:
                return rows, "Trendlyne (trendlyne.com)", rows[0]["date"], True
    except Exception: pass
    return None

def _try_moneycontrol():
    try:
        r = requests.get("https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/",
                         headers=HEADERS, timeout=10)
        if r.status_code == 200 and "FII" in r.text:
            rows = _parse_table_html(r.text)
            if rows:
                return rows, "Moneycontrol (moneycontrol.com)", rows[0]["date"], True
    except Exception: pass
    return None

def _parse_table_html(html):
    try:
        dates = re.findall(r'(\d{1,2}[-/]\w{3}[-/]\d{2,4})', html)
        nums  = re.findall(r'([-+]?\d{1,2},\d{3}(?:\.\d{1,2})?)', html)
        rows  = []
        for i, date in enumerate(dates[:25]):
            b = i * 6
            if b + 5 < len(nums):
                def pn(s): return float(s.replace(",",""))
                rows.append({"date":date, "fii_buy":abs(pn(nums[b])),
                             "fii_sell":abs(pn(nums[b+1])), "fii_net":pn(nums[b+2]),
                             "dii_buy":abs(pn(nums[b+3])), "dii_sell":abs(pn(nums[b+4])),
                             "dii_net":pn(nums[b+5]) if b+5 < len(nums) else 0})
        return rows if len(rows) >= 3 else []
    except: return []

def _demo_fiidii():
    """Clearly labelled demo — used when all live sources fail."""
    random.seed(42)
    today = now_ist()
    fii_t = [2800,-1200,3400,-800,1600,-2100,4200,-600,2900,1100,
             -3200,1800,3100,-1500,2400,-900,3600,-400,1900,2700,
             -1800,4100,-700,2200,1300,-2600,3800,-1100,2500,900]
    dii_t = [-1800,900,-2200,600,-1100,1400,-2800,400,-1900,-700,
              2100,-1200,-2000,1000,-1600,600,-2400,300,-1300,-1800,
              1200,-2700,500,-1500,-900,1700,-2500,800,-1700,-600]
    rows, j = [], 0
    for i in range(60):
        if j >= len(fii_t): break
        d = today - timedelta(days=i)
        if d.weekday() >= 5: continue
        fn, dn = fii_t[j], dii_t[j]; j += 1
        rows.append({"date":d.strftime("%d-%b-%Y"),
                     "fii_buy":round(abs(fn)+random.uniform(8000,15000),2),
                     "fii_sell":round(abs(fn)+random.uniform(7000,13000)-fn,2),
                     "fii_net":fn, "dii_buy":round(abs(dn)+random.uniform(4000,9000),2),
                     "dii_sell":round(abs(dn)+random.uniform(3500,8000)-dn,2),
                     "dii_net":dn})
    as_of = rows[0]["date"] if rows else today.strftime("%d-%b-%Y")
    return rows, "⚠️ Demo Data — Live sources unavailable", as_of, False

@st.cache_data(ttl=3600)
def fetch_economic():
    ivix = yf_quote("^INDIAVIX")
    vix  = yf_quote("^VIX")
    tnx  = yf_quote("^TNX")
    tyx  = yf_quote("^TYX")
    inr  = yf_quote("USDINR=X")
    gold = yf_quote("GC=F")
    oil  = yf_quote("CL=F")

    def vix_mood(v, india=False):
        label = "India VIX" if india else "US VIX"
        if not v: return "Loading...", "#718096"
        if v < 12:   return "Very Low — High complacency ⚠️", "#B7791F"
        elif v < 15: return "Low — Markets calm 😌", "#276749"
        elif v < 20: return "Moderate — Normal range 😐", "#B7791F"
        elif v < 25: return "Elevated — Fear building 😟", "#C53030"
        else:        return "High Fear — Market stressed 😨", "#C53030"

    ivix_v   = (ivix or {}).get("price")
    vix_v    = (vix  or {}).get("price")
    ivix_m,ivc = vix_mood(ivix_v, True)
    vix_m, vc  = vix_mood(vix_v, False)

    t10 = (tnx or {}).get("price")
    t30 = (tyx or {}).get("price")
    yc_sig, yc_c, yc_note = "Normal", "#276749", "Healthy — economy expanding"
    if t10 and t30:
        sp = round(float(t30) - float(t10), 2)
        if sp < 0:    yc_sig,yc_c,yc_note = "Inverted ⚠️","#C53030",f"Inverted {abs(sp):.2f}% — recession warning signal"
        elif sp < 0.5:yc_sig,yc_c,yc_note = "Flat","#B7791F",f"Flat spread ({sp:.2f}%) — slowing growth"
        else:         yc_note = f"Healthy spread {sp:.2f}%"

    # Latest India macro — from official announcements (clearly dated)
    macro = [
        {"indicator":"RBI Repo Rate",      "value":"6.25%",    "change":"↓ Cut 25bps",
         "date":"Jun 2025","source":"RBI MPC","note":"RBI cut repo rate 25bps in June 2025","color":"#276749"},
        {"indicator":"India CPI Inflation","value":"4.83%",    "change":"↑ from 4.59%",
         "date":"Apr 2025","source":"MOSPI","note":"April 2025 CPI — above RBI 4% target","color":"#C53030"},
        {"indicator":"India GDP Growth",   "value":"6.4%",     "change":"FY2024-25",
         "date":"FY25","source":"NSO/MOSPI","note":"Full-year FY25 GDP growth estimate","color":"#276749"},
        {"indicator":"Forex Reserves",     "value":"$688 Bn",  "change":"↑ Record high",
         "date":"Jun 2025","source":"RBI","note":"India forex at record — strong external position","color":"#276749"},
        {"indicator":"India IIP Growth",   "value":"3.0%",     "change":"Mar 2025",
         "date":"Mar 2025","source":"MOSPI","note":"Industrial production growth — moderated","color":"#B7791F"},
        {"indicator":"Fiscal Deficit",     "value":"4.8% GDP", "change":"Below 5.1% target",
         "date":"FY25","source":"Finance Ministry","note":"Government stayed within fiscal target","color":"#276749"},
    ]
    return {"ivix":{"val":ivix_v,"mood":ivix_m,"color":ivc},
            "vix": {"val":vix_v, "mood":vix_m, "color":vc},
            "yield":{"sig":yc_sig,"color":yc_c,"note":yc_note,"t10":t10,"t30":t30},
            "inr":inr,"gold":gold,"oil":oil,"macro":macro,"updated":fmt_ist()}

def get_market_events():
    events = [
        {"date":"04-06-2026","type":"RBI","title":"RBI MPC Decision",
         "detail":"Bi-monthly monetary policy — repo rate decision","color":"#2B6CB0","urgent":True},
        {"date":"25-06-2026","type":"F&O","title":"June F&O Expiry",
         "detail":"Monthly futures & options expiry — high volatility day","color":"#B7791F","urgent":True},
        {"date":"17-06-2026","type":"Fed","title":"US Fed FOMC Meeting",
         "detail":"Federal Reserve rate decision — impacts FII flows into India","color":"#4A5568","urgent":True},
        {"date":"15-07-2026","type":"Results","title":"Q1 FY27 Results Season",
         "detail":"TCS, Infosys, HCL Tech lead IT earnings — market direction setter","color":"#276749","urgent":False},
        {"date":"21-07-2026","type":"Results","title":"Major Bank Results",
         "detail":"HDFC Bank, ICICI Bank, Kotak quarterly results","color":"#276749","urgent":False},
        {"date":"30-07-2026","type":"F&O","title":"July F&O Expiry",
         "detail":"Monthly derivatives expiry","color":"#B7791F","urgent":False},
        {"date":"06-08-2026","type":"RBI","title":"RBI MPC Meeting",
         "detail":"August bi-monthly policy review","color":"#2B6CB0","urgent":False},
        {"date":"29-07-2026","type":"Fed","title":"US Fed FOMC Meeting",
         "detail":"Next Federal Reserve policy meeting","color":"#4A5568","urgent":False},
        {"date":"01-02-2027","type":"Budget","title":"Union Budget 2027",
         "detail":"Annual Union Budget — biggest market event of the year","color":"#C53030","urgent":False},
    ]
    today, out = now_ist(), []
    for e in events:
        try:
            edt  = datetime.strptime(e["date"],"%d-%m-%Y").replace(tzinfo=IST)
            diff = (edt - today).days
            if diff >= -1:
                e["days_away"] = diff
                e["date_fmt"]  = edt.strftime("%d %b %Y")
                out.append(e)
        except: pass
    return sorted(out, key=lambda x: x["days_away"])[:10]

def calc_fg(market, news):
    score  = 50
    nc     = (market.get("Nifty 50") or {}).get("chg", 0) or 0
    score += min(20, max(-20, nc * 4))
    ns     = [n["score"] for n in news if "score" in n]
    if ns:  score += min(15, max(-15, (sum(ns)/len(ns)) * 25))
    score  = max(0, min(100, int(score)))
    if   score <= 25: return score, "Extreme Fear 😨",  "#C53030"
    elif score <= 45: return score, "Fear 😟",           "#E67E22"
    elif score <= 55: return score, "Neutral 😐",        "#B7791F"
    elif score <= 75: return score, "Greed 😏",          "#276749"
    else:             return score, "Extreme Greed 🤑",  "#276749"

SECTOR_STOCKS = {
    "🏦 Banking & Finance":  ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","SBIN.NS","AXISBANK.NS"],
    "💻 IT / Technology":    ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "⛽ Energy & Oil":       ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS","GAIL.NS"],
    "💊 Pharma & Healthcare":["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS","BIOCON.NS"],
    "🚗 Auto & EV":          ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "🛒 FMCG & Consumer":   ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","DABUR.NS","BRITANNIA.NS"],
    "⚙️ Metals & Mining":   ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS","COALINDIA.NS"],
    "🏗️ Realty & Infrastructure":["DLF.NS","GODREJPROP.NS","LT.NS","ADANIPORTS.NS"],
    "📡 Telecom":            ["BHARTIARTL.NS","INDUSTOWER.NS"],
    "🏛️ PSU & Defence":     ["HAL.NS","BEL.NS","BHEL.NS","NTPC.NS","POWERGRID.NS"],
}

def make_pdf(market, news, fg_score, fg_label, fii_rows, fii_source, fii_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors as rc
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                        Spacer, Table, TableStyle, PageBreak)
        from reportlab.lib.enums import TA_CENTER
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
              leftMargin=20*mm, rightMargin=20*mm,
              topMargin=15*mm, bottomMargin=15*mm)
        NAVY=rc.HexColor("#1A202C"); RED=rc.HexColor("#C53030")
        GRAY=rc.HexColor("#718096"); WHITE=rc.white; W=A4[0]-40*mm
        def ps(n,**k): return ParagraphStyle(n,**k)
        story = []
        # Header
        hdr=Table([[Paragraph("📡 FinPulse",ps("h",fontName="Helvetica-Bold",fontSize=20,textColor=WHITE,leading=24)),
                    Paragraph(f"by Anoop Puri  ·  {fmt_ist()}",ps("s",fontName="Helvetica",fontSize=9,textColor=rc.HexColor("#A0AEC0"),alignment=2,leading=12))]],
                  colWidths=[W*.5,W*.5])
        hdr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),("LEFTPADDING",(0,0),(-1,-1),10),
                                  ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
                                  ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        story.append(hdr); story.append(Spacer(1,5*mm))
        # Markets
        story.append(Paragraph("MARKET SNAPSHOT",ps("mh",fontName="Helvetica-Bold",fontSize=8,textColor=GRAY)))
        story.append(Spacer(1,2*mm))
        mkt_rows=[["Index/Asset","Price","Change"]]
        for name in ["Nifty 50","Sensex","Bank Nifty","Gold","Oil (WTI)","USD/INR","Bitcoin"]:
            d=market.get(name,{}); chg=d.get("chg",0)
            mkt_rows.append([name,safe_price(d.get("price",0)),f"{d.get('arrow','')} {abs(chg):.2f}%"])
        styled=[[Paragraph(c,ps("mc",fontName="Helvetica-Bold" if i==0 else "Helvetica",
            fontSize=8,textColor=WHITE if i==0 else rc.HexColor("#2D3748"),leading=11)) for c in row]
            for i,row in enumerate(mkt_rows)]
        mt=Table(styled,colWidths=[55*mm,35*mm,35*mm])
        mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),
                                 ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,rc.HexColor("#F7FAFC")]),
                                 ("GRID",(0,0),(-1,-1),.3,rc.HexColor("#E2E8F0")),
                                 ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
                                 ("LEFTPADDING",(0,0),(-1,-1),6)]))
        story.append(mt); story.append(Spacer(1,5*mm))
        # FG
        fg=Table([[Paragraph(f"Fear & Greed: {fg_score} — {fg_label}",
            ps("fg",fontName="Helvetica-Bold",fontSize=11,textColor=NAVY,alignment=TA_CENTER))]],colWidths=[W])
        fg.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),rc.HexColor("#FFFBEB")),
                                 ("BOX",(0,0),(-1,-1),1,rc.HexColor("#F6E05E")),
                                 ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
        story.append(fg); story.append(Spacer(1,5*mm))
        # FII/DII
        if fii_rows:
            story.append(Paragraph(f"FII/DII — {fii_source} · As of {fii_date}",
                ps("fh",fontName="Helvetica-Bold",fontSize=8,textColor=GRAY)))
            story.append(Spacer(1,2*mm))
            fi=[["Date","FII Net (₹Cr)","DII Net (₹Cr)"]]
            for row in fii_rows[:5]:
                fn=row.get("fii_net",0); dn=row.get("dii_net",0)
                fi.append([row.get("date",""),f"{'+'if fn>=0 else ''}{fn:,.0f}",f"{'+'if dn>=0 else ''}{dn:,.0f}"])
            fi_s=[[Paragraph(c,ps("fc",fontName="Helvetica-Bold" if i==0 else "Helvetica",
                fontSize=8,textColor=WHITE if i==0 else rc.HexColor("#2D3748"),leading=11)) for c in row]
                for i,row in enumerate(fi)]
            ft=Table(fi_s,colWidths=[35*mm,40*mm,40*mm])
            ft.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),rc.HexColor("#2B6CB0")),
                                     ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,rc.HexColor("#EBF8FF")]),
                                     ("GRID",(0,0),(-1,-1),.3,rc.HexColor("#BEE3F8")),
                                     ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
                                     ("LEFTPADDING",(0,0),(-1,-1),6)]))
            story.append(ft); story.append(Spacer(1,5*mm))
        story.append(PageBreak())
        # News
        story.append(Paragraph("TOP NEWS TODAY",ps("nh",fontName="Helvetica-Bold",fontSize=8,textColor=GRAY)))
        story.append(Spacer(1,3*mm))
        for art in news[:8]:
            sc=(rc.HexColor("#276749") if art["color"]=="#276749"
               else rc.HexColor("#C53030") if art["color"]=="#C53030"
               else rc.HexColor("#B7791F"))
            hrow=Table([[Paragraph(art["emoji"],ps("e",fontName="Helvetica",fontSize=10,textColor=WHITE,alignment=TA_CENTER,leading=12)),
                         Paragraph(f"<b>{art['title'][:90]}</b>",ps("t",fontName="Helvetica-Bold",fontSize=9,textColor=rc.HexColor("#2D3748"),leading=12)),
                         Paragraph(art["source"],ps("s2",fontName="Helvetica-Oblique",fontSize=7.5,textColor=GRAY,alignment=2,leading=10))]],
                       colWidths=[8*mm,W-8*mm-28*mm,28*mm])
            hrow.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),sc),
                                       ("BACKGROUND",(1,0),(-1,-1),rc.HexColor("#F7FAFC")),
                                       ("LEFTPADDING",(0,0),(-1,-1),5),
                                       ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                                       ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                       ("BOX",(0,0),(-1,-1),.3,rc.HexColor("#E2E8F0"))]))
            story.append(hrow)
            for line in (art.get("summary") or [])[:2]:
                if line.strip():
                    story.append(Paragraph(f"→ {line}",ps("nl",fontName="Helvetica",fontSize=8,
                        textColor=rc.HexColor("#4A5568"),leftIndent=8,leading=12,spaceBefore=1)))
            story.append(Paragraph(f"Sectors: {' | '.join(art['sectors'])}  ·  Source: {art['source']}",
                ps("nm",fontName="Helvetica",fontSize=7.5,textColor=GRAY,leading=10,spaceBefore=2)))
            story.append(Spacer(1,3*mm))
        ft=Table([[Paragraph("FinPulse by Anoop Puri  ·  @theanooppuri  ·  Not Financial Advice",
            ps("ft",fontName="Helvetica",fontSize=8,textColor=GRAY,alignment=TA_CENTER))]],colWidths=[W])
        ft.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),rc.HexColor("#F7FAFC")),
                                  ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        story.append(ft)
        doc.build(story); buf.seek(0); return buf.getvalue()
    except Exception: return None

# ══════════════════════════════════════════════════════════════════════════
#  APP LAYOUT
# ══════════════════════════════════════════════════════════════════════════

# NAV
st.markdown("""
<div class="fp-nav">
  <div>
    <div class="nav-brand">📡 Fin<span>Pulse</span></div>
    <div class="nav-sub">by Anoop Puri · India First · World Coverage · All times in IST</div>
  </div>
  <div class="nav-links">
    <a href="https://instagram.com/theanooppuri" target="_blank">📸 @theanooppuri</a>
    <a href="https://linkedin.com/in/theanooppuri" target="_blank">💼 LinkedIn</a>
  </div>
</div>""", unsafe_allow_html=True)

# LOAD DATA
with st.spinner("Loading live data..."):
    market   = fetch_market()
    news     = fetch_all_news()
    fii_data = fetch_fiidii()
    eco      = fetch_economic()
    events   = get_market_events()

fii_rows, fii_source, fii_as_of, fii_live = fii_data
fg_score, fg_label, fg_color = calc_fg(market, news)
indian_news = [n for n in news if n.get("indian")]
global_news = [n for n in news if not n.get("indian")]

# DISCLAIMER
st.markdown(f"""
<div class="disc">
  <span>⚠️ <b>Not Financial Advice.</b> Data: NSE India · Yahoo Finance · ET · Mint ·
  BS · Moneycontrol · NDTV Profit · RBI · MOSPI. Verify independently.</span>
  <span>🕐 {fmt_ist()}</span>
</div>""", unsafe_allow_html=True)

st.markdown('<div class="wrap">', unsafe_allow_html=True)

# TOP BAR
rc1, rc2, rc3 = st.columns([2,1,1])
with rc1:
    elapsed = int((now_ist()-st.session_state.last_refresh).total_seconds()/60)
    remain  = max(0, 60-elapsed)
    st.markdown(f'<div class="rfsh"><div class="rdot"></div>Live · Updated {elapsed}m ago · Auto-refresh in {remain}m</div>',
                unsafe_allow_html=True)
with rc2:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_refresh = now_ist()
        st.rerun()
with rc3:
    pdf = make_pdf(market, news, fg_score, fg_label, fii_rows, fii_source, fii_as_of)
    if pdf:
        st.download_button("⬇️ Download Brief PDF", data=pdf,
            file_name=f"FinPulse_{now_ist().strftime('%d%b%Y')}.pdf",
            mime="application/pdf", use_container_width=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══ SECTION 1: COMMAND CENTER ═════════════════════════════
st.markdown('<p class="sec-title">📊 Command Center</p>', unsafe_allow_html=True)

# Indian indices row
for cols, names in [
    (st.columns(5), ["Nifty 50","Sensex","Bank Nifty","Nifty IT","Nifty Pharma"]),
]:
    for col, name in zip(cols, names):
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

# Global + FG row
gc1,gc2,gc3,gc4,gc5,gc6 = st.columns(6)
quick = [(gc1,"S&P 500"),(gc2,"Gold"),(gc3,"Oil (WTI)"),(gc4,"USD/INR"),(gc5,"Bitcoin")]
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
with gc6:
    st.markdown(f"""
    <div class="fg-wrap">
      <div class="cmd-label">Fear &amp; Greed</div>
      <div class="fg-num" style="color:{fg_color}">{fg_score}</div>
      <div class="fg-lbl" style="color:{fg_color}">{fg_label}</div>
      <div class="fg-bar-bg"><div class="fg-bar" style="width:{fg_score}%"></div></div>
      <div class="fg-scale"><span>Fear</span><span>Greed</span></div>
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══ SECTION 2: NEWS + SECTOR LEFT NAV ════════════════════
ALL_SECTORS = [
    "🌐 All News","🏦 Banking & Finance","💻 IT / Technology",
    "⛽ Energy & Oil","💊 Pharma & Healthcare","🚗 Auto & EV",
    "🛒 FMCG & Consumer","⚙️ Metals & Mining","🏗️ Realty & Infrastructure",
    "📡 Telecom","🏛️ PSU & Defence","🧪 Chemicals",
    "📈 Midcap & Smallcap","🌍 Global — US Tech","🌍 Global — Banks",
    "🌍 Global — Commodities","🇮🇳 India Macro & Policy",
]

SECTOR_KW_MAP = {
    "🏦 Banking & Finance":  ["bank","hdfc","icici","sbi","rbi","nbfc","credit","loan"],
    "💻 IT / Technology":    ["tcs","infosys","wipro","hcl","software","it","digital","ai"],
    "⛽ Energy & Oil":       ["oil","reliance","ongc","bpcl","crude","energy","opec"],
    "💊 Pharma & Healthcare":["pharma","sun pharma","cipla","dr reddy","fda","drug"],
    "🚗 Auto & EV":          ["maruti","tata motors","bajaj","ev","automobile","vehicle"],
    "🛒 FMCG & Consumer":   ["hindustan unilever","itc","nestle","dabur","fmcg","consumer"],
    "⚙️ Metals & Mining":   ["tata steel","jsw","hindalco","vedanta","coal","steel","metal"],
    "🏗️ Realty & Infrastructure":["dlf","godrej","real estate","realty","infrastructure","l&t"],
    "📡 Telecom":            ["airtel","jio","vodafone","telecom","5g","spectrum"],
    "🏛️ PSU & Defence":     ["psu","defence","hal","bhel","ntpc","lic","government"],
    "🧪 Chemicals":          ["chemical","fertiliser","pidilite","asian paints","specialty"],
    "📈 Midcap & Smallcap":  ["midcap","smallcap","bse midcap","small cap"],
    "🌍 Global — US Tech":   ["apple","nvidia","microsoft","google","us tech","nasdaq","s&p"],
    "🌍 Global — Banks":     ["jpmorgan","goldman","morgan stanley","global bank","fed"],
    "🌍 Global — Commodities":["crude oil","brent","gold price","silver","copper","opec"],
    "🇮🇳 India Macro & Policy":["rbi","sebi","finance ministry","budget","gdp","cpi","fiscal"],
}

st.markdown('<p class="sec-title">📰 News + Sector Intelligence</p>', unsafe_allow_html=True)

nav_col, content_col = st.columns([1, 3])

with nav_col:
    st.markdown('<div class="sec-nav-lbl">Select Sector</div>', unsafe_allow_html=True)
    for sec in ALL_SECTORS:
        is_active = st.session_state.sel_sector == sec
        btn_label = f"**{sec}**" if is_active else sec
        if st.button(sec, key=f"btn_{sec}", use_container_width=True):
            st.session_state.sel_sector = sec
            st.rerun()

with content_col:
    sel = st.session_state.sel_sector

    def filter_news_by_sector(arts, sector):
        if sector == "🌐 All News": return arts
        kws = SECTOR_KW_MAP.get(sector, [])
        return [a for a in arts if any(k in (a["title"]+" "+a.get("desc","")).lower() for k in kws)]

    # Get news for selected sector
    if sel == "🌐 All News":
        sec_arts      = news
        sec_indian    = indian_news
        sec_global    = global_news
    else:
        with st.spinner(f"Loading {sel} news..."):
            fresh         = fetch_sector_news(sel)
        sec_arts      = fresh
        sec_indian    = [a for a in fresh if a.get("indian", True)]
        sec_global    = [a for a in fresh if not a.get("indian", False)]

    # Sector intelligence header (for non-All views)
    if sel != "🌐 All News":
        scores    = [a["score"] for a in sec_arts]
        avg_score = sum(scores)/len(scores) if scores else 0
        pos_c     = sum(1 for s in scores if s > 0.05)
        neg_c     = sum(1 for s in scores if s < -0.05)
        if avg_score > 0.05:    mood, mc = "Bullish 📈", "#276749"
        elif avg_score < -0.05: mood, mc = "Bearish 📉", "#C53030"
        else:                   mood, mc = "Neutral ➡️",  "#B7791F"

        # Sector mood summary — fully data-grounded
        summary_line = (
            f"{len(sec_arts)} market-moving stories found today. "
            f"{pos_c} positive, {neg_c} negative signals. "
            f"Overall sector sentiment: {mood.split()[0]}."
        )

        st.markdown(f"""
        <div style="background:#F7FAFC;border:1px solid #E2E8F0;border-radius:10px;
                    padding:14px 16px;margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;align-items:center;
                      flex-wrap:wrap;gap:10px">
            <div>
              <div style="font-size:10px;font-weight:700;letter-spacing:1px;
                          text-transform:uppercase;color:#A0AEC0">Sector Mood Today</div>
              <div style="font-family:Syne,sans-serif;font-size:20px;
                          font-weight:800;color:{mc};margin-top:3px">{mood}</div>
              <div style="font-size:11px;color:#718096;margin-top:3px">{summary_line}</div>
            </div>
            <div style="display:flex;gap:14px;font-size:12px">
              <span style="color:#276749;font-weight:600">🟢 {pos_c} positive</span>
              <span style="color:#C53030;font-weight:600">🔴 {neg_c} negative</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Sector stock movers
        movers = SECTOR_STOCKS.get(sel, [])
        if movers:
            mover_html = ""
            for t in movers[:5]:
                d = yf_quote(t)
                if d and d.get("price"):
                    chg = d["chg"] or 0
                    mc2 = "#276749" if chg >= 0 else "#C53030"
                    bg2 = "#F0FFF4" if chg >= 0 else "#FFF5F5"
                    bc2 = "#9AE6B4" if chg >= 0 else "#FEB2B2"
                    mover_html += f"""
                    <div style="display:inline-block;background:{bg2};border:1px solid {bc2};
                                border-radius:8px;padding:7px 12px;margin:3px;text-align:center">
                      <div style="font-family:Syne,sans-serif;font-weight:800;
                                  font-size:12px;color:#1A202C">{t.replace('.NS','')}</div>
                      <div style="font-size:11px;font-weight:700;color:{mc2}">
                        {d['arrow']} {abs(chg):.2f}%
                      </div>
                    </div>"""
            if mover_html:
                st.markdown(f"""
                <div style="margin-bottom:14px">
                  <div style="font-size:10px;font-weight:700;letter-spacing:1px;
                              text-transform:uppercase;color:#A0AEC0;margin-bottom:6px">
                    Sector Stocks Today
                  </div>
                  {mover_html}
                </div>""", unsafe_allow_html=True)

    # News tabs
    tab_labels = (
        [f"🇮🇳 Indian ({len(sec_indian)})", f"🌍 Global ({len(sec_global)})"]
        if sel != "🌐 All News"
        else [f"🇮🇳 Indian ({len(sec_indian)})",
              f"🌍 Global ({len(sec_global)})",
              f"📋 All ({len(sec_arts)})"]
    )
    tabs     = st.tabs(tab_labels)
    tab_data = [(tabs[0], sec_indian), (tabs[1], sec_global)]
    if sel == "🌐 All News":
        tab_data.append((tabs[2], sec_arts))

    def render_news(articles):
        if not articles:
            st.markdown("""
            <div style="background:#F7FAFC;border:2px dashed #E2E8F0;border-radius:10px;
                        padding:24px;text-align:center;color:#A0AEC0">
              <div style="font-size:22px;margin-bottom:6px">📭</div>
              <div style="font-size:13px;font-weight:600;color:#718096">
                No market-moving stories found right now
              </div>
              <div style="font-size:11px;margin-top:4px">
                Try a different sector or click Refresh Now
              </div>
            </div>""", unsafe_allow_html=True)
            return
        for art in articles[:12]:
            short_title = art["title"][:105] + ("…" if len(art["title"]) > 105 else "")
            with st.expander(f"{art['emoji']}  {short_title}  ·  *{art['source']}*",
                             expanded=False):
                for line in (art.get("summary") or []):
                    if line.strip():
                        st.markdown(f"""
                        <div style="font-size:13px;color:#2D3748;line-height:1.6;
                                    padding:4px 0 4px 10px;border-left:3px solid #BEE3F8;
                                    margin-bottom:6px">{line}</div>""",
                                    unsafe_allow_html=True)
                secs_html = "".join(f'<span class="sec-tag">{s}</span>'
                                    for s in art.get("sectors", []))
                read_lnk  = (f"<a href='{art['url']}' target='_blank' "
                             f"style='font-size:11px;color:#2B6CB0;text-decoration:none'>"
                             f"Read original ↗</a>"
                             if art.get("url") and art["url"] != "#" else "")
                fresh_tag = ('<span style="font-size:10px;color:#276749;font-weight:600;'
                             'margin-left:6px">⚡ Google News</span>'
                             if art.get("from_google") else "")
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            flex-wrap:wrap;gap:6px;margin-top:8px;padding-top:8px;
                            border-top:1px solid #EDF2F7">
                  <div>{secs_html}</div>
                  <div style="display:flex;align-items:center;gap:8px">
                    <span class="src-badge">📰 {art['source']}</span>
                    <span style="font-size:11px;font-weight:600;color:{art['color']}">{art['label']}</span>
                    {fresh_tag}
                    {read_lnk}
                  </div>
                </div>""", unsafe_allow_html=True)

    for tab, articles in tab_data:
        with tab:
            render_news(articles)

    st.markdown(f"""
    <div style="font-size:10px;color:#A0AEC0;margin-top:8px;text-align:right">
      🔍 {len(news)} market-moving stories today · Opinion &amp; listicles filtered ·
      Sources: ET · BS · Mint · Moneycontrol · NDTV Profit · Google News · BBC · CNN
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══ SECTION 3: FII/DII ═══════════════════════════════════
st.markdown('<p class="sec-title">🏦 FII / DII Institutional Activity</p>',
            unsafe_allow_html=True)

badge_cls  = "live-badge" if fii_live else "demo-badge"
badge_text = f"🟢 Live · {fii_source}" if fii_live else f"⚠️ {fii_source}"

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:12px;flex-wrap:wrap;gap:8px">
  <div style="font-size:11px;color:#718096">
    FII = Foreign Institutional Investors · DII = Domestic Institutional Investors ·
    Values in ₹ Crore
  </div>
  <span class="data-badge {badge_cls}">{badge_text} · As of {fii_as_of}</span>
</div>""", unsafe_allow_html=True)

if fii_rows:
    latest = fii_rows[0]
    fn     = latest.get("fii_net", 0)
    dn     = latest.get("dii_net", 0)
    fhex   = "#276749" if fn >= 0 else "#C53030"
    dhex   = "#276749" if dn >= 0 else "#C53030"
    chex   = "#276749" if (fn+dn) >= 0 else "#C53030"

    c1, c2, c3 = st.columns(3)
    with c1:
        cls = "fii-buy" if fn >= 0 else "fii-sell"
        st.markdown(f"""
        <div class="{cls}">
          <div class="cmd-label">FII Net — {latest.get('date','')}</div>
          <div class="fii-val" style="color:{fhex}">
            {'+'if fn>=0 else ''}₹{abs(fn):,.0f} Cr
          </div>
          <div class="fii-lbl">
            Buy: ₹{latest.get('fii_buy',0):,.0f} · Sell: ₹{latest.get('fii_sell',0):,.0f}
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        cls = "fii-buy" if dn >= 0 else "fii-sell"
        st.markdown(f"""
        <div class="{cls}">
          <div class="cmd-label">DII Net — {latest.get('date','')}</div>
          <div class="fii-val" style="color:{dhex}">
            {'+'if dn>=0 else ''}₹{abs(dn):,.0f} Cr
          </div>
          <div class="fii-lbl">
            Buy: ₹{latest.get('dii_buy',0):,.0f} · Sell: ₹{latest.get('dii_sell',0):,.0f}
          </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        combined = fn + dn
        cls = "fii-buy" if combined >= 0 else "fii-sell"
        st.markdown(f"""
        <div class="{cls}">
          <div class="cmd-label">Combined Net Flow</div>
          <div class="fii-val" style="color:{chex}">
            {'+'if combined>=0 else ''}₹{abs(combined):,.0f} Cr
          </div>
          <div class="fii-lbl">
            {'Net buyers — positive for markets' if combined>=0 else 'Net sellers — watch support levels'}
          </div>
        </div>""", unsafe_allow_html=True)

    # 30-day Plotly chart
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    st.markdown("**📊 30-Day FII / DII Net Flow Trend (₹ Crore)**")
    try:
        import plotly.graph_objects as go
        chart_rows = list(reversed(fii_rows[:30]))
        dates   = [r["date"] for r in chart_rows]
        fii_net = [r.get("fii_net", 0) for r in chart_rows]
        dii_net = [r.get("dii_net", 0) for r in chart_rows]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates, y=fii_net, name="FII Net",
            marker_color=["#38A169" if v >= 0 else "#E53E3E" for v in fii_net],
            opacity=0.85
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=dii_net, name="DII Net",
            mode="lines+markers",
            line=dict(color="#2B6CB0", width=2),
            marker=dict(size=4)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#A0AEC0", line_width=1)
        fig.update_layout(
            height=280, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F8FAFC",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(size=11, color="#4A5568")),
            xaxis=dict(showgrid=False, color="#A0AEC0", tickfont=dict(size=9),
                       tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor="#EDF2F7",
                       color="#A0AEC0", tickfont=dict(size=9),
                       tickprefix="₹", ticksuffix=" Cr"),
            barmode="overlay",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")

    # Monthly summary table
    st.markdown("**📅 Recent Daily Activity**")
    table_rows = []
    for r in fii_rows[:10]:
        fn2 = r.get("fii_net", 0); dn2 = r.get("dii_net", 0)
        table_rows.append({
            "Date": r.get("date",""),
            "FII Net (₹Cr)": f"{'+'if fn2>=0 else ''}{fn2:,.0f}",
            "DII Net (₹Cr)": f"{'+'if dn2>=0 else ''}{dn2:,.0f}",
            "Combined":      f"{'+'if (fn2+dn2)>=0 else ''}{(fn2+dn2):,.0f}",
            "Signal":        "Buyers" if (fn2+dn2)>=0 else "Sellers",
        })
    try:
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True,
                     hide_index=True, height=280)
    except Exception:
        for r in table_rows[:5]:
            st.write(r)

    st.markdown(f"""
    <div style="font-size:10px;color:#A0AEC0;margin-top:6px">
      Source: {fii_source} · Data as of {fii_as_of} ·
      {'Live data' if fii_live else 'Demo data shown — live sources unavailable on current deployment'}
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══ SECTION 4: SECTOR WATCH ══════════════════════════════
st.markdown('<p class="sec-title">🏭 Sector Watch</p>', unsafe_allow_html=True)
sec_scores_dict = {}
for art in news:
    for s in art.get("sectors", []):
        sec_scores_dict.setdefault(s, []).append(art["score"])
sec_avg_dict = {k: sum(v)/len(v) for k, v in sec_scores_dict.items() if v}
sec_sorted   = sorted(sec_avg_dict.items(), key=lambda x: x[1], reverse=True)
if sec_sorted:
    hot  = sec_sorted[:3]
    cold = sec_sorted[-3:] if len(sec_sorted) >= 3 else []
    wc1, wc2 = st.columns(2)
    with wc1:
        st.markdown("**🔥 In Focus Today**")
        for sec, _ in hot:
            ref = next((a["title"][:70]+"…" for a in news if sec in a.get("sectors",[])), "")
            st.markdown(f"""
            <div class="sec-hot">
              <div class="sec-name">▲ {sec}</div>
              <div class="sec-reason">{ref}</div>
            </div>""", unsafe_allow_html=True)
    with wc2:
        st.markdown("**❄️ Under Pressure**")
        for sec, _ in cold:
            ref = next((a["title"][:70]+"…" for a in news if sec in a.get("sectors",[])), "")
            st.markdown(f"""
            <div class="sec-cold">
              <div class="sec-name">▼ {sec}</div>
              <div class="sec-reason">{ref}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("Sector data loading with news feed...")

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══ SECTION 5: MARKET EVENTS CALENDAR ════════════════════
st.markdown('<p class="sec-title">📅 Market Events Calendar — India & Global</p>',
            unsafe_allow_html=True)
if events:
    ecols = st.columns(2)
    for i, ev in enumerate(events):
        with ecols[i % 2]:
            days = ev.get("days_away", 0)
            if days == 0:    when = "🔴 TODAY"
            elif days == 1:  when = "🟠 Tomorrow"
            elif days <= 7:  when = f"🟡 In {days} days"
            else:            when = f"📅 {ev['date_fmt']}"
            st.markdown(f"""
            <div class="cal-item" style="border-left-color:{ev.get('color','#2B6CB0')}">
              <div class="cal-date">{when} &nbsp;·&nbsp; {ev['type']}</div>
              <div class="cal-title">{ev['title']}</div>
              <div class="cal-sub">{ev['detail']}</div>
            </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

# ══ SECTION 6: ECONOMIC PULSE ════════════════════════════
st.markdown('<p class="sec-title">🌐 Economic Pulse</p>', unsafe_allow_html=True)

# Part A: India Macro (official data, clearly dated)
st.markdown("""
<div style="font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;
            color:#2B6CB0;margin-bottom:8px">🇮🇳 India Macro — Latest Official Data</div>""",
            unsafe_allow_html=True)
st.markdown("""
<div style="font-size:10px;color:#A0AEC0;margin-bottom:12px;padding:6px 10px;
            background:#EBF8FF;border-radius:6px">
  ℹ️ Figures from latest RBI / MOSPI / Finance Ministry releases.
  Date shown on each card so you always know how fresh it is.
</div>""", unsafe_allow_html=True)

macro = eco.get("macro", [])
for i in range(0, len(macro), 3):
    batch = macro[i:i+3]
    mcols = st.columns(len(batch))
    for col, item in zip(mcols, batch):
        with col:
            c = item.get("color", "#B7791F")
            st.markdown(f"""
            <div class="eco-card" style="border-left:4px solid {c}">
              <div class="eco-lbl">{item['indicator']}</div>
              <div class="eco-val" style="color:{c}">{item['value']}</div>
              <div style="font-size:11px;font-weight:600;color:{c};margin:3px 0">{item['change']}</div>
              <div class="eco-note">{item['note']}</div>
              <div style="font-size:10px;color:#A0AEC0;margin-top:5px">
                📅 {item['date']} · {item['source']}
              </div>
            </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)

# Part B: Live market indicators
st.markdown("""
<div style="font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;
            color:#276749;margin-bottom:8px">📊 Live Market Indicators — Real Time</div>""",
            unsafe_allow_html=True)

ivix_d = eco.get("ivix", {}); vix_d = eco.get("vix", {})
yc     = eco.get("yield", {}); inr_d = eco.get("inr") or {}
gold_d = eco.get("gold") or {}; oil_d = eco.get("oil") or {}

lc1, lc2, lc3 = st.columns(3)
with lc1:
    ivv = ivix_d.get("val")
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">India VIX (Fear)</div>
      <div class="eco-val" style="color:{ivix_d.get('color','#B7791F')}">{f'{ivv:.1f}' if ivv else '–'}</div>
      <div class="eco-note">{ivix_d.get('mood','Loading...')}</div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:4px">Live · Yahoo Finance</div>
    </div>""", unsafe_allow_html=True)

with lc2:
    vv = vix_d.get("val")
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">US VIX (Global Fear)</div>
      <div class="eco-val" style="color:{vix_d.get('color','#B7791F')}">{f'{vv:.1f}' if vv else '–'}</div>
      <div class="eco-note">{vix_d.get('mood','Loading...')}</div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:4px">Live · Yahoo Finance</div>
    </div>""", unsafe_allow_html=True)

with lc3:
    t10s = f"{yc.get('t10'):.2f}%" if yc.get("t10") else "–"
    t30s = f"{yc.get('t30'):.2f}%" if yc.get("t30") else "–"
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">US Yield Curve</div>
      <div class="eco-val" style="color:{yc.get('color','#B7791F')}">{yc.get('sig','–')}</div>
      <div class="eco-note">{yc.get('note','–')}</div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:4px">
        10yr: {t10s} · 30yr: {t30s} · Live
      </div>
    </div>""", unsafe_allow_html=True)

lc4, lc5, lc6 = st.columns(3)
with lc4:
    iv = inr_d.get("price"); ic = inr_d.get("chg", 0) or 0
    icc = "#C53030" if ic > 0 else "#276749"
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">USD / INR</div>
      <div class="eco-val">{'₹'+str(round(iv,2)) if iv else '–'}</div>
      <div class="eco-note" style="color:{icc}">
        {'Rupee weakening ↓' if ic>0 else 'Rupee strengthening ↑'} {abs(ic):.2f}% today
      </div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:4px">Live · Yahoo Finance</div>
    </div>""", unsafe_allow_html=True)

with lc5:
    gv = gold_d.get("price"); gc2 = gold_d.get("chg", 0) or 0
    gcc = "#276749" if gc2 > 0 else "#C53030"
    gmsg = "Rising — safe haven demand" if gc2>1.5 else ("Falling — risk-on mood" if gc2<-1.5 else "Stable today")
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">Gold (Safe Haven)</div>
      <div class="eco-val">{'$'+str(round(gv,0)) if gv else '–'}</div>
      <div class="eco-note" style="color:{gcc}">{gmsg} {abs(gc2):.2f}%</div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:4px">Live · Yahoo Finance</div>
    </div>""", unsafe_allow_html=True)

with lc6:
    ov = oil_d.get("price"); oc2 = oil_d.get("chg", 0) or 0
    occ = "#C53030" if oc2 > 1 else ("#276749" if oc2 < -1 else "#B7791F")
    omsg = "Rising oil — higher import bill for India" if oc2>1 else ("Falling oil — positive for India" if oc2<-1 else "Stable")
    st.markdown(f"""
    <div class="eco-card">
      <div class="eco-lbl">Crude Oil WTI</div>
      <div class="eco-val">{'$'+str(round(ov,2)) if ov else '–'}</div>
      <div class="eco-note" style="color:{occ}">{omsg}</div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:4px">Live · Yahoo Finance</div>
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="fp-div"></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # close wrap

# FOOTER
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
    All times in IST (UTC+5:30) · Auto-refresh every 1 hour ·
    Sources: NSE India · Yahoo Finance · ET · Mint · BS · Moneycontrol · NDTV Profit ·
    RBI · MOSPI · Google News · BBC · CNN · Not Financial Advice · {now_ist().year}
  </div>
</div>""", unsafe_allow_html=True)
