# 📡 FinPulse by Anoop Puri
### Smart Financial Intelligence for Every Investor — Free Forever

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://finpulse.streamlit.app)

---

## What is FinPulse?
FinPulse is a free, AI-powered financial intelligence platform built from scratch
for retail investors, students, and finance enthusiasts who want professional-quality
market intelligence without the cost or complexity of traditional platforms.

**Built 100% on free tools. No login. No cost. Just intelligence.**

---

## Features

### 📊 Core Intelligence (7 sections)
| Feature | Description |
|---|---|
| Live Market Snapshot | Global indices, commodities, crypto, currencies — real time |
| Fear & Greed Index | Calculated in real time from multiple market signals |
| AI-Filtered News | Top stories with 3-line summaries + source, click to expand |
| Reddit Pulse | Live sentiment from r/investing, r/wallstreetbets, r/stocks |
| Sector Watch | Hot and cold sectors connected to today's news |
| Under-the-Radar Story | Lowest-sentiment story worth monitoring |
| Data-Grounded Summary | Every statement cites a real number and source |
| PDF Download | Full 7-page brief downloadable instantly |
| Auto-Refresh | Every 1 hour automatically + manual refresh button |

### ⚡ Advanced Intelligence Suite (7 sections)
| Feature | What it does |
|---|---|
| **Technical Signal Scanner** | RSI, MACD, Bollinger Bands, MA Cross, Volume — signal for any global ticker |
| **Portfolio Intelligence Hub** | Track any global stocks — live P&L, Beta, diversification, sector allocation |
| **Economic Pulse** | VIX, Yield Curve, Dollar Index, GDP growth, Gold signal |
| **Earnings Radar** | Major earnings this week and next with live prices |
| **News → Market Impact** | Links each news story to the stocks it directly affects |
| **Asset Correlation Matrix** | Interactive heatmap — how 10 global assets move relative to each other |
| **Insider Activity** | SEC EDGAR Form 4 filings — who's buying their own company's stock |

---

## 🛠️ Tech Stack (100% Free)
| Tool | Purpose |
|---|---|
| Streamlit | Web app framework |
| streamlit-autorefresh | Automatic hourly refresh |
| Yahoo Finance Chart API | Live prices, historical data |
| SEC EDGAR API | Insider filing data |
| World Bank API | GDP, CPI, unemployment data |
| RSS Feeds (BBC, CNN, Yahoo) | Global financial news |
| VADER Sentiment | NLP sentiment scoring |
| Plotly | Interactive charts |
| ReportLab | PDF generation |
| GitHub + Streamlit Cloud | Free hosting and deployment |

---

## 📁 Project Structure
```
finpulse/
├── app.py                          ← Main Streamlit app
├── requirements.txt                ← All packages needed
├── README.md                       ← This file
└── modules/
    ├── __init__.py
    ├── technical.py                ← RSI, MACD, Bollinger, MA signals
    ├── portfolio.py                ← P&L, Beta, allocation analysis
    ├── economic.py                 ← VIX, yield curve, macro data
    └── market_intelligence.py     ← Earnings, correlation, insider, news impact
```

---

## ⚡ Run Locally
```bash
git clone https://github.com/theanooppuri/finpulse
cd finpulse
pip install -r requirements.txt
streamlit run app.py
```

---

## 🚀 Deploy to Streamlit Cloud (Free)
1. Push to your GitHub repo
2. Go to share.streamlit.io
3. Connect your repo → Main file path: app.py
4. Deploy — live in 3 minutes

---

## Connect with Anoop Puri
- 📸 Instagram: [@theanooppuri](https://instagram.com/theanooppuri)
- 💼 LinkedIn: [@theanooppuri](https://linkedin.com/in/theanooppuri)

---

*FinPulse by Anoop Puri — AI for Finance Certificate Project*
*Built 100% on Free Tools — No paid APIs, No login required*
