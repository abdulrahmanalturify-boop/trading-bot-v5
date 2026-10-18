"""
tvchart.py - TradingView charts, free and without an API key.

- widget(sym): TradingView's own Advanced Chart widget in an iframe (their data, their drawing tools and indicators), for the
  stock page. Yahoo symbols are turned into TradingView's (2222.SR -> TADAWUL:2222, ^GSPC -> SP:SPX, BRK-B -> BRK.B).
- candles(df, trades): TradingView's open-source Lightweight Charts (Apache 2.0, vendored in static/vendor so it loads without
  a CDN) drawing our own yfinance candles, with the bots' buy / sell marks on them, for the bots' pages.
Both fill the page's width, so they work on a phone.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components

import lightmode as LM
from i18n import is_ar

LW_JS = Path(__file__).parent / "static" / "vendor" / "lightweight-charts.standalone.production.js"

# Yahoo -> TradingView for the symbols that are not spelled the same
TV_MAP = {
    "^GSPC": "SP:SPX", "^SPX": "SP:SPX", "^IXIC": "NASDAQ:IXIC", "^NDX": "NASDAQ:NDX", "^DJI": "DJ:DJI", "^RUT": "TVC:RUT",
    "^VIX": "TVC:VIX", "^TNX": "TVC:TNX", "^TASI.SR": "TADAWUL:TASI", "^TASI": "TADAWUL:TASI", "DX-Y.NYB": "TVC:DXY",
    "GC=F": "COMEX:GC1!", "SI=F": "COMEX:SI1!", "CL=F": "NYMEX:CL1!", "BZ=F": "NYMEX:BB1!", "NG=F": "NYMEX:NG1!",
    "ES=F": "CME_MINI:ES1!", "NQ=F": "CME_MINI:NQ1!", "YM=F": "CBOT_MINI:YM1!",
}


def tv_symbol(sym):
    """A Yahoo Finance symbol as TradingView spells it."""
    s = str(sym or "").strip().upper()
    if s in TV_MAP:
        return TV_MAP[s]
    m = re.fullmatch(r"(\d{4})(?:\.SR)?", s)
    if m:                                       # a Saudi company: 2222.SR -> TADAWUL:2222
        return f"TADAWUL:{m.group(1)}"
    m = re.fullmatch(r"([A-Z0-9]+)-USD", s)
    if m:                                       # crypto: BTC-USD -> BITSTAMP:BTCUSD
        return f"BITSTAMP:{m.group(1)}USD" if m.group(1) in ("BTC", "ETH") else f"COINBASE:{m.group(1)}USD"
    m = re.fullmatch(r"([A-Z]{6})=X", s)
    if m:                                       # currencies: EURUSD=X -> FX:EURUSD
        return f"FX:{m.group(1)}"
    return s.replace("-", ".")                  # share classes: BRK-B -> BRK.B


def _dark():
    return not LM.on()


def widget_html(sym, height=560, interval="D"):
    # a fixed pixel height, not "autosize": Streamlit's iframe opens 150px tall and iPhone Safari kept the widget at that size,
    # its header and toolbars piled on the candles. The config is finished in the page, where the screen's width is known:
    # on a phone the side drawing toolbar and the date-range bar give their room to the chart.
    cfg = {
        "width": "100%", "height": height, "symbol": tv_symbol(sym), "interval": interval,
        "timezone": "Asia/Riyadh" if str(sym).upper().endswith(".SR") else "America/New_York",
        "theme": "dark" if _dark() else "light", "style": "1", "locale": "ar_AE" if is_ar() else "en",
        "backgroundColor": "rgba(26,22,36,1)" if _dark() else "rgba(255,255,255,1)",
        "gridColor": "rgba(157,151,165,0.10)" if _dark() else "rgba(60,50,80,0.08)",
        "allow_symbol_change": False, "hide_side_toolbar": False, "withdateranges": True, "details": False,
        "calendar": False, "support_host": "https://www.tradingview.com",
    }
    return f"""<div class="tradingview-widget-container" id="tvw" style="height:{height}px;min-height:{height}px;width:100%">
<div class="tradingview-widget-container__widget" style="height:{height}px;width:100%"></div></div>
<style>html,body{{margin:0;padding:0;background:transparent;overflow:hidden;height:{height}px}}</style>
<script>
(function(){{
  var cfg = {json.dumps(cfg)};
  if ((window.innerWidth || document.documentElement.clientWidth) < 600) {{
    cfg.hide_side_toolbar = true; cfg.withdateranges = false; cfg.hide_legend = false;
  }}
  var sc = document.createElement('script');
  sc.type = 'text/javascript'; sc.async = true;
  sc.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
  sc.innerHTML = JSON.stringify(cfg);
  document.getElementById('tvw').appendChild(sc);
}})();
</script>"""


def widget(sym, height=560, interval="D"):
    """TradingView's Advanced Chart for one symbol, the page's width (phones too), in the page's look and language."""
    components.html(widget_html(sym, height, interval), height=height + 4)


@lru_cache(maxsize=1)
def _lw_js():
    return LW_JS.read_text(encoding="utf-8")


def _unix(ts):
    return int(pd.Timestamp(ts).tz_localize(None).timestamp()) if pd.Timestamp(ts).tzinfo else int(pd.Timestamp(ts).timestamp())


def candle_data(d):
    """OHLC + volume rows for Lightweight Charts (unix seconds, oldest first, one row per bar)."""
    d = d[~d.index.duplicated(keep="last")].sort_index()
    bars, vols = [], []
    for ts, r in d.iterrows():
        try:
            o, h, l, c = (float(r[k]) for k in ("Open", "High", "Low", "Close"))
        except (KeyError, TypeError, ValueError):
            continue
        if any(pd.isna(x) for x in (o, h, l, c)):
            continue
        t = _unix(ts)
        bars.append({"time": t, "open": round(o, 4), "high": round(h, 4), "low": round(l, 4), "close": round(c, 4)})
        v = r.get("Volume")
        if v is not None and not pd.isna(v):
            vols.append({"time": t, "value": float(v), "color": "rgba(52,210,122,.35)" if c >= o else "rgba(242,107,107,.35)"})
    return bars, vols


def trade_markers(d, trades, words=None):
    """The bots' trades as chart marks: a green arrow under the bar for each buy, a red one above it for each sell."""
    w = {"BUY": "BUY", "SELL": "SELL", **(words or {})}
    if trades is None or len(trades) == 0:
        return []
    idx = d.index[~d.index.duplicated(keep="last")].sort_values()
    norm = pd.DatetimeIndex(idx).normalize()

    def bar_time(x):
        try:
            day = pd.Timestamp(x)
        except (TypeError, ValueError):
            return None
        if pd.isna(day):
            return None
        day = day.tz_localize(None).normalize() if day.tzinfo else day.normalize()
        n = norm.tz_localize(None) if norm.tz is not None else norm
        hit = n.get_indexer([day])
        return _unix(idx[hit[0]]) if hit[0] >= 0 else None

    out = {}
    for _, r in trades.iterrows():
        t = bar_time(r.get("Entry Date"))
        if t is not None:
            out.setdefault((t, "b"), {"time": t, "position": "belowBar", "color": "#34D27A", "shape": "arrowUp", "text": w["BUY"]})
        if str(r.get("Exit Reason", "")) != "Open":
            t = bar_time(r.get("Exit Date"))
            if t is not None:
                pnl = r.get("P&L %")
                # the result in a left-to-right isolate, so "+4.2%" keeps its order next to an Arabic word
                txt = w["SELL"] + (f" \u2066{float(pnl):+.1f}%\u2069" if pnl is not None and not pd.isna(pnl) else "")
                out.setdefault((t, "s"), {"time": t, "position": "aboveBar", "color": "#F26B6B", "shape": "arrowDown", "text": txt})
    return sorted(out.values(), key=lambda m: m["time"])


def candles_html(d, trades=None, height=460, words=None, intraday=False):
    bars, vols = candle_data(d)
    marks = trade_markers(d, trades, words)
    dark = _dark()
    opts = {
        "autoSize": True,
        "layout": {"background": {"type": "solid", "color": "rgba(0,0,0,0)"}, "textColor": "#CFC9D9" if dark else "#3A3150",
                   "fontFamily": "DM Sans, Almarai, system-ui, sans-serif"},
        "grid": {"vertLines": {"color": "rgba(157,151,165,0.10)" if dark else "rgba(60,50,80,0.07)"},
                 "horzLines": {"color": "rgba(157,151,165,0.10)" if dark else "rgba(60,50,80,0.07)"}},
        "rightPriceScale": {"borderVisible": False, "scaleMargins": {"top": 0.08, "bottom": 0.22}},
        "timeScale": {"borderVisible": False, "timeVisible": bool(intraday), "secondsVisible": False},
        "crosshair": {"mode": 0},
        "localization": {"locale": "ar-SA-u-nu-latn" if is_ar() else "en-US"},
    }
    payload = json.dumps({"bars": bars, "vols": vols, "marks": marks, "opts": opts}).replace("</", "<\\/")
    js = _lw_js().replace("</script", "<\\/script")
    return f"""<div id="lw" style="width:100%;height:{height}px;direction:ltr"></div>
<style>html,body{{margin:0;padding:0;background:transparent;overflow:hidden}}</style>
<script>{js}</script>
<script>
(function(){{
  var P = {payload};
  var el = document.getElementById('lw');
  var chart = LightweightCharts.createChart(el, P.opts);
  var s = chart.addCandlestickSeries({{upColor:'#34D27A', downColor:'#F26B6B', borderVisible:false,
                                       wickUpColor:'#34D27A', wickDownColor:'#F26B6B'}});
  s.setData(P.bars);
  if (P.marks.length) s.setMarkers(P.marks);
  if (P.vols.length) {{
    var v = chart.addHistogramSeries({{priceFormat:{{type:'volume'}}, priceScaleId:'vol', lastValueVisible:false, priceLineVisible:false}});
    chart.priceScale('vol').applyOptions({{scaleMargins:{{top:0.82, bottom:0}}}});
    v.setData(P.vols);
  }}
  chart.timeScale().fitContent();
}})();
</script>"""


def candles(d, trades=None, height=460, words=None, intraday=False):
    """Our own candles (with the bots' trades marked) drawn by TradingView's Lightweight Charts, the page's width."""
    components.html(candles_html(d, trades, height, words, intraday), height=height + 4)
