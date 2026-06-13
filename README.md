# 📡 FinPulse by Anoop Puri
### Smart Financial Intelligence — India First, World Coverage

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://finpulse.streamlit.app)

> Free. No login. No paid APIs. Built for Indian investors and traders.

---

## What FinPulse Does

### 📊 Command Center
- Indian indices live: Nifty 50, Sensex, Bank Nifty, Nifty IT, Nifty Pharma
- Global: S&P 500, Gold, Oil, USD/INR, Bitcoin
- Fear & Greed Index — calculated from real market data

### 📰 News + Sector Intelligence
- **17 sector categories** with left-side navigation
- Click any sector → see sector mood, top stock movers, filtered news
- Sources: Economic Times, Business Standard, Mint, Moneycontrol, NDTV Profit, Google News, BBC, CNN
- Strict filter: opinion pieces and listicles removed automatically
- Each story shows source, sentiment, sector tags, "Read original" link

### 🏦 FII / DII Institutional Activity
- Tries NSE India → Trendlyne → Moneycontrol in sequence
- 30-day trend chart (Plotly)
- Daily activity table with ₹ Crore values
- Always shows: Data as of DD-MMM-YYYY · Source: XYZ

### 🏭 Sector Watch
- Hot sectors (most positive news today)
- Under pressure sectors (most negative news today)
- Linked to today's actual news stories

### 📅 Market Events Calendar
- RBI MPC meeting dates
- F&O expiry dates  
- US Fed FOMC meetings
- Earnings season dates
- Union Budget date

### 🌐 Economic Pulse
**Part A — India Macro (official data, clearly dated):**
RBI Repo Rate · CPI Inflation · GDP Growth · Forex Reserves · IIP · Fiscal Deficit

**Part B — Live Market Indicators (real-time):**
India VIX · US VIX · Yield Curve · USD/INR · Gold · Crude Oil

---

## Tech Stack (100% Free)
| Tool | Purpose |
|---|---|
| Streamlit | Web app framework |
| streamlit-autorefresh | Hourly auto-refresh |
| Yahoo Finance Chart API | Live prices, VIX, yields |
| Google News RSS | Keyword-based fresh news |
| NSE India API | FII/DII institutional data |
| Trendlyne / Moneycontrol | FII/DII fallback sources |
| ET, BS, Mint, Moneycontrol RSS | Indian financial news |
| BBC, CNN, Yahoo RSS | Global news |
| VADER Sentiment | NLP sentiment scoring |
| Plotly | Interactive FII/DII chart |
| ReportLab | PDF generation |
| GitHub + Streamlit Cloud | Free hosting |

---

## Deploy (2 files only)
```
1. Push app.py and requirements.txt to GitHub
2. Go to share.streamlit.io
3. Connect repo → Main file: app.py
4. Deploy — live in 3 minutes
```

---

## Connect
- 📸 Instagram: [@theanooppuri](https://instagram.com/theanooppuri)
- 💼 LinkedIn: [@theanooppuri](https://linkedin.com/in/theanooppuri)

---

*FinPulse by Anoop Puri — AI for Finance Certificate Project*
*All times in IST (UTC+5:30) · Not Financial Advice*
