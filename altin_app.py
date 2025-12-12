
from flask import Flask, jsonify, render_template
import requests
import time
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

def safe_float(val, default=0.0):
    try:
        if val is None:
            return default
        if isinstance(val, str):
            v = val.strip().replace(",", ".")
            if v in {"", "-", "—", "–", "N/A", "na"}:
                return default
            return float(v)
        return float(val)
    except (TypeError, ValueError):
        return default

def fetch_json(url, headers, timeout=8):
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    # JSON değilse patlamasın
    try:
        return r.json()
    except ValueError:
        snippet = (r.text or "")[:200]
        raise RuntimeError(f"Upstream JSON değil. URL={url} snippet={snippet!r}")

# Basit cache: OzanDöviz’i yormaz, Render’da da stabil olur
_CACHE = {"ts": 0, "data": None}
CACHE_SECONDS = 30

@app.route("/api/gold")
def gold_prices():
    global _CACHE
    now = time.time()
    if _CACHE["data"] is not None and (now - _CACHE["ts"] < CACHE_SECONDS):
        return jsonify(_CACHE["data"])

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*"
    }

    try:
        main_url = "https://ozandoviz.com/mainpagedataredis.php"
        main_json = fetch_json(main_url, headers=headers, timeout=8)
        main_data = (main_json or {}).get("data", {}) or {}

        altin_info = main_data.get("ALTIN", {}) or {}
        ons_info = main_data.get("ONS", {}) or {}

        gram_alis = safe_float(altin_info.get("alis"))
        gram_satis = safe_float(altin_info.get("satis"))
        ons_alis = safe_float(ons_info.get("alis"))
        ons_satis = safe_float(ons_info.get("satis"))

        sarrafiye_url = "https://ozandoviz.com/sarrafiyehaspagedataredis.php"
        sar_json = fetch_json(sarrafiye_url, headers=headers, timeout=8)
        sar_data = (sar_json or {}).get("data", {}) or {}

        def temiz(ad):
            return (ad or "").replace("ALTIN", "").replace("Altın", "").strip()

        data = []

        data.append({"urun": temiz("Ons ( $ )"),
                     "alis": f"{ons_alis:,.2f}",
                     "satis": f"{ons_satis:,.2f}"})

        data.append({"urun": "Has Altın",
                     "alis": f"{gram_alis:,.2f}",
                     "satis": f"{gram_satis:,.2f}"})

        data.append({"urun": "Gram Altın (24 Ayar)",
                     "alis": f"{gram_alis * 0.995:,.2f}",
                     "satis": f"{gram_satis * 1.004 + 10:,.2f}"})

        def sar_item(key, fallback_name, satis_ek=0, alis_ek=0):
            item = sar_data.get(key, {}) or {}
            code = temiz(item.get("code", fallback_name))
            alis_katsayi = safe_float(item.get("alis"))
            satis_katsayi = safe_float(item.get("satis"))
            return {
                "urun": code or fallback_name,
                "alis": f"{(alis_katsayi * gram_alis) + alis_ek:,.2f}",
                "satis": f"{(satis_katsayi * gram_satis) + satis_ek:,.2f}",
            }

        data.append(sar_item("stl2",  "E. Çeyrek", satis_ek=10))
        data.append(sar_item("stl4",  "E. Yarım",  satis_ek=20))
        data.append(sar_item("stl6",  "E. Teklik", satis_ek=40))

        # Ata Lira: senin mantığını korudum (alış -50, satış +100)
        ata = sar_item("stl10", "E. Ata Lira", satis_ek=100, alis_ek=-50)
        data.append(ata)

        data.append({"urun": "22 Ayar Hurda Bilezik",
                     "alis": f"{gram_alis * 0.912 - 3:,.2f}",
                     "satis": f"{gram_satis * 0.912 + 10:,.2f}"})

        _CACHE = {"ts": now, "data": data}
        return jsonify(data)

    except requests.exceptions.RequestException as e:
        # Ağ/timeout/DNS/403 vb.
        print("OzanDoviz request error:", repr(e))
        return jsonify({"error": "Upstream bağlantı hatası", "detail": str(e)}), 502

    except Exception as e:
        # JSON değil / beklenmeyen format vb.
        print("Gold endpoint error:", repr(e))
        return jsonify({"error": "Upstream veri formatı hatası", "detail": str(e)}), 502





