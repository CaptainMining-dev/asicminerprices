#!/usr/bin/env python3
"""Fetch live network data (100% free, no API key) and compute per-algo hashprice.
Sources:
  BTC  — mempool.space  (hashrate, difficulty, USD price)
  KAS  — kas.2miners.com public pool stats (network hashrate, live block reward, block time)
  LTC/DOGE — api.blockchair.com (difficulty, blocks/24h)  [merged-mined together]
  Prices — CoinGecko (KAS, LTC, DOGE)
Output: data.json consumed by build.py. On any failure, build.py keeps its snapshot constants.
"""
import json, os, sys, time, urllib.request, datetime

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

    print("blockchair (LTC, DOGE)…")
    ltc = get("https://api.blockchair.com/litecoin/stats")["data"]
    doge = get("https://api.blockchair.com/dogecoin/stats")["data"]
    LTC_REWARD, LTC_BT = 6.25, 150.0      # next halving ~Aug 2027
    DOGE_REWARD, DOGE_BT = 10000.0, 60.0  # fixed reward
    ltc_nethash_h = nethash_from_diff(ltc["difficulty"], LTC_BT)
    doge_nethash_h = nethash_from_diff(doge["difficulty"], DOGE_BT)
    ltc_blocks_day = float(ltc["blocks_24h"])
    doge_blocks_day = float(doge["blocks_24h"])

    print("CoinGecko (prices)…")
    ids = "kaspa,litecoin,dogecoin" + (",bitcoin" if btc_usd is None else "")
    prices = get(f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd")
    if btc_usd is None:
        btc_usd = float(prices["bitcoin"]["usd"])
    kas_usd = float(prices["kaspa"]["usd"])
    ltc_usd = float(prices["litecoin"]["usd"])
    doge_usd = float(prices["dogecoin"]["usd"])

    # ---- hashprice = $ revenue per hashrate unit per day ----
    BTC_REWARD, BTC_BLOCKS_DAY = 3.125, 144.0   # next halving ~2028
    hp_sha256 = BTC_BLOCKS_DAY * BTC_REWARD * btc_usd / (btc_nethash_h / TH)

    kas_coins_day = (86400.0 / kas_block_time) * kas_reward
    hp_kas = kas_coins_day * kas_usd / (kas_nethash_h / TH)

    ltc_per_gh = ltc_blocks_day * LTC_REWARD / (ltc_nethash_h / GH)
    doge_per_gh = doge_blocks_day * DOGE_REWARD / (doge_nethash_h / GH)
    hp_scrypt = ltc_per_gh * ltc_usd + doge_per_gh * doge_usd   # merged mining

    now = datetime.datetime.utcnow()
    out = {
        "source": "live: mempool.space + 2miners + blockchair + coingecko",
        "fetched_at": now.isoformat(timespec="seconds") + "Z",
        "updated_human": now.strftime("%B %d, %Y"),
        "btc_usd": round(btc_usd),
        "prices": {"BTC": round(btc_usd), "KAS": round(kas_usd, 6),
                   "LTC": round(ltc_usd, 2), "DOGE": round(doge_usd, 5)},
        "hashprice": {"SHA-256": round(hp_sha256, 5),
                      "kHeavyHash": round(hp_kas, 5),
                      "Scrypt": round(hp_scrypt, 4)},
        "networks": {
            "BTC": {"nethash_eh": round(btc_nethash_h / 1e18, 1), "block_reward": BTC_REWARD},
            "KAS": {"nethash_ph": round(kas_nethash_h / 1e15, 1), "block_reward": round(kas_reward, 4)},
            "LTC": {"nethash_ph": round(ltc_nethash_h / 1e15, 2), "block_reward": LTC_REWARD},
            "DOGE": {"nethash_ph": round(doge_nethash_h / 1e15, 2), "block_reward": DOGE_REWARD},
        },
    }
    with open(os.path.join(ROOT, "data.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print("OK → data.json")

if __name__ == "__main__":
    main()
