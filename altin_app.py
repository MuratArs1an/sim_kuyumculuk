
from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route("/api/gold")
def gold_prices():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0 Safari/537.36"
        }

        # 1️⃣ Gram altın ve ons
        main_url = "https://ozandoviz.com/mainpagedataredis.php"
        main_res = requests.get(main_url, headers=headers, timeout=10)
        main_res.raise_for_status()
        main_data = main_res.json().get("data", {})

        altin_info = main_data.get("ALTIN", {})
        ons_info = main_data.get("ONS", {})

        gram_alis = float(altin_info.get("alis", 0))
        gram_satis = float(altin_info.get("satis", 0))
        ons_alis = float(ons_info.get("alis", 0))
        ons_satis = float(ons_info.get("satis", 0))

        # 2️⃣ Sarrafiye
        sarrafiye_url = "https://ozandoviz.com/sarrafiyehaspagedataredis.php"
        sarrafiye_res = requests.get(sarrafiye_url, headers=headers, timeout=10)
        sarrafiye_res.raise_for_status()
        sarrafiye_data = sarrafiye_res.json().get("data", {})

        def temiz(ad):
            # "ALTIN " veya "Altın " gibi önekleri temizle
            return ad.replace("ALTIN", "").replace("Altın", "").strip()

        data = []

        # ONS
        data.append({
            "urun": temiz("Ons ( $ )"),
            "alis": f"{ons_alis:,.2f}",
            "satis": f"{ons_satis:,.2f}"
        })

        # HAS
        data.append({
            "urun": "Has Altın",
            "alis": f"{gram_alis:,.2f}",
            "satis": f"{gram_satis:,.2f}"
        })

        # 24 Ayar
        data.append({
            "urun": "Gram Altın (24 Ayar)",
            "alis": f"{gram_alis * 0.995:,.2f}",
            "satis": f"{gram_satis * 1.004+10:,.2f}"
        })

        # E. Çeyrek
        e_ceyrek = sarrafiye_data.get("stl2", {})
        data.append({
            "urun": temiz(e_ceyrek.get("code", "E. Çeyrek")),
            "alis": f"{float(e_ceyrek.get('alis', 0)) * gram_alis:,.2f}",
            "satis": f"{float(e_ceyrek.get('satis', 0)) * gram_satis + 10:,.2f}"
        })

        # E. Yarım
        e_yarim = sarrafiye_data.get("stl4", {})
        data.append({
            "urun": temiz(e_yarim.get("code", "E. Yarım")),
            "alis": f"{float(e_yarim.get('alis', 0)) * gram_alis:,.2f}",
            "satis": f"{float(e_yarim.get('satis', 0)) * gram_satis + 20:,.2f}"
        })

        # E. Teklik
        e_teklik = sarrafiye_data.get("stl6", {})
        data.append({
            "urun": temiz(e_teklik.get("code", "E. Teklik")),
            "alis": f"{float(e_teklik.get('alis', 0)) * gram_alis:,.2f}",
            "satis": f"{float(e_teklik.get('satis', 0)) * gram_satis + 40:,.2f}"
        })

        # E. Ata Lira (+100 TL)
        e_ata = sarrafiye_data.get("stl10", {})
        data.append({
            "urun": temiz(e_ata.get("code", "E. Ata Lira")),
            "alis": f"{float(e_ata.get('alis', 0)) * gram_alis-50:,.2f}",
            "satis": f"{float(e_ata.get('satis', 0)) * gram_satis + 100:,.2f}"
        })

        # Hurda 22 Ayar (ALTIN * 0.912)
        data.append({
            "urun": "22 Ayar Hurda Bilezik",
            "alis": f"{gram_alis * 0.912-3:,.2f}",
            "satis": f"{gram_satis * 0.912+10:,.2f}"
        })

        return jsonify(data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Veri alınırken hata: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)



