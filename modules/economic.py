# ═══════════════════════════════════════════════════════════
#  FinPulse — Economic Pulse Module
#  Global macro indicators from World Bank API (free)
#  + Yahoo Finance for VIX, Treasury yields
# ═══════════════════════════════════════════════════════════

import requests
import pandas as pd
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinPulse/1.0)"}


def _fetch_yf_quote(symbol):
    """Get single price from Yahoo Finance."""
    try:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?range=5d&interval=1d&corsDomain=finance.yahoo.com")
        r   = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None, None
        meta  = r.json()["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev  = meta.get("previousClose", price) or price
        chg   = round((price - prev) / prev * 100, 2)
        return round(float(price), 2), chg
    except Exception:
        return None, None


def _fetch_worldbank(indicator, country="US", years=5):
    """Fetch indicator from World Bank free API."""
    try:
        url = (f"https://api.worldbank.org/v2/country/{country}/"
               f"indicator/{indicator}?format=json&mrv={years}&per_page=10")
        r   = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        if len(data) < 2 or not data[1]:
            return []
        results = [
            {"year": int(d["date"]), "value": d["value"]}
            for d in data[1] if d["value"] is not None
        ]
        return sorted(results, key=lambda x: x["year"], reverse=True)
    except Exception:
        return []


def get_economic_pulse():
    """
    Fetch key macro economic indicators.
    Returns structured data for dashboard display.
    """

    # ── Market Fear Indicators ────────────────────────────
    vix,      vix_chg    = _fetch_yf_quote("^VIX")
    tnx,      tnx_chg    = _fetch_yf_quote("^TNX")     # 10yr Treasury yield
    tyx,      tyx_chg    = _fetch_yf_quote("^TYX")     # 30yr Treasury yield
    dxy,      dxy_chg    = _fetch_yf_quote("DX-Y.NYB") # Dollar index
    gold,     gold_chg   = _fetch_yf_quote("GC=F")
    oil,      oil_chg    = _fetch_yf_quote("CL=F")
    silver,   silver_chg = _fetch_yf_quote("SI=F")

    # ── Global GDP Growth (World Bank) ─────────────────────
    us_gdp   = _fetch_worldbank("NY.GDP.MKTP.KD.ZG", "US",  5)
    cn_gdp   = _fetch_worldbank("NY.GDP.MKTP.KD.ZG", "CN",  5)
    in_gdp   = _fetch_worldbank("NY.GDP.MKTP.KD.ZG", "IN",  5)
    eu_gdp   = _fetch_worldbank("NY.GDP.MKTP.KD.ZG", "EU",  5)

    # ── Inflation (World Bank CPI) ─────────────────────────
    us_cpi   = _fetch_worldbank("FP.CPI.TOTL.ZG", "US", 5)
    in_cpi   = _fetch_worldbank("FP.CPI.TOTL.ZG", "IN", 5)

    # ── Unemployment ──────────────────────────────────────
    us_unem  = _fetch_worldbank("SL.UEM.TOTL.ZS", "US", 5)
    in_unem  = _fetch_worldbank("SL.UEM.TOTL.ZS", "IN", 5)

    # ── VIX Interpretation ────────────────────────────────
    if vix:
        if vix < 15:
            vix_mood = "Complacent — Markets calm, risk appetite high"
            vix_color = "green"
        elif vix < 20:
            vix_mood = "Low — Investors comfortable, steady market"
            vix_color = "green"
        elif vix < 30:
            vix_mood = "Elevated — Some uncertainty, caution advised"
            vix_color = "yellow"
        elif vix < 40:
            vix_mood = "High — Fear in markets, increased volatility"
            vix_color = "red"
        else:
            vix_mood = "Extreme — Market panic, high risk environment"
            vix_color = "red"
    else:
        vix_mood = "Data loading..."
        vix_color = "yellow"

    # ── Yield Curve Analysis ──────────────────────────────
    yield_curve_signal = "Normal"
    yield_curve_color  = "green"
    yield_curve_note   = "Normal yield curve — economy healthy"
    if tnx and tyx:
        spread = round(tyx - tnx, 2)
        if spread < 0:
            yield_curve_signal = "Inverted"
            yield_curve_color  = "red"
            yield_curve_note   = f"Inverted curve (spread: {spread}%) — Recession warning signal"
        elif spread < 0.5:
            yield_curve_signal = "Flat"
            yield_curve_color  = "yellow"
            yield_curve_note   = f"Flat curve (spread: {spread}%) — Slowing growth signal"
        else:
            yield_curve_note   = f"Normal curve (spread: {spread}%) — Economy expanding"
    else:
        spread = None

    # ── Gold signal ───────────────────────────────────────
    gold_signal = "Neutral"
    gold_note   = "Gold stable — No extreme safe-haven demand"
    if gold and gold_chg:
        if gold_chg > 1.5:
            gold_signal = "Strong Safe-Haven Demand"
            gold_note   = f"Gold up {gold_chg}% — Markets seeking safety, risk-off mood"
        elif gold_chg < -1.5:
            gold_signal = "Risk-On"
            gold_note   = f"Gold down {gold_chg}% — Risk appetite improving, sell-off in safety assets"

    return {
        # Market indicators
        "vix":            {"value": vix,    "chg": vix_chg,    "mood": vix_mood,   "color": vix_color},
        "treasury_10yr":  {"value": tnx,    "chg": tnx_chg,    "label": "10-Yr Yield"},
        "treasury_30yr":  {"value": tyx,    "chg": tyx_chg,    "label": "30-Yr Yield"},
        "dollar_index":   {"value": dxy,    "chg": dxy_chg,    "label": "Dollar Index"},
        "gold":           {"value": gold,   "chg": gold_chg,   "signal": gold_signal, "note": gold_note},
        "oil":            {"value": oil,    "chg": oil_chg,    "label": "WTI Crude"},
        "silver":         {"value": silver, "chg": silver_chg, "label": "Silver"},
        # Yield curve
        "yield_curve":    {"signal": yield_curve_signal, "spread": spread,
                           "color": yield_curve_color,   "note": yield_curve_note},
        # GDP series
        "gdp": {
            "US":     us_gdp[:4]  if us_gdp  else [],
            "China":  cn_gdp[:4]  if cn_gdp  else [],
            "India":  in_gdp[:4]  if in_gdp  else [],
            "EU":     eu_gdp[:4]  if eu_gdp  else [],
        },
        # CPI
        "cpi": {
            "US":    us_cpi[:4]   if us_cpi  else [],
            "India": in_cpi[:4]   if in_cpi  else [],
        },
        # Unemployment
        "unemployment": {
            "US":    us_unem[:4]  if us_unem else [],
            "India": in_unem[:4]  if in_unem else [],
        },
        "last_updated": datetime.now().strftime("%H:%M UTC"),
    }
