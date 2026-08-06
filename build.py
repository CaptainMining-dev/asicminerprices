#!/usr/bin/env python3
"""asicminerprices.com — static site generator.
Generates the full multi-page site into dist/. No dependencies.
Data = plausible snapshot constants; swap HASHPRICE/prices with live API data later.
"""
import json, os, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "dist")
SITE = "https://asicminerprices.com"
DEFAULT_RATE = 0.10
UPDATED = datetime.date.today().strftime("%B %d, %Y")

# $ revenue per hashrate unit per day (snapshot fallback if data.json missing)
HASHPRICE = {"SHA-256": 0.045, "kHeavyHash": 1.15, "Scrypt": 3.10}
COIN = {"SHA-256": "BTC", "kHeavyHash": "KAS", "Scrypt": "LTC+DOGE"}
ALGO_SLUG = {"SHA-256": "sha-256", "kHeavyHash": "kheavyhash", "Scrypt": "scrypt"}

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
}

MINERS = [
    # name, brand, algo, hashrate, unit, power W, price USD
    dict(slug="antminer-s21-xp", name="Antminer S21 XP", brand="Bitmain", algo="SHA-256", hr=270, unit="TH/s", power=3645, price=5999),
    dict(slug="antminer-s21-pro", name="Antminer S21 Pro", brand="Bitmain", algo="SHA-256", hr=234, unit="TH/s", power=3510, price=4200),
    dict(slug="antminer-s21-plus", name="Antminer S21+", brand="Bitmain", algo="SHA-256", hr=216, unit="TH/s", power=3564, price=3600),
    dict(slug="antminer-s21", name="Antminer S21", brand="Bitmain", algo="SHA-256", hr=200, unit="TH/s", power=3500, price=2900),
    dict(slug="whatsminer-m60s", name="Whatsminer M60S", brand="MicroBT", algo="SHA-256", hr=186, unit="TH/s", power=3441, price=2400),
    dict(slug="antminer-s19-xp", name="Antminer S19 XP", brand="Bitmain", algo="SHA-256", hr=140, unit="TH/s", power=3010, price=1650),
    dict(slug="whatsminer-m30s-plus-plus", name="Whatsminer M30S++", brand="MicroBT", algo="SHA-256", hr=112, unit="TH/s", power=3472, price=950),
    dict(slug="iceriver-ks7", name="IceRiver KS7", brand="IceRiver", algo="kHeavyHash", hr=30, unit="TH/s", power=3500, price=5600),
    dict(slug="antminer-ks5-pro", name="Antminer KS5 Pro", brand="Bitmain", algo="kHeavyHash", hr=21, unit="TH/s", power=3150, price=3200),
    dict(slug="antminer-ks5l", name="Antminer KS5L", brand="Bitmain", algo="kHeavyHash", hr=12, unit="TH/s", power=1850, price=1700),
    dict(slug="iceriver-ks3m", name="IceRiver KS3M", brand="IceRiver", algo="kHeavyHash", hr=6, unit="TH/s", power=3400, price=800),
    dict(slug="antminer-l9", name="Antminer L9", brand="Bitmain", algo="Scrypt", hr=16, unit="GH/s", power=3360, price=7500),
    dict(slug="antminer-l7", name="Antminer L7", brand="Bitmain", algo="Scrypt", hr=9.05, unit="GH/s", power=3425, price=4200),
    dict(slug="elphapex-dg1", name="Elphapex DG1", brand="Elphapex", algo="Scrypt", hr=11, unit="GH/s", power=3420, price=3600),
]

COMPARE_PAIRS = [
    ("antminer-s21-xp", "antminer-s21-pro"),
    ("antminer-s21", "whatsminer-m60s"),
    ("antminer-ks5-pro", "antminer-ks5l"),
    ("iceriver-ks7", "antminer-ks5-pro"),
    ("antminer-l9", "antminer-l7"),
    ("antminer-l9", "elphapex-dg1"),
]

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
    ("/calculator/", "Calculator", "calculator"),
    ("/compare/", "Compare", "compare"),
    ("/guides/", "Guides", "guides"),
]

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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/style.css">
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
<script src="{r}assets/app.js"></script>
</body>
</html>"""

def rate_bar():
    return """<div class="panel rate-bar">
  <label for="elec-rate"><b>Electricity cost</b></label>
  <input type="range" id="elec-rate" min="0.02" max="0.20" step="0.005" value="0.10">
  <span class="rate-val" id="rate-val">$0.100/kWh</span>
</div>"""

def miner_row(m):
    p = profit(m)
    e = eff(m)
    roi = round(m["price"] / p) if p > 0 else None
    return f"""<tr data-hr="{m['hr']}" data-hp="{HASHPRICE[m['algo']]}" data-power="{m['power']}" data-price="{m['price']}" data-algo="{m['algo']}">
<td><a class="miner-name" href="{{{{R}}}}miners/{m['slug']}/">{m['name']}</a> <span class="algo-pill">{m['algo']}</span></td>
<td class="num" data-col-val="hr" data-sort="{m['hr']}">{m['hr']:g} {m['unit']}</td>
<td class="num" data-col-val="power" data-sort="{m['power']}">{m['power']:,} W</td>
<td class="num" data-col-val="eff" data-sort="{e}">{e:.1f} J/{'TH' if m['unit']=='TH/s' else 'GH'}<span class="effbar"><i style="width:{max(4,min(100,100-(e-12)*3)):.0f}%"></i></span></td>
<td class="num profit-cell" data-col-val="profit" data-sort="{p}">{pill(p)}</td>
<td class="num" data-col-val="price" data-sort="{m['price']}">${m['price']:,}</td>
<td class="num roi-cell" data-col-val="roi" data-sort="{roi if roi else 1e9}">{str(roi)+' d' if roi else '—'}</td>
</tr>"""

TABLE_HEAD = """<thead><tr>
<th data-col="miner">Miner</th><th class="num" data-col="hr">Hashrate</th><th class="num" data-col="power">Power</th>
<th class="num" data-col="eff">Efficiency</th><th class="num" data-col="profit">Profit/day</th>
<th class="num" data-col="price">Price</th><th class="num" data-col="roi">ROI</th></tr></thead>"""

def miners_table(miners, depth=0, autosort=True):
    rows = "\n".join(miner_row(m) for m in sorted(miners, key=lambda m: -profit(m)))
    r = "../" * depth
    t = f'<table class="{"autosort" if autosort else ""}">{TABLE_HEAD}<tbody>{rows}</tbody></table>'
    return t.replace("{{R}}", r)

# ---------------- pages ----------------
def page_index():
    ms = sorted(MINERS, key=lambda m: -profit(m))
    top = ms[0]
    best_eff = min(MINERS, key=eff)
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
  <div class="card"><div class="k">Top miner profit</div><div class="v" style="color:var(--green)">{money(profit(top))}<span style="font-size:13px;color:var(--ink3)">/day</span></div><div class="s">{top['name']} @ ${DEFAULT_RATE}/kWh</div></div>
  <div class="card"><div class="k">Miners tracked</div><div class="v">{len(MINERS)}</div><div class="s">3 algorithms · 4 brands</div></div>
  <div class="card"><div class="k">Best efficiency</div><div class="v">{eff(best_eff):.1f}<span style="font-size:13px;color:var(--ink3)"> J/TH</span></div><div class="s">{best_eff['name']}</div></div>
  <div class="card"><div class="k">{f"BTC ${LIVE.get('btc_usd', 0):,} · " if LIVE.get('btc_usd') else ""}Snapshot</div><div class="v" style="font-size:16px;padding-top:4px">{UPDATED}</div><div class="s">Hashprice: BTC ${HASHPRICE['SHA-256']}/TH · KAS ${HASHPRICE['kHeavyHash']}/TH · Scrypt ${HASHPRICE['Scrypt']}/GH</div></div>
</div>

{rate_bar()}

<div class="cards">
  <div class="card gold"><span class="tag gold">Best profitability</span><div class="v" style="font-size:18px"><a class="miner-name" href="miners/{top['slug']}/">{top['name']}</a></div><div class="s">{money(profit(top))}/day · ROI {round(top['price']/profit(top))} days</div></div>
  <div class="card blue"><span class="tag blue">Best efficiency</span><div class="v" style="font-size:18px"><a class="miner-name" href="miners/{best_eff['slug']}/">{best_eff['name']}</a></div><div class="s">{eff(best_eff):.1f} J/TH · {money(profit(best_eff))}/day</div></div>
  <div class="card violet"><span class="tag violet">Best budget</span><div class="v" style="font-size:18px"><a class="miner-name" href="miners/{budget['slug']}/">{budget['name']}</a></div><div class="s">${budget['price']:,} · {money(profit(budget))}/day</div></div>
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

<div class="ad-slot">Advertisement — AdSense responsive</div>

<div class="prose">
<h2>How ASIC miner profitability works</h2>
<p>An ASIC miner's daily profit is its mining revenue minus electricity cost. Revenue depends on the coin's price, network difficulty and block reward — captured in the <b>hashprice</b> (dollars earned per unit of hashrate per day). Electricity cost is simply power draw × 24h × your kWh rate, which is why the rate slider above is the single most important input: a miner profitable at $0.05/kWh can lose money at $0.15/kWh.</p>
<p>Before buying, check the <b>ROI in days</b> (machine price ÷ daily profit) and the <b>break-even electricity price</b> on each miner's page. Use our <a href="calculator/">profitability calculator</a> for pool fees and custom scenarios, or <a href="compare/">compare two miners head-to-head</a>.</p>
</div>"""
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "What is the most profitable ASIC miner right now?",
             "acceptedAnswer": {"@type": "Answer", "text": f"At a $0.10/kWh electricity rate, the {top['name']} currently leads at about {money(profit(top))} per day before pool fees."}},
            {"@type": "Question", "name": "How is ASIC miner profitability calculated?",
             "acceptedAnswer": {"@type": "Answer", "text": "Daily profit = (hashrate × hashprice) − (power in kW × 24 × electricity rate). Hashprice bundles coin price, network difficulty and block reward into one number."}},
            {"@type": "Question", "name": "What electricity rate do I need for mining to be profitable?",
             "acceptedAnswer": {"@type": "Answer", "text": "Each miner has a break-even electricity price listed on its page. Most profitable operations pay $0.02–$0.06/kWh; above $0.12/kWh only the newest generation stays profitable."}},
        ]}
    html = layout("Most Profitable ASIC Miners — Live Profitability & Prices | ASIC Miner Prices",
                  f"Live ranking of {len(MINERS)} ASIC miners by daily profit. Compare Bitcoin, Kaspa and Scrypt miners, set your electricity rate and find ROI before you buy.",
                  "overview", body, "/", 0,
                  f'<script type="application/ld+json">{json.dumps(faq)}</script>')
    write("index.html", html)

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
        (f"How long is the ROI on a {m['name']}?", (f"At ${m['price']:,} and {money(p)}/day net profit, the simple payback period is about {roi} days at current network conditions." if roi else f"At ${DEFAULT_RATE}/kWh the {m['name']} is currently not profitable, so ROI cannot be reached. Lower your electricity cost below ${be:.3f}/kWh.")),
        (f"What does the {m['name']} mine?", f"The {m['name']} is a {m['algo']} miner. It mines {coin}." + (" Scrypt miners mine Litecoin and Dogecoin simultaneously via merged mining." if m["algo"] == "Scrypt" else "")),
    ]
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    ld_product = {"@context": "https://schema.org", "@type": "Product", "name": m["name"],
                  "brand": {"@type": "Brand", "name": m["brand"]},
                  "description": f"{m['name']} {m['algo']} ASIC miner: {m['hr']:g} {m['unit']}, {m['power']}W, {e:.1f} J/{'TH' if m['unit']=='TH/s' else 'GH'}.",
                  "offers": {"@type": "Offer", "price": m["price"], "priceCurrency": "USD", "availability": "https://schema.org/InStock"}}
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    ld_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": m["algo"] + " miners", "item": SITE + "/" + ALGO_SLUG[m["algo"]] + "/"},
        {"@type": "ListItem", "position": 3, "name": m["name"]}]}
    body = f"""
<div class="crumbs"><a href="../../">Home</a> / <a href="../../{ALGO_SLUG[m['algo']]}/">{m['algo']} miners</a> / {m['name']}</div>
<h1>{m['name']} profitability &amp; price <span class="badge-live"><i></i>LIVE</span></h1>
<p class="lede">{m['brand']} {m['algo']} miner for {coin}. Currently <b style="color:var(--green)">{money(p)}/day</b> net at ${DEFAULT_RATE}/kWh.</p>

<div class="specgrid">
  <div class="spec"><div class="k">Algorithm</div><div class="v">{m['algo']}</div></div>
  <div class="spec"><div class="k">Coins</div><div class="v">{coin}</div></div>
  <div class="spec"><div class="k">Hashrate</div><div class="v">{m['hr']:g} {m['unit']}</div></div>
  <div class="spec"><div class="k">Power</div><div class="v">{m['power']:,} W</div></div>
  <div class="spec"><div class="k">Efficiency</div><div class="v">{e:.1f} J/{'TH' if m['unit']=='TH/s' else 'GH'}</div></div>
  <div class="spec"><div class="k">Est. price</div><div class="v">${m['price']:,}</div></div>
  <div class="spec"><div class="k">Revenue/day</div><div class="v">{money(rev(m))}</div></div>
  <div class="spec"><div class="k">Break-even elec.</div><div class="v">${be:.3f}</div></div>
</div>

<div class="panel" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <a class="cta" href="#" rel="sponsored nofollow">Check {m['name']} price →</a>
  <a class="cta secondary" href="#" rel="sponsored nofollow">Get hosting quote</a>
  <span style="font-size:12px;color:var(--ink3)">Affiliate links — we may earn a commission</span>
</div>

<div class="ad-slot">Advertisement — AdSense rectangle 336×280</div>

<h2>Profitability vs electricity cost</h2>
<div class="panel" style="overflow-x:auto"><table>
<thead><tr><th class="num">Rate ($/kWh)</th><th class="num">Cost/day</th><th class="num">Revenue/day</th><th class="num">Net profit/day</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>ROI at current rates</h2>
<div class="prose"><p>{(f'At <b>${m["price"]:,}</b> and <b>{money(p)}/day</b> net profit, the {m["name"]} pays itself back in roughly <b>{roi} days</b> at the {UPDATED} network snapshot. Difficulty increases and coin-price moves will shift this number — recheck before ordering.' if roi else f'At ${DEFAULT_RATE}/kWh the {m["name"]} is currently unprofitable ({money(p)}/day). You need electricity below <b>${be:.3f}/kWh</b> to break even.')}</p></div>

<h2>FAQ — {m['name']}</h2>
<div class="faq">{faq_html}</div>

<h2>Other {m['algo']} miners</h2>
<div class="cards">{rel}</div>"""
    head = (f'<script type="application/ld+json">{json.dumps(ld_product)}</script>'
            f'<script type="application/ld+json">{json.dumps(ld_faq)}</script>'
            f'<script type="application/ld+json">{json.dumps(ld_bc)}</script>')
    html = layout(f"{m['name']} Profitability, Price & Specs — {m['algo']} Miner | ASIC Miner Prices",
                  f"{m['name']} mining profitability: {money(p)}/day at $0.10/kWh. Full specs, ROI, break-even electricity price and where to buy the {m['brand']} {m['name']}.",
                  ALGO_SLUG[m["algo"]], body, f"/miners/{m['slug']}/", 2, head)
    write(f"miners/{m['slug']}/index.html", html)

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
  <div class="card"><div class="k">Hashprice snapshot</div><div class="v" style="font-size:18px">${HASHPRICE[algo]}<span style="font-size:13px;color:var(--ink3)">/{'TH' if ms[0]['unit']=='TH/s' else 'GH'}/day</span></div><div class="s">{UPDATED}</div></div>
</div>

{rate_bar()}

<h2>{algo} miner ranking</h2>
<div class="panel" style="overflow-x:auto">{miners_table(ms, depth=1)}</div>

<div class="ad-slot">Advertisement — AdSense responsive</div>

<div class="prose">
<h2>Choosing a {algo} miner</h2>
<p>Within {algo}, the decision comes down to three numbers: <b>efficiency</b> (lower J/{'TH' if ms[0]['unit']=='TH/s' else 'GH'} survives difficulty increases longer), <b>daily profit at your electricity rate</b>, and <b>payback period</b>. New-generation machines cost more per unit of hashrate but stay profitable at electricity rates that kill older hardware.</p>
<p>Not sure between two models? Use the <a href="../compare/">head-to-head comparison</a> or run your exact numbers in the <a href="../calculator/">calculator</a>.</p>
</div>"""
    html = layout(f"Best {algo} Miners — {coin} Profitability Ranking | ASIC Miner Prices",
                  f"Live {algo} ({coin}) ASIC miner ranking: daily profit, efficiency, prices and ROI for {len(ms)} miners. Updated {UPDATED}.",
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
  <div><label>Electricity cost ($/kWh)</label><input type="number" id="calc-rate" value="0.10" min="0" max="1" step="0.005"></div>
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
<p class="lede">Side-by-side spec, efficiency, profit and ROI comparisons of the most-shopped ASIC miners.</p>
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
        ("Profit/day @ $0.10", money(profit(a)), money(profit(b)), (profit(a), profit(b), "high")),
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
    roi_a = round(a["price"] / pa) if pa > 0 else None
    roi_b = round(b["price"] / pb) if pb > 0 else None
    winner = a if (roi_a or 9e9) < (roi_b or 9e9) else b
    loser = b if winner is a else a
    body = f"""
<div class="crumbs"><a href="../../">Home</a> / <a href="../">Compare</a> / {a['name']} vs {b['name']}</div>
<h1>{a['name']} vs {b['name']}</h1>
<p class="lede">{a['algo']} head-to-head: which miner wins on profit, efficiency and payback at ${DEFAULT_RATE}/kWh (snapshot {UPDATED}).</p>

<div class="panel" style="overflow-x:auto"><table>
<thead><tr><th></th><th class="num">{a['name']}</th><th class="num">{b['name']}</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<div class="verdict"><b style="color:var(--ink)">Verdict:</b> The <b>{winner['name']}</b> wins this matchup — {money(profit(winner))}/day vs {money(profit(loser))}/day, payback ~{round(winner['price']/profit(winner)) if profit(winner)>0 else '—'} days{'. The ' + loser['name'] + ' only makes sense at a significantly lower purchase price or electricity rate.' if profit(loser) > 0 else ', while the ' + loser['name'] + ' is underwater at $0.10/kWh.'}</div>

<div class="vs-wrap">
  <div class="card"><div class="k">{a['brand']}</div><div class="v" style="font-size:16px"><a class="miner-name" href="../../miners/{a['slug']}/">{a['name']} full page →</a></div><div class="s">{money(pa)}/day · ${a['price']:,}</div></div>
  <div class="card"><div class="k">{b['brand']}</div><div class="v" style="font-size:16px"><a class="miner-name" href="../../miners/{b['slug']}/">{b['name']} full page →</a></div><div class="s">{money(pb)}/day · ${b['price']:,}</div></div>
</div>

<div class="ad-slot">Advertisement — AdSense responsive</div>"""
    html = layout(f"{a['name']} vs {b['name']} — Profitability & Specs Compared | ASIC Miner Prices",
                  f"{a['name']} vs {b['name']}: daily profit, efficiency, break-even electricity and ROI compared head-to-head. Updated {UPDATED}.",
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
    urls = ["/", "/sha-256/", "/kheavyhash/", "/scrypt/", "/calculator/", "/compare/", "/guides/"]
    urls += [f"/miners/{m['slug']}/" for m in MINERS]
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
    for algo in HASHPRICE:
        page_algo(algo)
    page_calculator()
    page_compare_index()
    for a, b in COMPARE_PAIRS:
        page_compare(a, b)
    page_guides()
    for g in GUIDES:
        page_guide(*g)
    n = sitemap()
    total = sum(len(files) for _, _, files in os.walk(OUT))
    print(f"OK — {n} URLs in sitemap, {total} files in dist/")

if __name__ == "__main__":
    main()
