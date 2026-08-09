#!/usr/bin/env python3
"""Fetch live network data (100% free, no API key) and compute per-algo hashprice.
Sources:
  BTC  — mempool.space  (hashrate, difficulty, USD price)
  KAS  — kas.2miners.com public pool stats (network hashrate, live block reward, block time)
  LTC/DOGE — api.blockchair.com (difficulty, blocks/24h)  [merged-mined together]
  Prices — CoinGecko (KAS, LTC, DOGE)
Output: data.json consumed by build.py. On any failure, build.py keeps its snapshot constants.
"""
import json, os, sys, time, urllib.request, datetime, re

ROOT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) asicminerprices.com/1.0"}

def get(url, timeout=20, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"  retry {i+1}/{retries} {url[:55]}… ({e})", file=sys.stderr)
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"fetch failed: {url}")

def nethash_from_diff(difficulty, block_time):
    """Standard PoW relation: hashrate = difficulty * 2^32 / block_time."""
    return float(difficulty) * (2 ** 32) / float(block_time)

def main():
    TH, GH = 1e12, 1e9

    print("mempool.space (BTC)…")
    mp_hash = get("https://mempool.space/api/v1/mining/hashrate/3d")
    btc_nethash_h = float(mp_hash["currentHashrate"])          # H/s
    # transaction fees: average per-block fees over the last week (satoshis → BTC)
    try:
        fees = get("https://mempool.space/api/v1/mining/blocks/fees/1w")
        avg_fee_btc = (sum(f["avgFees"] for f in fees) / len(fees)) / 1e8
    except Exception:
        avg_fee_btc = 0.0
    try:
        btc_usd = float(get("https://mempool.space/api/v1/prices")["USD"])
    except Exception:
        btc_usd = None

    print("2miners (KAS)…")
    kas_stats = get("https://kas.2miners.com/api/stats")
    node = kas_stats["nodes"][0]
    kas_nethash_h = float(node["networkhashps"])               # H/s
    kas_reward = float(node["blockReward"]) / 1e8              # sompi → KAS
    kas_block_time = float(node["avgBlockTime"])               # ~0.1s (10 BPS)

    print("2miners (ZEC)…")
    zec_stats = get("https://zec.2miners.com/api/stats")
    znode = zec_stats["nodes"][0]
    zec_nethash_s = float(znode["networkhashps"])          # Sol/s
    ZEC_REWARD = 1.5625                                    # post Nov-2024 halving, next ~2028
    zec_reward = ZEC_REWARD
    zec_block_time = float(znode["avgBlockTime"])          # ~75s

    print("blockchair (LTC, DOGE)…")
    ltc = get("https://api.blockchair.com/litecoin/stats")["data"]
    doge = get("https://api.blockchair.com/dogecoin/stats")["data"]
    LTC_REWARD, LTC_BT = 6.25, 150.0      # next halving ~Aug 2027
    DOGE_REWARD, DOGE_BT = 10000.0, 60.0  # fixed reward
    ltc_nethash_h = nethash_from_diff(ltc["difficulty"], LTC_BT)
    doge_nethash_h = nethash_from_diff(doge["difficulty"], DOGE_BT)
    ltc_blocks_day = float(ltc["blocks_24h"])
    doge_blocks_day = float(doge["blocks_24h"])

    # ---- extra algos: each optional, failures fall back to snapshot constants ----
    extra = {}
    try:
        print("2miners (ETC)…")
        enode = get("https://etc.2miners.com/api/stats")["nodes"][0]
        etc_nethash = float(enode["networkhashps"])
        etc_bt = float(enode["avgBlockTime"])
        etc_height = int(enode["height"])
        etc_reward = 5.0 * 0.8 ** ((etc_height - 1) // 5_000_000)   # ECIP-1017 era
        extra["ETC"] = (etc_nethash, etc_reward, etc_bt)
    except Exception as e:
        print(f"  ETC skipped: {e}", file=sys.stderr)
    try:
        print("2miners (CKB)…")
        cnode = get("https://ckb.2miners.com/api/stats")["nodes"][0]
        extra["CKB"] = (float(cnode["networkhashps"]), float(cnode["blockReward"]) / 1e8, float(cnode["avgBlockTime"]))
    except Exception as e:
        print(f"  CKB skipped: {e}", file=sys.stderr)
    try:
        print("blockchair (DASH)…")
        dash = get("https://api.blockchair.com/dash/stats")["data"]
        dash_bt = 86400.0 / float(dash["blocks_24h"])
        dash_nethash = float(dash["difficulty"]) * (2 ** 32) / dash_bt
        extra["DASH"] = (dash_nethash, 2.02, dash_bt)   # reward ~7%/yr decrease, ~2.02 in 2026
    except Exception as e:
        print(f"  DASH skipped: {e}", file=sys.stderr)
    try:
        print("supportxmr (XMR)…")
        xmr = get("https://www.supportxmr.com/api/network/stats")
        extra["XMR"] = (float(xmr["difficulty"]) / 120.0, float(xmr["value"]) / 1e12, 120.0)
    except Exception as e:
        print(f"  XMR skipped: {e}", file=sys.stderr)
    try:
        print("asicminervalue calibration (ALPH)…")
        req = urllib.request.Request("https://www.asicminervalue.com/miners/bitmain/antminer-al1",
                                     headers={"User-Agent": UA["User-Agent"]})
        amv_html = urllib.request.urlopen(req, timeout=30).read().decode(errors="ignore")
        m = re.search(r"Income\s*\n?\s*\$([\d.]+)", amv_html) or re.search(r"Income</[^>]+>[^$]*\$([\d.]+)", amv_html)
        if not m:  # text skeleton fallback
            txt = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>", "", amv_html, flags=re.S))
            m = re.search(r"Income\s+\$([\d.]+)", txt)
        extra["ALPH_INCOME"] = float(m.group(1))   # $ revenue/day of AL1 (15.6 TH/s)
    except Exception as e:
        print(f"  ALPH calibration skipped: {e}", file=sys.stderr)

    print("CoinGecko (prices)…")
    ids = "kaspa,litecoin,dogecoin,zcash,ethereum-classic,nervos-network,dash,monero" + (",bitcoin" if btc_usd is None else "")
    prices = get(f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd")
    if btc_usd is None:
        btc_usd = float(prices["bitcoin"]["usd"])
    kas_usd = float(prices["kaspa"]["usd"])
    ltc_usd = float(prices["litecoin"]["usd"])
    doge_usd = float(prices["dogecoin"]["usd"])
    zec_usd = float(prices["zcash"]["usd"])
    etc_usd = float(prices["ethereum-classic"]["usd"]) if "ETC" in extra else 0
    ckb_usd = float(prices["nervos-network"]["usd"]) if "CKB" in extra else 0
    dash_usd = float(prices["dash"]["usd"]) if "DASH" in extra else 0
    xmr_usd = float(prices["monero"]["usd"]) if "XMR" in extra else 0

    # ---- hashprice = $ revenue per hashrate unit per day ----
    BTC_REWARD, BTC_BLOCKS_DAY = 3.125, 144.0   # next halving ~2028
    btc_block_total = BTC_REWARD + avg_fee_btc  # subsidy + tx fees (like asicminervalue)
    hp_sha256 = BTC_BLOCKS_DAY * btc_block_total * btc_usd / (btc_nethash_h / TH)

    kas_coins_day = (86400.0 / kas_block_time) * kas_reward
    hp_kas = kas_coins_day * kas_usd / (kas_nethash_h / TH)

    ltc_per_gh = ltc_blocks_day * LTC_REWARD / (ltc_nethash_h / GH)
    doge_per_gh = doge_blocks_day * DOGE_REWARD / (doge_nethash_h / GH)
    hp_scrypt = ltc_per_gh * ltc_usd + doge_per_gh * doge_usd   # merged mining

    zec_coins_day = (86400.0 / zec_block_time) * zec_reward
    hp_equihash = zec_coins_day * zec_usd / (zec_nethash_s / 1e3)   # $ per kSol/day

    extra_hp, extra_net = {}, {}
    if "ETC" in extra:
        nh, rw, bt = extra["ETC"]
        extra_hp["EtHash"] = round((86400.0 / bt) * rw * etc_usd / (nh / 1e6), 6)  # $/MH/day
        extra_net["ETC"] = {"nethash_th": round(nh / 1e12, 1), "block_reward": round(rw, 4)}
    if "CKB" in extra:
        nh, rw, bt = extra["CKB"]
        extra_hp["Eaglesong"] = round((86400.0 / bt) * rw * ckb_usd / (nh / 1e12), 6)  # $/TH/day
        extra_net["CKB"] = {"nethash_ph": round(nh / 1e15, 1), "block_reward": round(rw, 1)}
    if "DASH" in extra:
        nh, rw, bt = extra["DASH"]
        extra_hp["X11"] = round((86400.0 / bt) * rw * dash_usd / (nh / 1e9), 6)  # $/GH/day
        extra_net["DASH"] = {"nethash_ph": round(nh / 1e15, 1), "block_reward": rw}
    if "XMR" in extra:
        nh, rw, bt = extra["XMR"]
        extra_hp["RandomX"] = round((86400.0 / bt) * rw * xmr_usd / (nh / 1e3), 6)  # $/kH/day
        extra_net["XMR"] = {"nethash_gh": round(nh / 1e9, 2), "block_reward": round(rw, 4)}
    if "ALPH_INCOME" in extra:
        extra_hp["Blake3"] = round(extra["ALPH_INCOME"] / 15.6, 4)  # $/TH/day (calibrated on Antminer AL1)

    now = datetime.datetime.utcnow()
    out = {
        "source": "live: mempool.space + 2miners + blockchair + coingecko",
        "fetched_at": now.isoformat(timespec="seconds") + "Z",
        "updated_human": now.strftime("%B %d, %Y"),
        "btc_usd": round(btc_usd),
        "prices": {"BTC": round(btc_usd), "KAS": round(kas_usd, 6),
                   "LTC": round(ltc_usd, 2), "DOGE": round(doge_usd, 5),
                   "ZEC": round(zec_usd, 2)},
        "hashprice": {"SHA-256": round(hp_sha256, 5),
                      "kHeavyHash": round(hp_kas, 5),
                      "Scrypt": round(hp_scrypt, 4),
                      "Equihash": round(hp_equihash, 5),
                      **extra_hp},
        "networks": {
            "BTC": {"nethash_eh": round(btc_nethash_h / 1e18, 1), "block_reward": BTC_REWARD, "avg_fees_btc": round(avg_fee_btc, 4)},
            "KAS": {"nethash_ph": round(kas_nethash_h / 1e15, 1), "block_reward": round(kas_reward, 4)},
            "LTC": {"nethash_ph": round(ltc_nethash_h / 1e15, 2), "block_reward": LTC_REWARD},
            "DOGE": {"nethash_ph": round(doge_nethash_h / 1e15, 2), "block_reward": DOGE_REWARD},
            "ZEC": {"nethash_gsol": round(zec_nethash_s / 1e9, 2), "block_reward": round(zec_reward, 4)},
            **extra_net,
        },
    }
    with open(os.path.join(ROOT, "data.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print("OK → data.json")

if __name__ == "__main__":
    main()
