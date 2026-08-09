#!/usr/bin/env python3
"""asicminerprices.com — static site generator.
Generates the full multi-page site into dist/. No dependencies.
Data = plausible snapshot constants; swap HASHPRICE/prices with live API data later.
"""
import json, os, re, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "dist")
SITE = "https://asicminerprices.com"
DEFAULT_RATE = 0.072
UPDATED = datetime.date.today().strftime("%B %d, %Y")

# $ revenue per hashrate unit per day (snapshot fallback if data.json missing)
HASHPRICE = {"SHA-256": 0.045, "kHeavyHash": 1.15, "Scrypt": 3.10, "Equihash": 0.036,
             "EtHash": 0.0013, "X11": 0.0097, "Eaglesong": 0.00026, "RandomX": 0.0266, "Blake3": 0.5}
COIN = {"SHA-256": "BTC", "kHeavyHash": "KAS", "Scrypt": "LTC+DOGE", "Equihash": "ZEC",
        "EtHash": "ETC", "X11": "DASH", "Eaglesong": "CKB", "RandomX": "XMR", "Blake3": "ALPH"}
ALGO_SLUG = {"SHA-256": "sha-256", "kHeavyHash": "kheavyhash", "Scrypt": "scrypt", "Equihash": "equihash",
             "EtHash": "ethash", "X11": "x11", "Eaglesong": "eaglesong", "RandomX": "randomx"}
EFF_UNIT = {"TH/s": "J/TH", "GH/s": "J/GH", "kSol/s": "J/kSOL", "MH/s": "J/MH", "kH/s": "J/kH"}
HP_UNIT = {"SHA-256": "TH", "kHeavyHash": "TH", "Scrypt": "GH", "Equihash": "kSol",
           "EtHash": "MH", "X11": "GH", "Eaglesong": "TH", "RandomX": "kH", "Blake3": "TH"}

# ---- live data layer: fetch_data.py writes data.json; override snapshot constants ----
DATA_SOURCE = "snapshot constants (run fetch_data.py for live data)"
LIVE = {}
_data_path = os.path.join(ROOT, "data.json")
if os.path.exists(_data_path):
    try:
        with open(_data_path) as _f:
            LIVE = json.load(_f)
        for _k, _v in LIVE.get("hashprice", {}).items():
            if _v:
                HASHPRICE[_k] = _v
        UPDATED = LIVE.get("updated_human", UPDATED)
        DATA_SOURCE = LIVE.get("source", "live")
    except Exception as _e:
        print(f"warning: data.json ignored ({_e})")
ALGO_BLURB = {
    "SHA-256": "SHA-256 is the algorithm behind Bitcoin. SHA-256 ASICs are the oldest and most competitive category — efficiency (J/TH) matters more than raw hashrate because margins are thin and difficulty adjusts every 2 weeks.",
    "kHeavyHash": "kHeavyHash is the proof-of-work algorithm of Kaspa (KAS), a blockDAG chain with 1-second blocks. Kaspa ASICs are newer, power-hungry, and currently offer some of the highest revenue per day — with higher coin-price risk.",
    "Scrypt": "Scrypt miners mine Litecoin and Dogecoin simultaneously through merged mining (AuxPoW) — one machine, two revenue streams. That dual income is why Scrypt rigs like the Antminer L9 dominate their category.",
    "Equihash": "Equihash is the proof-of-work algorithm of Zcash (ZEC), the leading privacy coin. The Antminer Z15 family owns this category — with ZEC's rally these machines currently post the best profit-per-watt of any ASIC on the market.",
    "EtHash": "EtHash (formerly Ethash) is the algorithm of Ethereum Classic (ETC). After Ethereum moved to proof-of-stake, its ASICs moved to ETC. EtHash machines are measured in MH/s and tend to be quiet and home-friendly.",
    "X11": "X11 is the algorithm behind Dash (DASH), chained from 11 hash functions. A small, stable ASIC category dominated by Bitmain's Antminer D-series.",
    "Eaglesong": "Eaglesong is the proof-of-work algorithm of Nervos Network (CKB). Bitmain's Antminer K7 and Goldshell's CK series compete in this mid-size category.",
    "RandomX": "RandomX is the CPU-friendly algorithm of Monero (XMR), designed to resist ASICs — yet Bitmain's Antminer X-series finally cracked it. RandomX rigs are measured in kH/s and sip power compared to Bitcoin miners.",
    "Blake3": "Blake3 is the ultra-fast hash at the core of Alephium (ALPH), a sharded proof-of-work chain. ALPH ASICs are a young, fast-moving category where IceRiver, Goldshell and Bitmain all compete.",
}

MINERS = [
    # name, brand, algo, hashrate, unit, power W, price USD (street-price estimates)
    # ---------------- SHA-256 (BTC) ----------------
    dict(slug="antminer-s23-hyd-3u", name="Antminer S23 Hyd 3U", brand="Bitmain", algo="SHA-256", hr=1160, unit="TH/s", power=11020, price=19500),
    dict(slug="bitdeer-sealminer-a4-ultra-hydro", name="Bitdeer SealMiner A4 Ultra Hydro", brand="Bitdeer", algo="SHA-256", hr=886, unit="TH/s", power=8372, price=9741),
    dict(slug="antminer-s23e-hyd-2u", name="Antminer S23e Hyd 2U", brand="Bitmain", algo="SHA-256", hr=865, unit="TH/s", power=8650, price=11699),
    dict(slug="bitdeer-sealminer-a4-pro-hydro", name="Bitdeer SealMiner A4 Pro Hydro", brand="Bitdeer", algo="SHA-256", hr=680, unit="TH/s", power=7412, price=8449),
    dict(slug="antminer-s21-xp-plus-hyd", name="Antminer S21 XP+ Hyd", brand="Bitmain", algo="SHA-256", hr=500, unit="TH/s", power=5500, price=8690),
    dict(slug="antminer-s23-hyd", name="Antminer S23 Hyd", brand="Bitmain", algo="SHA-256", hr=580, unit="TH/s", power=5510, price=9800),
    dict(slug="antminer-s23", name="Antminer S23", brand="Bitmain", algo="SHA-256", hr=318, unit="TH/s", power=3498, price=5400),
    dict(slug="antminer-s21-xp-hyd", name="Antminer S21 XP Hyd", brand="Bitmain", algo="SHA-256", hr=473, unit="TH/s", power=5676, price=9800),
    dict(slug="antminer-s21-xp", name="Antminer S21 XP", brand="Bitmain", algo="SHA-256", hr=270, unit="TH/s", power=3645, price=5999),
    dict(slug="antminer-s21-pro", name="Antminer S21 Pro", brand="Bitmain", algo="SHA-256", hr=234, unit="TH/s", power=3510, price=4200),
    dict(slug="antminer-s21-plus", name="Antminer S21+", brand="Bitmain", algo="SHA-256", hr=216, unit="TH/s", power=3564, price=3600),
    dict(slug="antminer-s21-hyd", name="Antminer S21 Hyd", brand="Bitmain", algo="SHA-256", hr=335, unit="TH/s", power=5360, price=5400),
    dict(slug="antminer-s21", name="Antminer S21", brand="Bitmain", algo="SHA-256", hr=200, unit="TH/s", power=3500, price=2900),
    dict(slug="bitdeer-sealminer-a2", name="Bitdeer SealMiner A2", brand="Bitdeer", algo="SHA-256", hr=226, unit="TH/s", power=3729, price=3900),
    dict(slug="whatsminer-m60s", name="Whatsminer M60S", brand="MicroBT", algo="SHA-256", hr=186, unit="TH/s", power=3441, price=2400),
    dict(slug="avalon-a1566", name="Avalon A1566", brand="Canaan", algo="SHA-256", hr=185, unit="TH/s", power=3420, price=2300),
    dict(slug="whatsminer-m60", name="Whatsminer M60", brand="MicroBT", algo="SHA-256", hr=172, unit="TH/s", power=3422, price=2050),
    dict(slug="antminer-s19-xp-hyd", name="Antminer S19 XP Hyd", brand="Bitmain", algo="SHA-256", hr=255, unit="TH/s", power=5304, price=2900),
    dict(slug="antminer-s19-xp", name="Antminer S19 XP", brand="Bitmain", algo="SHA-256", hr=140, unit="TH/s", power=3010, price=1650),
    dict(slug="avalon-a1466", name="Avalon A1466", brand="Canaan", algo="SHA-256", hr=150, unit="TH/s", power=3230, price=1700),
    dict(slug="avalon-a1366", name="Avalon A1366", brand="Canaan", algo="SHA-256", hr=130, unit="TH/s", power=3250, price=1150),
    dict(slug="antminer-s19k-pro", name="Antminer S19k Pro", brand="Bitmain", algo="SHA-256", hr=120, unit="TH/s", power=2760, price=1050),
    dict(slug="antminer-s19j-pro-plus", name="Antminer S19j Pro+", brand="Bitmain", algo="SHA-256", hr=122, unit="TH/s", power=3355, price=900),
    dict(slug="antminer-s19-pro", name="Antminer S19 Pro", brand="Bitmain", algo="SHA-256", hr=110, unit="TH/s", power=3250, price=780),
    dict(slug="antminer-s19j-pro", name="Antminer S19j Pro", brand="Bitmain", algo="SHA-256", hr=104, unit="TH/s", power=3068, price=700),
    dict(slug="antminer-s19", name="Antminer S19", brand="Bitmain", algo="SHA-256", hr=95, unit="TH/s", power=3250, price=600),
    dict(slug="whatsminer-m30s-plus-plus", name="Whatsminer M30S++", brand="MicroBT", algo="SHA-256", hr=112, unit="TH/s", power=3472, price=950),
    dict(slug="whatsminer-m30s-plus", name="Whatsminer M30S+", brand="MicroBT", algo="SHA-256", hr=100, unit="TH/s", power=3400, price=780),
    dict(slug="whatsminer-m30s", name="Whatsminer M30S", brand="MicroBT", algo="SHA-256", hr=88, unit="TH/s", power=3344, price=600),
    dict(slug="avalon-a1346", name="Avalon A1346", brand="Canaan", algo="SHA-256", hr=110, unit="TH/s", power=3300, price=820),
    # ---------------- kHeavyHash (KAS) ----------------
    dict(slug="iceriver-ks7", name="IceRiver KS7", brand="IceRiver", algo="kHeavyHash", hr=30, unit="TH/s", power=3500, price=5600),
    dict(slug="antminer-ks5-pro", name="Antminer KS5 Pro", brand="Bitmain", algo="kHeavyHash", hr=21, unit="TH/s", power=3150, price=3200),
    dict(slug="antminer-ks5", name="Antminer KS5", brand="Bitmain", algo="kHeavyHash", hr=20, unit="TH/s", power=3000, price=2900),
    dict(slug="iceriver-ks5m", name="IceRiver KS5M", brand="IceRiver", algo="kHeavyHash", hr=15, unit="TH/s", power=3400, price=2400),
    dict(slug="antminer-ks5l", name="Antminer KS5L", brand="Bitmain", algo="kHeavyHash", hr=12, unit="TH/s", power=1850, price=1700),
    dict(slug="antminer-ks3", name="Antminer KS3", brand="Bitmain", algo="kHeavyHash", hr=8.3, unit="TH/s", power=3188, price=1100),
    dict(slug="iceriver-ks3", name="IceRiver KS3", brand="IceRiver", algo="kHeavyHash", hr=8, unit="TH/s", power=3200, price=1050),
    dict(slug="iceriver-ks3m", name="IceRiver KS3M", brand="IceRiver", algo="kHeavyHash", hr=6, unit="TH/s", power=3400, price=800),
    dict(slug="goldshell-e-ka1m", name="Goldshell E-KA1M", brand="Goldshell", algo="kHeavyHash", hr=5.5, unit="TH/s", power=1500, price=900),
    dict(slug="iceriver-ks2", name="IceRiver KS2", brand="IceRiver", algo="kHeavyHash", hr=2, unit="TH/s", power=1200, price=450),
    dict(slug="goldshell-ka-box", name="Goldshell KA-BOX", brand="Goldshell", algo="kHeavyHash", hr=1.18, unit="TH/s", power=400, price=300),
    dict(slug="iceriver-ks1", name="IceRiver KS1", brand="IceRiver", algo="kHeavyHash", hr=1, unit="TH/s", power=600, price=280),
    dict(slug="iceriver-ks0-ultra", name="IceRiver KS0 Ultra", brand="IceRiver", algo="kHeavyHash", hr=0.4, unit="TH/s", power=100, price=150),
    # ---------------- Scrypt (LTC+DOGE) ----------------
    dict(slug="bitdeer-sealminer-dl1-hydro", name="Bitdeer SealMiner DL1 Hydro", brand="Bitdeer", algo="Scrypt", hr=52.5, unit="GH/s", power=7823, price=8999),
    dict(slug="antminer-l9", name="Antminer L9", brand="Bitmain", algo="Scrypt", hr=16, unit="GH/s", power=3360, price=7500),
    dict(slug="volcminer-d1", name="VolcMiner D1", brand="VolcMiner", algo="Scrypt", hr=15, unit="GH/s", power=3450, price=4300),
    dict(slug="elphapex-dg1-plus", name="Elphapex DG1+", brand="Elphapex", algo="Scrypt", hr=14, unit="GH/s", power=3950, price=4600),
    dict(slug="elphapex-dg1", name="Elphapex DG1", brand="Elphapex", algo="Scrypt", hr=11, unit="GH/s", power=3420, price=3600),
    dict(slug="antminer-l7", name="Antminer L7", brand="Bitmain", algo="Scrypt", hr=9.05, unit="GH/s", power=3425, price=4200),
    dict(slug="goldshell-lt6", name="Goldshell LT6", brand="Goldshell", algo="Scrypt", hr=3.35, unit="GH/s", power=3200, price=1400),
    dict(slug="goldshell-lt5-pro", name="Goldshell LT5 Pro", brand="Goldshell", algo="Scrypt", hr=2.45, unit="GH/s", power=3100, price=1000),
    dict(slug="innosilicon-a6-plus", name="Innosilicon A6+", brand="Innosilicon", algo="Scrypt", hr=2.2, unit="GH/s", power=2100, price=850),
    dict(slug="goldshell-mini-doge-iii", name="Goldshell Mini-DOGE III", brand="Goldshell", algo="Scrypt", hr=0.7, unit="GH/s", power=400, price=350),
    # ---------------- Equihash (ZEC) ----------------
    dict(slug="antminer-z15-pro", name="Antminer Z15 Pro", brand="Bitmain", algo="Equihash", hr=840, unit="kSol/s", power=2780, price=3317),
    dict(slug="antminer-z15", name="Antminer Z15", brand="Bitmain", algo="Equihash", hr=420, unit="kSol/s", power=1510, price=749),
    dict(slug="antminer-z9-mini", name="Antminer Z9 Mini", brand="Bitmain", algo="Equihash", hr=10, unit="kSol/s", power=300, price=120),
]

# ---- extended catalog imported from asicminervalue.com benchmark (benchmark/amv_import.py) ----
_extra_path = os.path.join(ROOT, "miners_extra.json")
if os.path.exists(_extra_path):
    with open(_extra_path) as _f:
        for _m in json.load(_f):
            MINERS.append(dict(slug=_m["slug"], name=_m["name"], brand=_m["brand"], algo=_m["algo"],
                               hr=_m["hr"], unit=_m["unit"], power=_m["power"], price=int(_m["price"] or 0),
                               release=_m.get("release")))
# ---- AMV price/release overrides for base miners (benchmark/sync_prices.py) ----
_ovr_path = os.path.join(ROOT, "prices_amv.json")
if os.path.exists(_ovr_path):
    _ovr = json.load(open(_ovr_path))
    for _m in MINERS:
        if _m["slug"] in _ovr:
            _m.update(_ovr[_m["slug"]])

COMPARE_PAIRS = [
    ("antminer-s21-xp", "antminer-s21-pro"),
    ("antminer-s21", "whatsminer-m60s"),
    ("antminer-ks5-pro", "antminer-ks5l"),
    ("iceriver-ks7", "antminer-ks5-pro"),
    ("antminer-l9", "antminer-l7"),
    ("antminer-l9", "elphapex-dg1"),
]
# auto-expand: all pairs among the 12 most profitable miners (deduped, ordered)
_by_profit = sorted(MINERS, key=lambda m: -(m["hr"] * HASHPRICE[m["algo"]] - m["power"] / 1000 * 24 * DEFAULT_RATE))[:12]
_seen = {tuple(sorted(p)) for p in COMPARE_PAIRS}
for _i in range(len(_by_profit)):
    for _j in range(_i + 1, len(_by_profit)):
        _a, _b = _by_profit[_i]["slug"], _by_profit[_j]["slug"]
        if tuple(sorted((_a, _b))) not in _seen:
            _seen.add(tuple(sorted((_a, _b))))
            COMPARE_PAIRS.append((_a, _b))

# ---------------- helpers ----------------
def rev(m): return m["hr"] * HASHPRICE[m["algo"]]
def cost(m, rate): return m["power"] / 1000 * 24 * rate
def profit(m, rate=DEFAULT_RATE): return rev(m) - cost(m, rate)
def eff(m): return m["power"] / m["hr"]
def breakeven(m): return rev(m) / (m["power"] / 1000 * 24)
def money(x, dec=2): return ("-$" if x < 0 else "$") + f"{abs(x):,.{dec}f}"
def pill(x): return f'<span class="{"pill-profit" if x>=0 else "pill-loss"}">{"+" if x>=0 else ""}{money(x)}</span>'
def by_slug(s): return next(m for m in MINERS if m["slug"] == s)

def write(path, html):
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)

NAV = [
    ("/", "Overview", "overview"),
    ("/sha-256/", "SHA-256 (BTC)", "sha-256"),
    ("/kheavyhash/", "kHeavyHash (KAS)", "kheavyhash"),
    ("/scrypt/", "Scrypt (LTC+DOGE)", "scrypt"),
    ("/equihash/", "Equihash (ZEC)", "equihash"),
    ("/ethash/", "EtHash (ETC)", "ethash"),
    ("/eaglesong/", "Eaglesong (CKB)", "eaglesong"),
    ("/x11/", "X11 (DASH)", "x11"),
    ("/randomx/", "RandomX (XMR)", "randomx"),
    ("/calculator/", "Calculator", "calculator"),
    ("/compare/", "Compare", "compare"),
    ("/guides/", "Guides", "guides"),
    ("/blog/", "Blog", "blog"),
    ("/contact/", "Contact", "contact"),
]

# ---------------- inline CSS + self-hosted fonts (Core Web Vitals) ----------------
# Fonts are self-hosted in assets/fonts/ (latin subsets, woff2) and the whole
# stylesheet is inlined into <head> so there is NO render-blocking request.
_FONT_SPECS = (("Inter", "inter", (400, 600, 700, 800)),
               ("JetBrains Mono", "jetbrainsmono", (400, 600)))
_INLINE_CSS_CACHE = None

def inline_css(r):
    global _INLINE_CSS_CACHE
    if _INLINE_CSS_CACHE is None:
        faces = []
        for fam, fname, weights in _FONT_SPECS:
            for w in weights:
                faces.append(
                    "@font-face{font-family:'%s';font-style:normal;font-weight:%d;"
                    "font-display:swap;src:url('__R__assets/fonts/%s-%d.woff2') format('woff2')}"
                    % (fam, w, fname, w))
        with open(os.path.join(ROOT, "assets", "style.css"), encoding="utf-8") as f:
            _INLINE_CSS_CACHE = "".join(faces) + f.read()
    return _INLINE_CSS_CACHE.replace("__R__", r)

def layout(title, desc, active, body, path, depth=0, extra_head=""):
    r = "../" * depth
    nav = "".join(
        f'<a href="{r if href=="/" else r+href.strip("/")+"/"}" class="{"active" if key==active else ""}">{label}</a>'
        for href, label, key in NAV)
    canonical = SITE + (path if path.startswith("/") else "/" + path)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="ASIC Miner Prices">
<link rel="preload" href="{r}assets/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/jetbrainsmono-400.woff2" as="font" type="font/woff2" crossorigin>
<style>{inline_css(r)}</style>
{extra_head}
</head>
<body>
<aside class="sidebar">
  <div class="logo"><b>ASIC Miner Prices</b><span>Live profitability tracker</span></div>
  <nav>{nav}</nav>
  <div class="foot">Data snapshot: {UPDATED}<br>&copy; 2026 asicminerprices.com</div>
</aside>
<div class="main">
{body}
<footer class="site">
  <div class="links">
    <a href="{r}sha-256/">SHA-256 miners</a><a href="{r}kheavyhash/">Kaspa miners</a>
    <a href="{r}scrypt/">Scrypt miners</a><a href="{r}calculator/">Profitability calculator</a>
    <a href="{r}compare/">Compare miners</a><a href="{r}guides/">Mining guides</a>
  </div>
  <p>Profitability estimates from {DATA_SOURCE} ({UPDATED}) and your electricity cost. Not financial advice. Prices may contain affiliate links.</p>
</footer>
</div>
<script src="{r}assets/app.js?v=""" + datetime.datetime.now().strftime("%Y%m%d%H%M") + """\"></script>
</body>
</html>"""

def rate_bar():
    return """<div class="panel rate-bar">
  <label for="elec-rate"><b>Electricity cost</b></label>
  <input type="range" id="elec-rate" min="20" max="200" step="1" value="72">
  <span class="rate-val" id="rate-val">$0.072/kWh</span>
</div>"""

def miner_row(m):
    p = profit(m)
    e = eff(m)
    be = breakeven(m)
    return f"""<tr data-hr="{m['hr']}" data-hp="{HASHPRICE[m['algo']]}" data-power="{m['power']}" data-price="{m['price']}" data-algo="{m['algo']}">
<td><a class="miner-name" href="{{{{R}}}}miners/{m['slug']}/">{m['name']}</a> <span class="algo-pill">{m['algo']}</span></td>
<td class="num" data-col-val="hr" data-sort="{m['hr']}">{m['hr']:g} {m['unit']}</td>
<td class="num" data-col-val="power" data-sort="{m['power']}">{m['power']:,} W</td>
<td class="num" data-col-val="eff" data-sort="{e}">{e:.1f} {EFF_UNIT[m['unit']]}<span class="effbar"><i style="width:{max(4,min(100,100-(e-12)*3)):.0f}%"></i></span></td>
<td class="num profit-cell" data-col-val="profit" data-sort="{p}">{pill(p)}</td>
<td class="num" data-col-val="price" data-sort="{m['price']}">${m['price']:,}</td>
<td class="num" data-col-val="be" data-sort="{be}">${be:.3f}</td>
</tr>"""

TABLE_HEAD = """<thead><tr>
<th data-col="miner">Miner</th><th class="num" data-col="hr">Hashrate</th><th class="num" data-col="power">Power</th>
<th class="num" data-col="eff">Efficiency</th><th class="num" data-col="profit">Profit/day</th>
<th class="num" data-col="price">Price</th><th class="num" data-col="be">Break-even</th></tr></thead>"""

def miners_table(miners, depth=0, autosort=True):
    rows = "\n".join(miner_row(m) for m in sorted(miners, key=lambda m: -profit(m)))
    r = "../" * depth
    t = f'<table class="ranking-table {"autosort" if autosort else ""}">{TABLE_HEAD}<tbody>{rows}</tbody></table>'
    return t.replace("{{R}}", r)

# ---------------- pages ----------------
def page_index():
    ms = sorted(MINERS, key=lambda m: -profit(m))
    top = ms[0]
    best_eff = min([m for m in MINERS if m["algo"] == "SHA-256"], key=eff)
    budget = max([m for m in MINERS if m["price"] <= 2000], key=lambda m: profit(m))
    maxp = max(profit(m) for m in MINERS)
    bars = "".join(
        f'<div class="b"><em>{money(profit(m),0)}</em><i data-hr="{m["hr"]}" data-hp="{HASHPRICE[m["algo"]]}" data-power="{m["power"]}" style="height:{max(2,profit(m)/maxp*100):.0f}%"></i><span>{m["name"].replace("Antminer ","").replace("Whatsminer ","M").replace("IceRiver ","IR ").replace("Elphapex ","")}</span></div>'
        for m in ms[:8])
    body = f"""
<div class="crumbs">Home</div>
<h1>Most profitable ASIC miners <span class="badge-live"><i></i>LIVE</span></h1>
<p class="lede">Real-time profitability ranking of {len(MINERS)} ASIC miners across Bitcoin (SHA-256), Kaspa (kHeavyHash) and Litecoin+Dogecoin (Scrypt). Set your electricity rate — every number on this page updates instantly.</p>

<div class="cards">
  <div class="card"><div class="k">Top miner profit</div><div class="v" style="color:var(--green)"><span data-dyn-profit data-hr="{top['hr']}" data-hp="{HASHPRICE[top['algo']]}" data-power="{top['power']}">{money(profit(top))}</span><span style="font-size:13px;color:var(--ink3)">/day</span></div><div class="s">{top['name']} @ <span class="dyn-rate">${DEFAULT_RATE}/kWh</span></div></div>
  <div class="card"><div class="k">Miners tracked</div><div class="v">{len(MINERS)}</div><div class="s">{len(ALGO_SLUG)} algorithms · {len({m['brand'] for m in MINERS})} brands</div></div>
  <div class="card"><div class="k">Best efficiency</div><div class="v">{eff(best_eff):.1f}<span style="font-size:13px;color:var(--ink3)"> J/TH</span></div><div class="s">{best_eff['name']}</div></div>
  <div class="card"><div class="k">{f"BTC ${LIVE.get('btc_usd', 0):,} · " if LIVE.get('btc_usd') else ""}Snapshot</div><div class="v" style="font-size:16px;padding-top:4px">{UPDATED}</div><div class="s">Hashprice: {" · ".join(f"{COIN[a]} ${HASHPRICE[a]}/{HP_UNIT[a]}" for a in ("SHA-256", "kHeavyHash", "Scrypt", "Equihash"))}</div></div>
</div>

{rate_bar()}

<div class="cards">
  <div class="card gold"><span class="tag gold">Best profitability</span><div class="v" style="font-size:18px"><a class="miner-name" href="miners/{top['slug']}/">{top['name']}</a></div><div class="s"><span data-dyn-profit data-hr="{top['hr']}" data-hp="{HASHPRICE[top['algo']]}" data-power="{top['power']}">{money(profit(top))}</span>/day · break-even ${breakeven(top):.3f}/kWh</div></div>
  <div class="card blue"><span class="tag blue">Best efficiency</span><div class="v" style="font-size:18px"><a class="miner-name" href="miners/{best_eff['slug']}/">{best_eff['name']}</a></div><div class="s">{eff(best_eff):.1f} J/TH · <span data-dyn-profit data-hr="{best_eff['hr']}" data-hp="{HASHPRICE[best_eff['algo']]}" data-power="{best_eff['power']}">{money(profit(best_eff))}</span>/day</div></div>
  <div class="card violet"><span class="tag violet">Best budget</span><div class="v" style="font-size:18px"><a class="miner-name" href="miners/{budget['slug']}/">{budget['name']}</a></div><div class="s">${budget['price']:,} · <span data-dyn-profit data-hr="{budget['hr']}" data-hp="{HASHPRICE[budget['algo']]}" data-power="{budget['power']}">{money(profit(budget))}</span>/day</div></div>
</div>

<div class="ad-slot">Advertisement — AdSense leaderboard 728×90</div>

<h2>Top 8 miners by daily profit</h2>
<div class="panel"><div class="bars" data-max="{maxp:.2f}">{bars}</div></div>

<h2>Full profitability ranking</h2>
<div class="tabs">
  <button data-algo="all" class="active">All</button>
  <button data-algo="SHA-256">SHA-256 (BTC)</button>
  <button data-algo="kHeavyHash">kHeavyHash (KAS)</button>
  <button data-algo="Scrypt">Scrypt (LTC+DOGE)</button>
</div>
<div class="panel" style="overflow-x:auto">{miners_table(MINERS)}</div>

<h2>Buy through our vendor &amp; hosting network</h2>
<p class="lede">We're plugged into the supply side of mining: <b>50+ verified machine vendors</b> — manufacturers, authorized distributors and vetted resellers — plus <b>30+ partner hosting facilities</b> across North America and beyond. One inquiry reaches the whole network.</p>
<div class="cards">
  <div class="card"><div class="k">Machine sourcing</div><div class="v">50+<span style="font-size:13px;color:var(--ink3)"> vendors</span></div><div class="s">Bitmain, MicroBT, IceRiver, Canaan &amp; verified resellers — live stock, real delivered pricing, no bait listings</div></div>
  <div class="card"><div class="k">Hosting partners</div><div class="v">30+<span style="font-size:13px;color:var(--ink3)"> facilities</span></div><div class="s">$0.04–0.07/kWh all-in — US, Canada, Paraguay, Ethiopia &amp; more, with dashboards and insurance options</div></div>
  <div class="card"><div class="k">One inquiry, full market</div><div class="v">24h<span style="font-size:13px;color:var(--ink3)"> response</span></div><div class="s">Tell us the model + quantity — we query the network and come back with the best available price &amp; hosting match</div></div>
</div>
<div class="panel" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <a class="cta" href="contact/">Request a quote — it's free →</a>
  <a class="cta secondary" href="contact/?topic=hosting">Find hosting for your machines</a>
</div>

<div class="ad-slot">Advertisement — AdSense responsive</div>

<div class="prose">
<h2>How ASIC miner profitability works</h2>
<p>An ASIC miner's daily profit is its mining revenue minus electricity cost. Revenue depends on the coin's price, network difficulty and block reward — captured in the <b>hashprice</b> (dollars earned per unit of hashrate per day). Electricity cost is simply power draw × 24h × your kWh rate, which is why the rate slider above is the single most important input: a miner profitable at $0.05/kWh can lose money at $0.15/kWh.</p>
<p>Before buying, check the <b>break-even electricity price</b> on each miner's page — the maximum rate at which the machine still makes money. Use our <a href="calculator/">profitability calculator</a> for pool fees and custom scenarios, or <a href="compare/">compare two miners head-to-head</a>.</p>
</div>"""
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "What is the most profitable ASIC miner right now?",
             "acceptedAnswer": {"@type": "Answer", "text": f"At a ${DEFAULT_RATE}/kWh electricity rate (the typical industrial average), the {top['name']} currently leads at about {money(profit(top))} per day before pool fees."}},
            {"@type": "Question", "name": "How is ASIC miner profitability calculated?",
             "acceptedAnswer": {"@type": "Answer", "text": "Daily profit = (hashrate × hashprice) − (power in kW × 24 × electricity rate). Hashprice bundles coin price, network difficulty and block reward into one number."}},
            {"@type": "Question", "name": "What electricity rate do I need for mining to be profitable?",
             "acceptedAnswer": {"@type": "Answer", "text": "Each miner has a break-even electricity price listed on its page. Most profitable operations pay $0.02–$0.06/kWh; above $0.12/kWh only the newest generation stays profitable."}},
        ]}
    html = layout("Most Profitable ASIC Miners — Live Profitability & Prices | ASIC Miner Prices",
                  f"Live ranking of {len(MINERS)} ASIC miners by daily profit. Compare Bitcoin, Kaspa and Scrypt miners, set your electricity rate and find your break-even point before you buy.",
                  "overview", body, "/", 0,
                  f'<script type="application/ld+json">{json.dumps(faq)}</script>')
    write("index.html", html)

def miner_description(m, coin, e, p, be):
    """Unique 2-3 sentence description per miner from its own data."""
    rel = f" Released in {m['release']}, it" if m.get("release") else " It"
    tier = "industrial-grade" if m["power"] >= 3000 else ("mid-power" if m["power"] >= 800 else "quiet home-class")
    scrypt_note = " Because Scrypt merged-mines Litecoin and Dogecoin, every hash earns two coins at once." if m["algo"] == "Scrypt" else ""
    return (f"<p>The <b>{m['name']}</b> is a {tier} {m['algo']} ASIC miner from {m['brand']}, "
            f"delivering <b>{m['hr']:g} {m['unit']}</b> for <b>{m['power']:,} W</b> of power draw — "
            f"an efficiency of <b>{e:.1f} {EFF_UNIT[m['unit']]}</b>.{scrypt_note}</p>"
            f"<p>{rel.strip()} targets the {coin} market: at today's network conditions ({UPDATED}) it produces about "
            f"<b>{money(rev(m))}/day</b> in {coin} revenue, or <b>{money(p)}/day</b> net of electricity at ${DEFAULT_RATE}/kWh, "
            f"and stays in the green down to a break-even rate of <b>${be:.3f}/kWh</b>. "
            f"Street price is around <b>${m['price']:,}</b> — request a quote below for live stock and delivery times.</p>")

def page_miner(m):
    p = profit(m)
    e = eff(m)
    be = breakeven(m)
    roi = round(m["price"] / p) if p > 0 else None
    coin = COIN[m["algo"]]
    rates = [round(0.02 + 0.02 * i, 2) for i in range(10)]
    maxp = max(abs(profit(m, r)) for r in rates)
    rows = "".join(
        f'<tr><td class="num">${r:.2f}</td><td class="num">{money(cost(m,r))}</td><td class="num">{money(rev(m))}</td><td class="num">{pill(profit(m,r))}</td>'
        f'<td><span class="effbar" style="width:140px"><i style="width:{abs(profit(m,r))/maxp*100:.0f}%;background:{"var(--green)" if profit(m,r)>=0 else "var(--red)"}"></i></span></td></tr>'
        for r in rates)
    related = [x for x in MINERS if x["algo"] == m["algo"] and x["slug"] != m["slug"]][:3]
    rel = "".join(f'<div class="card"><div class="k">{x["algo"]}</div><div class="v" style="font-size:16px"><a class="miner-name" href="../{x["slug"]}/">{x["name"]}</a></div><div class="s">{money(profit(x))}/day · ${x["price"]:,}</div></div>' for x in related)
    faqs = [
        (f"Is the {m['name']} profitable?", f"At ${DEFAULT_RATE}/kWh the {m['name']} earns about {money(rev(m))}/day in revenue and {money(p)}/day in net profit. Its break-even electricity price is ${be:.3f}/kWh — above that rate it mines at a loss."),
        (f"What electricity rate does the {m['name']} need?", f"The {m['name']} breaks even at ${be:.3f}/kWh at current network conditions — below that rate it earns {money(p)}/day net at ${DEFAULT_RATE}/kWh. Miners with access to industrial power ($0.04–0.07/kWh) have the healthiest margins."),
        (f"What does the {m['name']} mine?", f"The {m['name']} is a {m['algo']} miner. It mines {coin}." + (" Scrypt miners mine Litecoin and Dogecoin simultaneously via merged mining." if m["algo"] == "Scrypt" else "")),
    ]
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    ld_product = {"@context": "https://schema.org", "@type": "Product", "name": m["name"],
                  "brand": {"@type": "Brand", "name": m["brand"]},
                  "description": f"{m['name']} {m['algo']} ASIC miner: {m['hr']:g} {m['unit']}, {m['power']}W, {e:.1f} {EFF_UNIT[m['unit']]}.",
                  "offers": {"@type": "Offer", "price": m["price"], "priceCurrency": "USD", "availability": "https://schema.org/InStock"}}
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    ld_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": m["algo"] + " miners", "item": SITE + "/" + ALGO_SLUG[m["algo"]] + "/"},
        {"@type": "ListItem", "position": 3, "name": m["name"]}]}
    rel_year = ""
    if m.get("release"):
        rel_year = f'<div class="spec"><div class="k">Release</div><div class="v">{m["release"]}</div></div>'
    desc = miner_description(m, coin, e, p, be)
    body = f"""
<div class="crumbs"><a href="../../">Home</a> / <a href="../../{ALGO_SLUG[m['algo']]}/">{m['algo']} miners</a> / {m['name']}</div>
<h1>{m['name']} profitability &amp; price <span class="badge-live"><i></i>LIVE</span></h1>
<p class="lede">{m['brand']} {m['algo']} miner for {coin}. Currently <b style="color:var(--green)">{money(p)}/day</b> net at ${DEFAULT_RATE}/kWh.</p>

<div class="specgrid">
  <div class="spec"><div class="k">Algorithm</div><div class="v">{m['algo']}</div></div>
  <div class="spec"><div class="k">Brand</div><div class="v"><a href="../../brands/{brand_slug(m['brand'])}/" style="color:var(--blue)">{m['brand']}</a></div></div>
  <div class="spec"><div class="k">Coins</div><div class="v">{coin}</div></div>
  <div class="spec"><div class="k">Hashrate</div><div class="v">{m['hr']:g} {m['unit']}</div></div>
  <div class="spec"><div class="k">Power</div><div class="v">{m['power']:,} W</div></div>
  <div class="spec"><div class="k">Efficiency</div><div class="v">{e:.1f} {EFF_UNIT[m['unit']]}</div></div>
  {rel_year}
  <div class="spec"><div class="k">Est. price</div><div class="v">${m['price']:,}</div></div>
  <div class="spec"><div class="k">Revenue/day</div><div class="v">{money(rev(m))}</div></div>
  <div class="spec"><div class="k">Break-even elec.</div><div class="v">${be:.3f}</div></div>
</div>

<div class="panel" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <a class="cta" href="../../contact/?miner={m['slug']}">Request {m['name']} quote →</a>
  <a class="cta secondary" href="../../contact/?topic=hosting&miner={m['slug']}">Get hosting quote</a>
  <span style="font-size:12px;color:var(--ink3)">We query 50+ vendors &amp; 30+ hosting partners — reply within 24h</span>
</div>

<h2>About the {m['name']}</h2>
<div class="prose">{desc}</div>

<div class="ad-slot">Advertisement — AdSense rectangle 336×280</div>

<h2>Profitability vs electricity cost</h2>
<div class="panel" style="overflow-x:auto"><table>
<thead><tr><th class="num">Rate ($/kWh)</th><th class="num">Cost/day</th><th class="num">Revenue/day</th><th class="num">Net profit/day</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Break-even electricity price</h2>
<div class="prose"><p>{(f'The {m["name"]} currently earns <b>{money(p)}/day</b> net at ${DEFAULT_RATE}/kWh ({UPDATED} snapshot). It stays profitable as long as your electricity costs less than <b>${be:.3f}/kWh</b> — its break-even rate. Difficulty increases and coin-price moves will shift this number — recheck before ordering.' )}</p></div>

<h2>FAQ — {m['name']}</h2>
<div class="faq">{faq_html}</div>

<h2>Other {m['algo']} miners</h2>
<div class="cards">{rel}</div>"""
    head = (f'<script type="application/ld+json">{json.dumps(ld_product)}</script>'
            f'<script type="application/ld+json">{json.dumps(ld_faq)}</script>'
            f'<script type="application/ld+json">{json.dumps(ld_bc)}</script>')
    html = layout(f"{m['name']} Profitability, Price & Specs — {m['algo']} Miner | ASIC Miner Prices",
                  f"{m['name']} mining profitability: {money(p)}/day at ${DEFAULT_RATE}/kWh. Full specs, break-even electricity price and where to buy the {m['brand']} {m['name']}.",
                  ALGO_SLUG[m["algo"]], body, f"/miners/{m['slug']}/", 2, head)
    write(f"miners/{m['slug']}/index.html", html)

BRAND_BLURB = {
    "Bitmain": "Bitmain is the largest ASIC manufacturer on earth — its Antminer line dominates Bitcoin (SHA-256), Litecoin/Dogecoin (Scrypt) and Kaspa (kHeavyHash) mining. S21-generation machines are the current industry benchmark for efficiency.",
    "MicroBT": "MicroBT's Whatsminer line is the strongest alternative to Bitmain for Bitcoin mining, known for robust build quality and stable firmware. The M60 series competes head-to-head with the Antminer S21 family.",
    "IceRiver": "IceRiver is the reference Kaspa (kHeavyHash) manufacturer, consistently shipping the most efficient KAS miners first. Its KS series sets the pace for the Kaspa ASIC market.",
    "Canaan": "Canaan (Avalon) invented the Bitcoin ASIC in 2013. Its Avalon line offers reliable air-cooled and home-class quiet miners, often at aggressive prices.",
    "Goldshell": "Goldshell specializes in compact, lower-power ASICs — the go-to brand for home miners targeting altcoins with quiet, plug-and-play boxes.",
    "Elphapex": "Elphapex is a newer manufacturer with competitive Scrypt and SHA-256 machines, often undercutting incumbents on price per terahash.",
    "iPollo": "iPollo builds altcoin ASICs (ETHash/ETC, Grin, and others) and compact home miners.",
    "Innosilicon": "Innosilicon is a veteran ASIC design house with a wide altcoin catalog; its older Scrypt and SHA-256 units trade actively on the used market.",
    "StrongU": "StrongU shipped popular SHA-256 and altcoin miners; remaining units are mostly second-hand today.",
    "Ebang": "Ebang's Ebit line covers budget SHA-256 machines, mostly traded on the secondary market.",
    "ElphaPex": "ElphaPex is a newer manufacturer with competitive Scrypt and SHA-256 machines, often undercutting incumbents on price per terahash.",
}

def brand_slug(brand):
    return re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")

def page_brand(brand):
    ms = sorted([m for m in MINERS if m["brand"] == brand], key=lambda m: -profit(m))
    if not ms:
        return
    coin_list = sorted({m["algo"] for m in ms})
    blurb = BRAND_BLURB.get(brand, f"{brand} ASIC miners — full lineup with live profitability and prices.")
    top = ms[0]
    body = f"""
<div class="crumbs"><a href="../">Home</a> / {brand} miners</div>
<h1>{brand} miners — full lineup <span class="badge-live"><i></i>LIVE</span></h1>
<p class="lede">{blurb}</p>
<div class="cards">
  <div class="card"><div class="k">Top {brand} miner</div><div class="v" style="font-size:18px"><a class="miner-name" href="../miners/{top['slug']}/">{top['name']}</a></div><div class="s">{money(profit(top))}/day net</div></div>
  <div class="card"><div class="k">Models tracked</div><div class="v">{len(ms)}</div><div class="s">{" · ".join(coin_list)}</div></div>
  <div class="card"><div class="k">Price range</div><div class="v" style="font-size:18px">${min(m['price'] for m in ms):,} – ${max(m['price'] for m in ms):,}</div><div class="s">street prices, updated {UPDATED}</div></div>
</div>
<h2>All {brand} miners by profitability</h2>
<div class="panel" style="overflow-x:auto">{miners_table(ms)}</div>
<div class="prose"><p>Need a quote on a {brand} machine? We source directly from {brand} and its authorized distributors through our vendor network — <a href="../contact/">request a live quote</a> and we'll confirm stock and delivered pricing within 24 hours.</p></div>"""
    html = layout(f"{brand} Miners — Full Lineup, Prices & Profitability | ASIC Miner Prices",
                  f"All {len(ms)} {brand} ASIC miners ranked by live profitability: specs, prices, break-even electricity rates. {blurb[:110]}",
                  "overview", body, f"/brands/{brand_slug(brand)}/", 1)
    write(f"brands/{brand_slug(brand)}/index.html", html)

def page_algo(algo):
    ms = sorted([m for m in MINERS if m["algo"] == algo], key=lambda m: -profit(m))
    coin = COIN[algo]
    top = ms[0]
    body = f"""
<div class="crumbs"><a href="../">Home</a> / {algo} miners</div>
<h1>Best {algo} miners — {coin} <span class="badge-live"><i></i>LIVE</span></h1>
<p class="lede">{ALGO_BLURB[algo]}</p>

<div class="cards">
  <div class="card"><div class="k">Top {algo} miner</div><div class="v" style="font-size:18px"><a class="miner-name" href="../miners/{top['slug']}/">{top['name']}</a></div><div class="s">{money(profit(top))}/day net</div></div>
  <div class="card"><div class="k">Miners tracked</div><div class="v">{len(ms)}</div><div class="s">{coin}</div></div>
  <div class="card"><div class="k">Hashprice snapshot</div><div class="v" style="font-size:18px">${HASHPRICE[algo]}<span style="font-size:13px;color:var(--ink3)">/{EFF_UNIT[ms[0]['unit']].split('/')[1]}/day</span></div><div class="s">{UPDATED}</div></div>
</div>

{rate_bar()}

<h2>{algo} miner ranking</h2>
<div class="panel" style="overflow-x:auto">{miners_table(ms, depth=1)}</div>

<div class="ad-slot">Advertisement — AdSense responsive</div>

<div class="prose">
<h2>Choosing a {algo} miner</h2>
<p>Within {algo}, the decision comes down to three numbers: <b>efficiency</b> (lower {EFF_UNIT[ms[0]['unit']]} survives difficulty increases longer), <b>daily profit at your electricity rate</b>, and <b>break-even electricity price</b>. New-generation machines cost more per unit of hashrate but stay profitable at electricity rates that kill older hardware.</p>
<p>Not sure between two models? Use the <a href="../compare/">head-to-head comparison</a> or run your exact numbers in the <a href="../calculator/">calculator</a>.</p>
</div>"""
    html = layout(f"Best {algo} Miners — {coin} Profitability Ranking | ASIC Miner Prices",
                  f"Live {algo} ({coin}) ASIC miner ranking: daily profit, efficiency, prices and break-even rates for {len(ms)} miners. Updated {UPDATED}.",
                  ALGO_SLUG[algo], body, f"/{ALGO_SLUG[algo]}/", 1)
    write(f"{ALGO_SLUG[algo]}/index.html", html)

def page_calculator():
    data = [dict(name=m["name"], hr=m["hr"], unit=m["unit"], power=m["power"], price=m["price"], hp=HASHPRICE[m["algo"]]) for m in MINERS]
    body = f"""
<div class="crumbs"><a href="../">Home</a> / Calculator</div>
<h1>ASIC mining profitability calculator</h1>
<p class="lede">Pick a miner, enter your electricity rate and pool fee — get daily, monthly and yearly net profit, break-even electricity and payback period.</p>

<div class="panel">
<div id="calc-form">
<div class="form-grid">
  <div><label>Miner</label><select id="calc-miner"></select></div>
  <div><label>Electricity cost ($/kWh)</label><input type="number" id="calc-rate" value="0.072" min="0" max="1" step="0.005"></div>
  <div><label>Pool fee (%)</label><input type="number" id="calc-fee" value="1" min="0" max="10" step="0.1"></div>
</div>
</div>
</div>

<div class="cards">
  <div class="card"><div class="k">Net profit / day</div><div class="v result-hero" id="calc-daily">—</div></div>
  <div class="card"><div class="k">Net profit / month</div><div class="v" id="calc-monthly">—</div></div>
  <div class="card"><div class="k">Net profit / year</div><div class="v" id="calc-yearly">—</div></div>
</div>
<div class="cards">
  <div class="card"><div class="k">Gross revenue / day</div><div class="v" id="calc-rev" style="font-size:18px">—</div></div>
  <div class="card"><div class="k">Electricity cost / day</div><div class="v" id="calc-cost" style="font-size:18px;color:var(--red)">—</div></div>
  <div class="card"><div class="k">Break-even electricity</div><div class="v" id="calc-be" style="font-size:18px">—</div></div>
  <div class="card"><div class="k">Payback period</div><div class="v" id="calc-roi" style="font-size:18px">—</div></div>
</div>

<div class="ad-slot">Advertisement — AdSense responsive</div>

<div class="prose">
<h2>How to use this calculator</h2>
<ul>
<li><b>Electricity rate</b> — your all-in cost per kWh, including demand charges and cooling overhead (add ~10% for fans/HVAC in warm climates).</li>
<li><b>Pool fee</b> — most pools charge 0.5–2.5%. PPS+ and FPPS pools smooth payout variance.</li>
<li><b>Break-even electricity</b> — the kWh price where this miner exactly covers its power bill. Below it you profit; above it you lose money every day.</li>
</ul>
</div>
<script>window.MINERS = {json.dumps(data)};</script>"""
    html = layout("ASIC Mining Profitability Calculator | ASIC Miner Prices",
                  "Calculate ASIC mining profit: daily, monthly and yearly net, break-even electricity price and ROI for any miner and power rate.",
                  "calculator", body, "/calculator/", 1)
    write("calculator/index.html", html)

def page_compare_index():
    cards = "".join(
        f'<div class="card"><div class="k">Head-to-head</div><div class="v" style="font-size:15px;padding-top:4px"><a class="miner-name" href="{a}-vs-{b}/">{by_slug(a)["name"]} vs {by_slug(b)["name"]}</a></div><div class="s">{by_slug(a)["algo"]} · updated {UPDATED}</div></div>'
        for a, b in COMPARE_PAIRS)
    body = f"""
<div class="crumbs"><a href="../">Home</a> / Compare</div>
<h1>Compare ASIC miners head-to-head</h1>
<p class="lede">Side-by-side spec, efficiency, profit and break-even comparisons of the most-shopped ASIC miners.</p>
<div class="cards">{cards}</div>"""
    html = layout("Compare ASIC Miners Head-to-Head | ASIC Miner Prices",
                  "Side-by-side ASIC miner comparisons: specs, efficiency, daily profit, price and payback period.",
                  "compare", body, "/compare/", 1)
    write("compare/index.html", html)

def page_compare(sa, sb):
    a, b = by_slug(sa), by_slug(sb)
    rows_def = [
        ("Algorithm", a["algo"], b["algo"], None),
        ("Coins", COIN[a["algo"]], COIN[b["algo"]], None),
        ("Hashrate", f'{a["hr"]:g} {a["unit"]}', f'{b["hr"]:g} {b["unit"]}', (a["hr"], b["hr"], "high")),
        ("Power draw", f'{a["power"]:,} W', f'{b["power"]:,} W', (a["power"], b["power"], "low")),
        ("Efficiency", f'{eff(a):.1f} vs {eff(b):.1f}'.split(" vs ")[0] + f' J/{"TH" if a["unit"]=="TH/s" else "GH"}', f'{eff(b):.1f} J/{"TH" if b["unit"]=="TH/s" else "GH"}', (eff(a), eff(b), "low")),
        ("Revenue/day", money(rev(a)), money(rev(b)), (rev(a), rev(b), "high")),
        (f"Profit/day @ ${DEFAULT_RATE}", money(profit(a)), money(profit(b)), (profit(a), profit(b), "high")),
        ("Break-even elec.", f"${breakeven(a):.3f}", f"${breakeven(b):.3f}", (breakeven(a), breakeven(b), "high")),
        ("Est. price", f'${a["price"]:,}', f'${b["price"]:,}', (a["price"], b["price"], "low")),
    ]
    rows = ""
    for label, va, vb, cmp_ in rows_def:
        ca = cb = ""
        if cmp_:
            x, y, mode = cmp_
            if x != y:
                aw = (x > y) if mode == "high" else (x < y)
                ca, cb = (' class="win"', "") if aw else ("", ' class="win"')
        rows += f'<tr><td>{label}</td><td class="num"{ca}>{va}</td><td class="num"{cb}>{vb}</td></tr>'
    pa, pb = profit(a), profit(b)
    winner = a if pa > pb else b
    loser = b if winner is a else a
    body = f"""
<div class="crumbs"><a href="../../">Home</a> / <a href="../">Compare</a> / {a['name']} vs {b['name']}</div>
<h1>{a['name']} vs {b['name']}</h1>
<p class="lede">{a['algo']} head-to-head: which miner wins on profit, efficiency and break-even rate at ${DEFAULT_RATE}/kWh (snapshot {UPDATED}).</p>

<div class="panel" style="overflow-x:auto"><table>
<thead><tr><th></th><th class="num">{a['name']}</th><th class="num">{b['name']}</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<div class="verdict"><b style="color:var(--ink)">Verdict:</b> The <b>{winner['name']}</b> wins this matchup — {money(profit(winner))}/day vs {money(profit(loser))}/day at ${DEFAULT_RATE}/kWh, with a break-even rate of ${breakeven(winner):.3f}/kWh{'. The ' + loser['name'] + ' only makes sense at a significantly lower purchase price or electricity rate.' if profit(loser) > 0 else ', while the ' + loser['name'] + f' is underwater at ${DEFAULT_RATE}/kWh.'}</div>

<div class="vs-wrap">
  <div class="card"><div class="k">{a['brand']}</div><div class="v" style="font-size:16px"><a class="miner-name" href="../../miners/{a['slug']}/">{a['name']} full page →</a></div><div class="s">{money(pa)}/day · ${a['price']:,}</div></div>
  <div class="card"><div class="k">{b['brand']}</div><div class="v" style="font-size:16px"><a class="miner-name" href="../../miners/{b['slug']}/">{b['name']} full page →</a></div><div class="s">{money(pb)}/day · ${b['price']:,}</div></div>
</div>

<div class="ad-slot">Advertisement — AdSense responsive</div>"""
    html = layout(f"{a['name']} vs {b['name']} — Profitability & Specs Compared | ASIC Miner Prices",
                  f"{a['name']} vs {b['name']}: daily profit, efficiency and break-even electricity compared head-to-head. Updated {UPDATED}.",
                  "compare", body, f"/compare/{sa}-vs-{sb}/", 2)
    write(f"compare/{sa}-vs-{sb}/index.html", html)

GUIDES = [
    ("how-to-choose-an-asic-miner", "How to Choose an ASIC Miner (2026 Buyer's Guide)",
     "The 5-step framework for picking an ASIC miner: efficiency, electricity rate, payback period, resale value and firmware ecosystem.",
     """<p>Buying an ASIC miner is a bet on three variables: the coin's price, network difficulty, and your electricity cost. Here's the framework professional hosting buyers use:</p>
<ul>
<li><b>1. Lock your electricity rate first.</b> Everything else follows. Under $0.06/kWh almost any current-gen miner works; above $0.10/kWh only top-efficiency machines survive.</li>
<li><b>2. Buy efficiency, not hashrate.</b> A 270 TH/s miner at 13.5 J/TH outlives a 200 TH/s miner at 17.5 J/TH through difficulty increases. Efficiency determines your break-even electricity price.</li>
<li><b>3. Compute payback at pessimistic assumptions.</b> Use today's hashprice minus 20%. If payback is still under 12 months, the deal is solid.</li>
<li><b>4. Check resale liquidity.</b> Bitmain and MicroBT hold value; niche brands depreciate fast.</li>
<li><b>5. Plan infrastructure.</b> A 3.5 kW miner needs a dedicated 240V/20A circuit and moves as much air as a small shop-vac. Budget for PDUs, networking and noise.</li>
</ul>
<p>Run your exact scenario in our <a href="../../calculator/">profitability calculator</a> before wiring any money.</p>"""),
    ("asic-mining-electricity-costs", "Electricity Cost: The Number That Decides Mining Profit",
     "Why $0.02/kWh separates winning and losing mining operations, and how to compute your real all-in power cost.",
     """<p>Two identical Antminer S21s can be a great investment and a terrible one — the only difference is the power bill. Electricity is 70–90% of a miner's operating cost, so small rate differences compound brutally.</p>
<p><b>Your real rate is not your utility's headline rate.</b> Add demand charges, delivery fees, taxes, and the ~5–10% overhead from cooling and fans. A "$0.08" residential plan is often $0.11 all-in.</p>
<ul>
<li><b>$0.02–0.05/kWh</b> — industrial/hosting territory. Nearly all current hardware profitable.</li>
<li><b>$0.06–0.09/kWh</b> — good home/ sheds rate. Stick to latest-gen efficiency leaders.</li>
<li><b>$0.10–0.14/kWh</b> — marginal. Only the most efficient machines, and only in strong markets.</li>
<li><b>$0.15+/kWh</b> — don't mine. Buy the coin instead.</li>
</ul>
<p>Every miner page on this site lists its <b>break-even electricity price</b> — compare it to your all-in rate, not your nominal one.</p>"""),
    ("what-is-merged-mining", "Merged Mining Explained: How Scrypt Miners Earn LTC + DOGE",
     "Merged mining (AuxPoW) lets one Scrypt ASIC mine Litecoin and Dogecoin at the same time — here's how it works and why it matters for profitability.",
     """<p>Scrypt miners like the Antminer L9 don't choose between Litecoin and Dogecoin — they mine both at once. The technique is called <b>merged mining</b>, standardized as AuxPoW (Auxiliary Proof of Work).</p>
<p>The miner's proof-of-work is submitted to the Litecoin network, and the same work is embedded in a Dogecoin block via a cryptographic proof. Dogecoin accepts Litecoin's work as valid for its own chain. No extra electricity, no split hashrate — genuinely free additional revenue.</p>
<p>In practice DOGE adds 30–60% on top of LTC revenue depending on the DOGE price, which is why Scrypt hashprice ($/GH/day) looks so rich compared to the LTC-only math. When comparing Scrypt miners, always use merged-mining revenue — any calculator showing LTC-only income is missing a third to half the picture.</p>"""),
]

def page_blog_index(articles):
    cards = "".join(
        f'<div class="card"><div class="k">{a["date"]}</div><div class="v" style="font-size:15px;padding-top:4px"><a class="miner-name" href="{a["slug"]}/">{a["title"]}</a></div><div class="s">{a["desc"]}</div></div>'
        for a in articles)
    body = f"""
<div class="crumbs"><a href="../">Home</a> / Blog</div>
<h1>Mining blog — market analysis &amp; buyer guides</h1>
<p class="lede">Weekly analysis from our desk: miner comparisons, real electricity math, hosting intel and market timing — written from live pricing across our vendor network.</p>
<div class="cards">{cards}</div>"""
    html = layout("Bitcoin & ASIC Mining Blog — Market Analysis | ASIC Miner Prices",
                  "Weekly ASIC mining analysis: miner comparisons, profitability math, hosting insights and buying guides from live market data.",
                  "blog", body, "/blog/", 1)
    write("blog/index.html", html)

def page_blog_post(a, articles):
    with open(os.path.join(ROOT, "content", "articles", a["file"])) as f:
        content = f.read()
    others = "".join(f'<li><a href="../{o["slug"]}/">{o["title"]}</a></li>' for o in articles if o["slug"] != a["slug"]) or '<li><a href="../../contact/">Request a quote</a></li>'
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"],
          "datePublished": a["date"], "author": {"@type": "Organization", "name": "ASIC Miner Prices"},
          "description": a["desc"]}
    body = f"""
<div class="crumbs"><a href="../../">Home</a> / <a href="../">Blog</a> / {a['title']}</div>
<h1>{a['title']}</h1>
<p class="lede">{a['desc']} — <span style="color:var(--ink3)">{a['date']}</span></p>
<div class="prose">{content}</div>
<div class="panel" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:24px">
  <a class="cta" href="../../contact/">Get a live quote from our vendor network →</a>
  <span style="font-size:12px;color:var(--ink3)">50+ verified vendors · 30+ partner hosting facilities · reply within 24h</span>
</div>
<h2>Keep reading</h2>
<div class="prose"><ul>{others}</ul></div>"""
    head = f'<script type="application/ld+json">{json.dumps(ld)}</script>'
    html = layout(f"{a['title']} | ASIC Miner Prices", a["desc"], "blog", body, f"/blog/{a['slug']}/", 2, head)
    write(f"blog/{a['slug']}/index.html", html)

def load_articles():
    p = os.path.join(ROOT, "content", "articles.json")
    if not os.path.exists(p):
        return []
    arts = json.load(open(p))
    return sorted(arts, key=lambda a: a["date"], reverse=True)

def page_contact():
    body = """
<div class="crumbs"><a href="../">Home</a> / Contact</div>
<h1>Contact us — quotes, stock &amp; hosting</h1>
<p class="lede">Tell us which miner you're looking at and your electricity rate — we reply within 24 hours with live pricing, stock and delivery options. You can also write directly to <b>contact@asicminerprices.com</b>.</p>

<div class="panel" style="max-width:640px">
<form id="contact-form" action="https://formsubmit.co/contact@asicminerprices.com" method="POST" style="display:grid;gap:14px">
  <input type="hidden" name="_subject" value="New inquiry — asicminerprices.com">
  <input type="hidden" name="_captcha" value="false">
  <input type="hidden" name="_template" value="table">
  <input type="text" name="_honey" style="display:none">
  <label style="display:grid;gap:6px">Your name
    <input type="text" name="name" required style="padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg2);color:var(--ink)"></label>
  <label style="display:grid;gap:6px">Your email
    <input type="email" name="email" required style="padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg2);color:var(--ink)"></label>
  <label style="display:grid;gap:6px">Topic
    <select name="topic" id="contact-topic" style="padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg2);color:var(--ink)">
      <option value="quote">Price quote / stock</option>
      <option value="hosting">Hosting quote</option>
      <option value="bulk">Bulk / reseller order</option>
      <option value="other">Other question</option>
    </select></label>
  <label style="display:grid;gap:6px">Miner of interest
    <input type="text" name="miner" id="contact-miner" placeholder="e.g. Antminer S21 Pro" style="padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg2);color:var(--ink)"></label>
  <label style="display:grid;gap:6px">Message
    <textarea name="message" rows="5" required style="padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg2);color:var(--ink)"></textarea></label>
  <button class="cta" type="submit" style="border:0;cursor:pointer">Send message →</button>
</form>
</div>
<script>
(function(){
  const q = new URLSearchParams(location.search);
  const miner = q.get('miner');
  if (miner) {
    const inp = document.getElementById('contact-miner');
    inp.value = miner.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
  const topic = q.get('topic');
  if (topic) document.getElementById('contact-topic').value = topic;
})();
</script>

<div class="prose">
<h2>Why buy through our network</h2>
<p>We don't hold stock — we hold <b>relationships</b>. ASIC Miner Prices is connected to <b>50+ verified machine vendors</b> (manufacturers, authorized distributors and vetted resellers) and <b>30+ partner hosting facilities</b> across North America, South America and Africa. When you send one inquiry, we query the whole network and come back with the best live combination of price, stock and power rate.</p>
<ul>
  <li><b>Price quotes</b> — live street pricing and confirmed stock across our vendor network, not stale listing prices.</li>
  <li><b>Hosting</b> — facility matching at $0.04–0.07/kWh all-in, with dashboards, insurance and contract terms we've already vetted.</li>
  <li><b>Bulk orders</b> — container-scale pricing for farms and resellers, direct from distributors.</li>
  <li><b>Second-hand &amp; rare models</b> — access to off-market batches our network doesn't list publicly.</li>
</ul>
</div>"""
    html = layout("Contact — Miner Quotes, Stock & Hosting | ASIC Miner Prices",
                  "Contact the ASIC Miner Prices team for live miner quotes, stock checks, hosting and bulk orders. Reply within 24 hours.",
                  "contact", body, "/contact/", 1)
    write("contact/index.html", html)


def page_guides():
    cards = "".join(
        f'<div class="card"><div class="k">Guide</div><div class="v" style="font-size:15px;padding-top:4px"><a class="miner-name" href="{slug}/">{title}</a></div><div class="s">{desc}</div></div>'
        for slug, title, desc, _ in GUIDES)
    body = f"""
<div class="crumbs"><a href="../">Home</a> / Guides</div>
<h1>ASIC mining guides</h1>
<p class="lede">Practical, numbers-first guides for buying and running ASIC miners.</p>
<div class="cards">{cards}</div>"""
    html = layout("ASIC Mining Guides | ASIC Miner Prices",
                  "Practical ASIC mining guides: choosing hardware, electricity costs, merged mining and profitability strategy.",
                  "guides", body, "/guides/", 1)
    write("guides/index.html", html)

def page_guide(slug, title, desc, content):
    body = f"""
<div class="crumbs"><a href="../../">Home</a> / <a href="../">Guides</a> / {title.split(':')[0]}</div>
<h1>{title}</h1>
<p class="lede">{desc}</p>
<div class="prose" style="margin-top:18px">{content}</div>
<div class="ad-slot">Advertisement — AdSense in-article</div>
<div class="panel" style="display:flex;gap:12px;flex-wrap:wrap">
  <a class="cta" href="../../calculator/">Run the calculator →</a>
  <a class="cta secondary" href="../../">See live rankings</a>
</div>"""
    html = layout(f"{title} | ASIC Miner Prices", desc, "guides", body, f"/guides/{slug}/", 2)
    write(f"guides/{slug}/index.html", html)

def sitemap():
    urls = ["/", "/calculator/", "/compare/", "/guides/", "/contact/", "/blog/"] + [f"/{s}/" for s in ALGO_SLUG.values()]
    urls += [f"/miners/{m['slug']}/" for m in MINERS]
    urls += [f"/brands/{brand_slug(b)}/" for b in sorted({m['brand'] for m in MINERS})]
    urls += [f"/blog/{a['slug']}/" for a in load_articles()]
    urls += [f"/compare/{a}-vs-{b}/" for a, b in COMPARE_PAIRS]
    urls += [f"/guides/{g[0]}/" for g in GUIDES]
    today = datetime.date.today().isoformat()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    xml += "\n</urlset>\n"
    write("sitemap.xml", xml)
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    return len(urls)

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    page_index()
    for m in MINERS:
        page_miner(m)
    for algo in ALGO_SLUG:
        page_algo(algo)
    page_calculator()
    page_compare_index()
    for a, b in COMPARE_PAIRS:
        page_compare(a, b)
    page_contact()
    articles = load_articles()
    page_blog_index(articles)
    for a in articles:
        page_blog_post(a, articles)
    for b in sorted({m["brand"] for m in MINERS}):
        page_brand(b)
    page_guides()
    for g in GUIDES:
        page_guide(*g)
    n = sitemap()
    total = sum(len(files) for _, _, files in os.walk(OUT))
    print(f"OK — {n} URLs in sitemap, {total} files in dist/")

if __name__ == "__main__":
    main()
