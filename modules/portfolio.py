# ═══════════════════════════════════════════════════════════
#  FinPulse — Portfolio Intelligence Module
#  Tracks holdings, calculates P&L, risk, allocation
#  Uses Yahoo Finance chart API (free, no key)
# ═══════════════════════════════════════════════════════════

import requests
import pandas as pd
import numpy as np
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinPulse/1.0)"}

# Sector mapping for common tickers
TICKER_SECTORS = {
    "AAPL":"Technology",  "MSFT":"Technology",  "NVDA":"Technology",
    "GOOGL":"Technology", "META":"Technology",   "AMZN":"Consumer",
    "TSLA":"Automotive",  "JPM":"Banking",       "GS":"Banking",
    "BAC":"Banking",      "WMT":"Consumer",      "COST":"Consumer",
    "XOM":"Energy",       "CVX":"Energy",        "JNJ":"Healthcare",
    "PFE":"Healthcare",   "V":"Banking",         "MA":"Banking",
    "BTC-USD":"Crypto",   "ETH-USD":"Crypto",    "GLD":"Commodities",
    "TCS.NS":"Technology","RELIANCE.NS":"Energy","HDFCBANK.NS":"Banking",
    "INFY.NS":"Technology","SPY":"ETF",          "QQQ":"ETF",
    "TSM":"Technology",   "BABA":"Consumer",     "NKE":"Consumer",
}

REGION_MAP = {
    ".NS": "India", ".BO": "India",
    ".L":  "UK",    ".PA": "France",
    ".DE": "Germany",
    "BTC-USD": "Crypto", "ETH-USD": "Crypto",
    "GLD": "Global", "SLV": "Global",
    "SPY": "USA",    "QQQ": "USA",
}


def get_live_price(ticker):
    """Fetch current price for a ticker."""
    try:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
               f"?range=5d&interval=1d&corsDomain=finance.yahoo.com")
        r   = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None, None, None

        data   = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None, None, None

        meta   = result[0]["meta"]
        price  = meta.get("regularMarketPrice", 0)
        prev   = meta.get("previousClose", price) or price
        name   = meta.get("shortName", ticker)
        chg    = round((price - prev) / prev * 100, 2) if prev else 0
        return round(float(price), 2), chg, name

    except Exception:
        return None, None, ticker


def get_beta(ticker):
    """Approximate beta from 1-year vs SPY correlation."""
    try:
        def fetch_closes(sym):
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                   f"?range=1y&interval=1wk&corsDomain=finance.yahoo.com")
            r   = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code != 200:
                return None
            data   = r.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            closes = result[0]["indicators"]["quote"][0].get("close", [])
            return pd.Series([c for c in closes if c]).pct_change().dropna()

        stock_ret = fetch_closes(ticker)
        spy_ret   = fetch_closes("SPY")

        if stock_ret is None or spy_ret is None or len(stock_ret) < 10:
            return 1.0

        min_len = min(len(stock_ret), len(spy_ret))
        sr = stock_ret.iloc[-min_len:].values
        mr = spy_ret.iloc[-min_len:].values
        cov = np.cov(sr, mr)[0][1]
        var = np.var(mr)
        return round(cov / var, 2) if var > 0 else 1.0

    except Exception:
        return 1.0


def analyze_portfolio(holdings):
    """
    Analyze portfolio. holdings = list of dicts:
    [{"ticker":"AAPL","shares":10,"buy_price":150}, ...]
    """
    if not holdings:
        return None

    results    = []
    total_cost = 0
    total_val  = 0

    for h in holdings:
        ticker    = h["ticker"].upper().strip()
        shares    = float(h["shares"])
        buy_price = float(h["buy_price"])
        cost      = shares * buy_price

        price, chg_pct, name = get_live_price(ticker)
        if price is None:
            price   = buy_price
            chg_pct = 0
            name    = ticker

        cur_val  = shares * price
        pl       = cur_val - cost
        pl_pct   = (pl / cost * 100) if cost > 0 else 0

        # Sector & Region
        sector = TICKER_SECTORS.get(ticker, "Other")
        region = "USA"
        for suffix, reg in REGION_MAP.items():
            if ticker.endswith(suffix) or ticker == suffix:
                region = reg
                break

        total_cost += cost
        total_val  += cur_val

        results.append({
            "ticker":    ticker,
            "name":      name or ticker,
            "shares":    shares,
            "buy_price": buy_price,
            "price":     price,
            "chg_pct":   chg_pct,
            "cost":      round(cost, 2),
            "value":     round(cur_val, 2),
            "pl":        round(pl, 2),
            "pl_pct":    round(pl_pct, 2),
            "sector":    sector,
            "region":    region,
            "weight":    0,  # filled below
        })

    # Weights
    for r in results:
        r["weight"] = round(r["value"] / total_val * 100, 1) if total_val > 0 else 0

    # Portfolio-level metrics
    total_pl     = total_val - total_cost
    total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0

    # Sector allocation
    sectors = {}
    for r in results:
        sectors[r["sector"]] = sectors.get(r["sector"], 0) + r["value"]

    # Region allocation
    regions = {}
    for r in results:
        regions[r["region"]] = regions.get(r["region"], 0) + r["value"]

    # Best/worst performers
    results_sorted = sorted(results, key=lambda x: x["pl_pct"], reverse=True)
    best   = results_sorted[0]  if results_sorted else None
    worst  = results_sorted[-1] if results_sorted else None

    # Weighted beta (approximate)
    betas = {}
    for r in results[:5]:  # limit API calls
        betas[r["ticker"]] = get_beta(r["ticker"])

    portfolio_beta = sum(
        r["weight"] / 100 * betas.get(r["ticker"], 1.0)
        for r in results
    )

    # Diversification score (0-100)
    n_sectors = len(sectors)
    n_assets  = len(results)
    max_weight = max(r["weight"] for r in results) if results else 100
    div_score  = min(100, int(
        (n_sectors / 8 * 30) +
        (n_assets  / 15 * 30) +
        ((100 - max_weight) / 100 * 40)
    ))

    # Risk level
    if portfolio_beta > 1.3 or div_score < 30:
        risk = "High Risk 🔴"
    elif portfolio_beta > 0.9 or div_score < 60:
        risk = "Moderate Risk 🟡"
    else:
        risk = "Low-Moderate Risk 🟢"

    return {
        "holdings":      results,
        "total_cost":    round(total_cost, 2),
        "total_value":   round(total_val,  2),
        "total_pl":      round(total_pl,   2),
        "total_pl_pct":  round(total_pl_pct, 2),
        "sectors":       {k: round(v/total_val*100, 1) for k,v in sectors.items()},
        "regions":       {k: round(v/total_val*100, 1) for k,v in regions.items()},
        "best":          best,
        "worst":         worst,
        "portfolio_beta":round(portfolio_beta, 2),
        "div_score":     div_score,
        "risk":          risk,
        "n_holdings":    len(results),
    }
