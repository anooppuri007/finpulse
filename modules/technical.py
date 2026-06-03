# ═══════════════════════════════════════════════════════════
#  FinPulse — Technical Analysis Module
#  Calculates RSI, MACD, Bollinger Bands, MA signals
#  Uses Yahoo Finance chart API (free, no key needed)
# ═══════════════════════════════════════════════════════════

import requests
import pandas as pd
import numpy as np
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinPulse/1.0)"}

# ── Top global stocks to scan by default ─────────────────
DEFAULT_TICKERS = {
    # US Tech
    "AAPL":  "Apple",
    "MSFT":  "Microsoft",
    "NVDA":  "NVIDIA",
    "GOOGL": "Alphabet",
    "AMZN":  "Amazon",
    # US Finance
    "JPM":   "JPMorgan",
    "GS":    "Goldman Sachs",
    # Global
    "TSM":   "TSMC",
    "BABA":  "Alibaba",
    "TCS.NS":"TCS India",
    # ETFs
    "SPY":   "S&P 500 ETF",
    "QQQ":   "NASDAQ ETF",
    "GLD":   "Gold ETF",
    # Crypto
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
}


def _fetch_history(ticker, period="6mo", interval="1d"):
    """Fetch OHLCV data from Yahoo Finance chart API."""
    try:
        period_map = {"1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y"}
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
               f"?range={period_map.get(period,'6mo')}&interval={interval}"
               f"&includePrePost=false&corsDomain=finance.yahoo.com")
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None

        data  = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None

        timestamps = result[0]["timestamp"]
        ohlcv = result[0]["indicators"]["quote"][0]

        df = pd.DataFrame({
            "date":   pd.to_datetime(timestamps, unit="s"),
            "open":   ohlcv.get("open", []),
            "high":   ohlcv.get("high", []),
            "low":    ohlcv.get("low", []),
            "close":  ohlcv.get("close", []),
            "volume": ohlcv.get("volume", []),
        }).dropna(subset=["close"])

        df.set_index("date", inplace=True)
        return df

    except Exception:
        return None


def _rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).iloc[-1]


def _macd(series, fast=12, slow=26, sig=9):
    ema_f  = series.ewm(span=fast, adjust=False).mean()
    ema_s  = series.ewm(span=slow, adjust=False).mean()
    macd   = ema_f - ema_s
    signal = macd.ewm(span=sig, adjust=False).mean()
    hist   = macd - signal
    return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])


def _bollinger(series, period=20, std_mult=2):
    sma   = series.rolling(period).mean()
    std   = series.rolling(period).std()
    upper = sma + std_mult * std
    lower = sma - std_mult * std
    cur   = float(series.iloc[-1])
    u, m, l = float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])
    pct   = (cur - l) / (u - l) if (u - l) > 0 else 0.5
    return u, m, l, round(pct * 100, 1)


def _moving_averages(series):
    sma50  = float(series.rolling(50).mean().iloc[-1])
    sma200 = float(series.rolling(200).mean().iloc[-1])
    ema20  = float(series.ewm(span=20, adjust=False).mean().iloc[-1])
    cur    = float(series.iloc[-1])
    return sma50, sma200, ema20, cur


def analyze_ticker(ticker):
    """
    Full technical analysis for one ticker.
    Returns dict with all indicators + overall signal.
    """
    df = _fetch_history(ticker, "6mo")
    if df is None or len(df) < 30:
        return _demo_signal(ticker)

    close  = df["close"].astype(float)
    volume = df["volume"].astype(float)

    # ── Indicators ─────────────────────────────────────────
    rsi_val            = _rsi(close)
    macd_val, sig_val, hist_val = _macd(close)
    bb_u, bb_m, bb_l, bb_pct    = _bollinger(close)
    sma50, sma200, ema20, price  = _moving_averages(close)

    # Volume trend
    avg_vol   = float(volume.rolling(20).mean().iloc[-1])
    cur_vol   = float(volume.iloc[-1])
    vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1.0

    # 5-day momentum
    momentum  = ((price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100
                 if len(close) >= 6 else 0)

    # ── Signal scoring ─5 to +5 ─────────────────────────
    score    = 0
    signals  = []

    # RSI
    rsi_val = round(float(rsi_val), 1)
    if rsi_val < 30:
        score += 2
        signals.append(("RSI", f"{rsi_val}", "Oversold — Strong buy zone", "green"))
    elif rsi_val < 45:
        score += 1
        signals.append(("RSI", f"{rsi_val}", "Approaching oversold — Watch", "green"))
    elif rsi_val > 70:
        score -= 2
        signals.append(("RSI", f"{rsi_val}", "Overbought — Consider taking profits", "red"))
    elif rsi_val > 55:
        score -= 1
        signals.append(("RSI", f"{rsi_val}", "Approaching overbought — Caution", "red"))
    else:
        signals.append(("RSI", f"{rsi_val}", "Neutral zone (30–55)", "yellow"))

    # MACD
    if macd_val > sig_val and hist_val > 0:
        score += 2
        signals.append(("MACD", f"{macd_val:.3f}", "Above signal & rising — Bullish momentum", "green"))
    elif macd_val > sig_val:
        score += 1
        signals.append(("MACD", f"{macd_val:.3f}", "Above signal line — Mildly bullish", "green"))
    elif macd_val < sig_val and hist_val < 0:
        score -= 2
        signals.append(("MACD", f"{macd_val:.3f}", "Below signal & falling — Bearish momentum", "red"))
    else:
        score -= 1
        signals.append(("MACD", f"{macd_val:.3f}", "Below signal line — Mildly bearish", "red"))

    # MA Cross (Golden/Death)
    if sma50 > sma200 and price > sma50:
        score += 2
        signals.append(("MA Cross", f"50MA: {sma50:.1f}", "Golden Cross — Strong uptrend", "green"))
    elif sma50 > sma200:
        score += 1
        signals.append(("MA Cross", f"50MA: {sma50:.1f}", "Golden Cross but below 50MA — Caution", "yellow"))
    elif sma50 < sma200 and price < sma50:
        score -= 2
        signals.append(("MA Cross", f"50MA: {sma50:.1f}", "Death Cross — Strong downtrend", "red"))
    else:
        score -= 1
        signals.append(("MA Cross", f"50MA: {sma50:.1f}", "Death Cross — Watch for reversal", "yellow"))

    # Bollinger Bands
    if bb_pct < 15:
        score += 1
        signals.append(("Bollinger", f"{bb_pct:.0f}%", "Near lower band — Potential bounce", "green"))
    elif bb_pct > 85:
        score -= 1
        signals.append(("Bollinger", f"{bb_pct:.0f}%", "Near upper band — Potential pullback", "red"))
    else:
        signals.append(("Bollinger", f"{bb_pct:.0f}%", f"Mid-band position — No extreme signal", "yellow"))

    # Volume confirmation
    if vol_ratio > 1.5 and score > 0:
        score += 1
        signals.append(("Volume", f"{vol_ratio:.1f}x avg", "High volume confirms bullish move", "green"))
    elif vol_ratio > 1.5 and score < 0:
        score -= 1
        signals.append(("Volume", f"{vol_ratio:.1f}x avg", "High volume confirms bearish move", "red"))
    else:
        signals.append(("Volume", f"{vol_ratio:.1f}x avg", "Normal volume — No confirmation signal", "yellow"))

    # ── Overall signal ─────────────────────────────────────
    if score >= 5:
        overall, oc = "STRONG BUY",  "green"
    elif score >= 2:
        overall, oc = "BUY",         "green"
    elif score <= -5:
        overall, oc = "STRONG SELL", "red"
    elif score <= -2:
        overall, oc = "SELL",        "red"
    else:
        overall, oc = "NEUTRAL",     "yellow"

    # Price change
    prev_close = float(close.iloc[-2]) if len(close) > 1 else price
    chg_pct    = round((price - prev_close) / prev_close * 100, 2)

    return {
        "ticker":   ticker,
        "name":     DEFAULT_TICKERS.get(ticker, ticker),
        "price":    round(price, 2),
        "chg_pct":  chg_pct,
        "rsi":      rsi_val,
        "macd":     round(macd_val, 4),
        "macd_sig": round(sig_val, 4),
        "bb_pct":   bb_pct,
        "sma50":    round(sma50, 2),
        "sma200":   round(sma200, 2),
        "momentum": round(momentum, 2),
        "vol_ratio":round(vol_ratio, 2),
        "score":    score,
        "signals":  signals,
        "overall":  overall,
        "overall_color": oc,
        "history":  df[["close", "volume"]].tail(90),
        "live": True,
    }


def _demo_signal(ticker):
    """Fallback demo signal when API unavailable."""
    import random
    score = random.randint(-4, 4)
    if score >= 2:   overall, oc = "BUY",     "green"
    elif score <= -2: overall, oc = "SELL",    "red"
    else:             overall, oc = "NEUTRAL", "yellow"
    return {
        "ticker": ticker, "name": DEFAULT_TICKERS.get(ticker, ticker),
        "price": 0, "chg_pct": 0, "rsi": 50, "macd": 0,
        "macd_sig": 0, "bb_pct": 50, "sma50": 0, "sma200": 0,
        "momentum": 0, "vol_ratio": 1.0, "score": score,
        "signals": [
            ("RSI",      "50.0", "Data unavailable — API loading",     "yellow"),
            ("MACD",     "0.000","Data unavailable — API loading",     "yellow"),
            ("MA Cross", "N/A",  "Data unavailable — API loading",     "yellow"),
            ("Bollinger","50%",  "Data unavailable — API loading",     "yellow"),
            ("Volume",   "1.0x", "Data unavailable — API loading",     "yellow"),
        ],
        "overall": overall, "overall_color": oc,
        "history": None, "live": False,
    }


def scan_tickers(tickers=None):
    """Scan multiple tickers and return sorted results."""
    tickers = tickers or list(DEFAULT_TICKERS.keys())[:10]
    results = []
    for t in tickers:
        try:
            results.append(analyze_ticker(t))
        except Exception:
            results.append(_demo_signal(t))
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
