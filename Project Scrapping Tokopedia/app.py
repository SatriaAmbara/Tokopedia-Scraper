from flask import Flask, render_template, request, jsonify, send_file
import threading
from scraper import run_scraper, stop_scraper
import pandas as pd
import io

app = Flask(__name__)

data_live = []
status_app = "stop"
selected_city_name = ""

KOTA_MAPPING = {
    "Kab. Kotawaringin Barat": 329,
    "Kab. Kotawaringin Timur": 330,
    "Kab. Kapuas": 327,
    "Kab. Barito Selatan": 323,
    "Kab. Barito Utara": 325,
    "Kab. Sukamara": 334,
    "Kab. Lamandau": 331,
    "Kab. Seruyan": 335,
    "Kab. Katingan": 328,
    "Kab. Pulang Pisau": 333,
    "Kab. Gunung Mas": 326,
    "Kab. Barito Timur": 324,
    "Kab. Murung Raya": 332,
    "Kota Palangkaraya": 336
}

# reverse mapping
KOTA_CODE_TO_NAME = {v: k.lower() for k, v in KOTA_MAPPING.items()}

# =============================
# FULL CATEGORY
# =============================
CATEGORIES = {
    "rumah-tangga": [
        "Dekorasi","Furniture","Kamar Mandi","Kamar Tidur","Kebersihan",
        "Kebutuhan Rumah","Laundry","Ruang Tamu Keluarga","Taman",
        "Tempat Penyimpanan","Travel"
    ],
    "buku": [
        "Buku Arsitektur Desain","Buku Ekonomi Bisnis","Buku Hobi",
        "Buku Hukum","Buku Import","Buku Kedokteran","Buku Keluarga",
        "Buku Kesehatan Gaya Hidup","Buku Kewanitaan","Buku Komputer Internet",
        "Buku Masakan","Buku Pendidikan","Buku Pengembangan Diri Karir",
        "Buku Persiapan Ujian","Buku Pertanian","Buku Religi Spiritual",
        "Buku Remaja Anak","Buku Sosial Politik","Buku Teknik Sains",
        "Kamus Bahasa Asing","Komik","Majalah","Novel Sastra"
    ],
    "dapur": [
        "Aksesoris Dapur","Alat Masak Khusus","Bekal",
        "Kemasan Makanan dan Minuman","Penyimpanan Makanan",
        "Peralatan Baking","Peralatan Dapur","Peralatan Makan Minum",
        "Peralatan Masak","Perlengkapan Cuci Piring"
    ],
    "elektronik": [
        "Alat Pendingin Ruangan","Elektronik Dapur","Elektronik Kantor",
        "Elektronik Rumah Tangga","TV Aksesoris","Telepon"
    ],
    "fashion-anak-bayi": [
        "Aksesoris Anak","Aksesoris Bayi","Baju Sepatu Bayi","Jam Tangan Anak", "Kostum Anak"
        "Pakaian Adat Anak","Pakaian Anak Laki Laki","Pakaian Anak Perempuan", "Pakaian Dalam Anak", "Perhiasan Anak",
        "Sepatu Anak Laki Laki", "Sepatu Anak Perempuan", "Seragam Sekolah", "Tas Anak"
    ],
    "fashion-muslim": [
        "Aksesoris Muslim","Atasan Muslim Wanita","Baju Renang Muslim","Bawahan Muslim Wanita", "Dress Muslim Wanita"
        "Jilbab","Masker Hijab","Outerwear Muslim Wanita", "Pakaian Muslim Anak", "Pakaian Muslim Pria",
        "Perlengkapan Ibadah"
    ],
    "fashion-pria": [
        "Aksesoris Pria","Aksesoris Sepatu Pria", "Atasan Pria", "Baju Tidur Pria", "Batik Pria", "Blazer Jas Pria", "Celana Pria",
        "Jam Tangan Pria", "Jeans Denim Pria", "Masker Pria", "Outwear Pria", "Pakaian Adat Pria", "Pakaian Dalam Pria", "Perhiasan Pria",
        "Perhiasan Pria", "Sepatu Pria", "Seragam Pria", "Tas Pria", "Topi Pria"
    ],
    "fashion-wanita": [
        "Aksesoris Sepatu Wania","Aksesoris Wanita","Atasan Wanita","Baju Tidur Wanita","Batik Wanita", "Bawahan Wanita", "Beachwear Wanita", "Bridal", "Dress",
        "Fashion Couple", "Jam Tangan Wanita", "Jeans Denim Wanita", "Kebaya", "Masker Wanita", "Outerwear Wanita", "Pakaian Adat Wanita", "Pakaian Dalam Wanita",
        "Pakaian Ibu Hamil", "Perhiasan Wanita", "Sepatu Wanita", "Seragam Wanita", "Setelan Wanita", "Tas Wanita"
    ],
    "film-musik": [
        "Alat Musik Digital","Alat Musik Gesek","Alat Musik Tiup", "Alat Musik Tradisional", "Drum Perkusi", "Film Serial TV", "Gitar Bass",
        "Keyboard Piano", "Merchandise", "Musik", "Perlengkapan Alat Musik", "Vokal"
    ],
    "gaming": [
        "Aksesoris Game Console", "Aksesoris Mobile Gaming", "CD Game", "Game Console", "Virtual Reality"
    ],
    "handphone-tablet": [
        "Aksesoris Handphone", "Aksesoris Tablet", "Handphone", "Komponen Handphone", "Komponen Tablet", "Nomor Perdana Voucher",
        "Power Bank", "Tablet", "Wearable Devices"
    ],
    "ibu-bayi": [
        "Aksesori Popok", "Aktivitas Bayi", "Makanan Susu Ibu Hamil", "Makanan Bayi", "Peralatan Perlengkapan Menyusui", "Perawatan Bayi", "Perlengkapan Perawatan Ibu",
        "Perlengkapan Makan Bayi", "Perlengkapan Mandi Bayi", "Perlengkapan Tidur Bayi", "Popok", "Stroller Alat Bantu Bawa Bayi", "Susu Bayi Anak", "Tempat Sampah Popok Isi Ulang" 
    ],
    "kecantikan": [
        "Aksesoris Rambut","Alat Kecantikan Wajah","Brush Applicator", "Eyebrow Kit", "Face Body Paint Kit", "Kesehatan Kulit", "Lip Color Lip Care",
        "Make up Mata", "Make up Tools", "Make up Wajah", "Makeup Tools", "Masker Kecantikan", "Mata dan Telinga", "Mix Palette", "Pembersih Make Up",
        "Perawatan Kuku Nail Art", "Perawatan Wajah", "Styling Rambut Wanita", "Suplemen Kecantikan Collagen"
    ],
    "kesehatan": [
        "Kesehatan Wanita","Masker Medis Pelindung Wajah", "Obat-Obatan", "Perlengkapan Kebersihan", "Perlengkapan Medis", "Produk Dewasa", "Suplemen Diet", "Tes Kehamilan dan Masa Subur", 
        "Tulang Otot Sendi", "Vitamin Suplemen"
    ],
    "komputer-laptop": [
        "Aksesoris Komputer Laptop", "Aksesoris PC Gaming", "Desktop Mini PC", "Kabel Adaptor", "Komponen Komputer","Komponen Laptop",
        "Laptop", "Media Penyimpanan Data", "Memory Card", "Monitor", "Networking", "PC Laptop Gaming", "Printer", "Proyektor Aksesoris", "Software"
    ],
    "mainan-hobi": [
        "Aksesoris Airsoft","Board Game", "Boneka", "Diescast", "Figure", "Gag Prank Toy", "Kostum", "Mainan Anak Anak", "Mainan Bayi", "Mainan Remote Control", "Model Kit",
        "Perlengkapan Sulap", "Permainan Kartu", "Permainan Tradisional", "Puzzle", "Stress Relieve Toys"
    ],
    "makanan-minuman": [
        "Bahan Kue", "Beras Shirataki dan Porang", "Buah", "Bumbu Bahan Masakan", "Daging", "Hampers Parsel dan Paket Makanan", "Kue", "Makanan Jadi", "Makanan Kering", "Makanan Ringan", ""
        "Makanan Sarapan", "Mie Pasta", "Minuman", "Produk Mengandung Babi", "Sayur", "Seafood", "Susu Olahan Susu", "Telur", "Tepung"
    ],
    "office-stationery": [
        "Alat Tulis", "Alat Ukir", "Buku Tulis", "Document Organizer", "Kalkulator Kamus Elektronik", "Kerajinan Tangan", "Kertas", "Kertas Seni", "Pemotong Kertas", "Pengikat Perekat", 
        "Peralatan Jahit", "Peralatan Melukis",
        "Peralatan Menggambar", "Perlengkapan Kaligrafi", "Surat Menyurat"
    ],
    "olahraga": [
        "Aksesoris Olahraga", "Alat Pancing", "Badminton", "Baseball", "Basket", "Beladiri", "Billiard", "Boxing", "Golf", "Gym Fitness", "Hiking Camping", "Olahraga Air", 
        "Pakaian Olahraga Pria", "Pakaian Olahraga Wanita",
        "Panahan", "Perlengkapan Lari", "Sepak Bola Futsal", "Sepatu Roda Skateboard", "Sepeda", "Tenis", "Tenis Meja", "Voli", "Yoga Pilates"
    ],
    "otomotif": [
        "Aksesoris Motor","Aksesoris Pengendara Motor","Alat Berat","Audio Video Mobil", "Ban Mobil", "Ban Motor", "Eksterior Mobil", "Helm Motor", "Interior Mobil", "Mobil", 
        "Mobil Bekas", "Oli Penghemat BBM",
        "Perawatan Kendaraan", "Perkakas Kendaraan", "Sepeda Motor", "Sepeda Motor Bekas", "Spare Part Mobil", "Spare Part Motor", "Velg Mobil", "Velg Motor"
    ],
    "perawatan-hewan": [
        "Grooming Hewan", "Hewan Peliharaan", "Perawatan Anjing", "Perawatan Ayam", "Perawatan Burung", "Perawatan Hamster", "Perawatan Hewan Ternak", "Perawatan Ikan", 
        "Perawatan Kelinci",
        "Perawatan Kucing", "Perawatan Reptil", "Perlengkapan Hewan"
    ],
    "perawatan-tubuh": [
        "Grooming", "Kesehatan Gigi Mulut", "Parfum Cologne Fragrance", "Perawatan Kaki Tangan", "Perawatan Kuku", "Perawatan Kulit", "Perawatan Mata", "Perawatan Rambut", 
        "Perawatan Telinga", "Perlengkapan Mandi", "Produk Kewanitaan"
    ],
    "perlengkapan-pesta": [
        "Balon", "Bunga", "Bungkus Kemasan", "Dekorasi Pesta", "Hadiah", "Kebutuhan Pesta", "Persiapan Pernikahan"
    ],
    "pertukangan": [
        "Alat Angkut Barang", "Alat Keselamatan", "Alat Perkebunan", "Alat Ukur Industri", "Baut Mur Pengencang", "Cat Perlengkapan", "Generator Genset", "Gerobak", 
        "Hand Tools", "Industrial Material", "Lampu", "Ledeng", "Machinery", "Material Bangunan", "Motors Power Transmission", "Otomasi Industrial", "Perangkat Keamanan", "Perlengkapan Las", "Perlengkapan Listrik", "Pneumatic"
    ],
    "properti": [
        "Booking Fee Properti", "Full Payment Properti", "Sewa Properti" 
    ],
    "tiket-travel-voucher": [
        "Dokumen Perjalanan", "Tur", "Sim Card Wifi Internasional", "Tiket Atraksi", "Tiket Transportasi", "Voucher Fisik" 
    ],
    "audio-kamera-elektronik-lainnya": [
        "Aksesoris Kamera","Audio","Frame Album Roll Film","Kamera Digital","Kamera Analog","Kamera Instan","Kamera Pengintai","Lensa Aksesoris","Media Player","Perangkat Elektronik Lainnya",
        "Audio","Lighting Studio","Video", "Remote Control Drone"
    ]
}


def update_data(data):
    global selected_city_name

    try:
        city_scrap = (data.get("city") or "").lower()

        if selected_city_name in city_scrap:
            data_live.append(data)
        else:
            print("SKIP:", data.get("shop_name"))

    except Exception as e:
        print("FILTER ERROR:", e)


def scraping_selesai():
    global status_app
    if status_app != "stop":
        status_app = "selesai"


@app.route("/")
def index():
    return render_template("index.html", kota=KOTA_MAPPING)


@app.route("/start", methods=["POST"])
def start():
    global data_live, status_app, selected_city_name

    data_live = []
    status_app = "sedang berjalan"

    body = request.json
    city = int(body.get("city"))
    max_page = int(body.get("max_page", 5))

    selected_city_name = KOTA_CODE_TO_NAME.get(city, "")
    print("FILTER KOTA:", selected_city_name)

    threading.Thread(
        target=run_scraper,
        args=(update_data, city, CATEGORIES, max_page, scraping_selesai),
        daemon=True
    ).start()

    return jsonify({"status": status_app})


@app.route("/stop")
def stop():
    global status_app
    stop_scraper()
    status_app = "stop"
    return jsonify({"status": status_app})


@app.route("/status")
def get_status():
    return jsonify({"status": status_app})


@app.route("/data")
def data():
    return jsonify(data_live)


@app.route("/download")
def download():
    if not data_live:
        return jsonify({"error": "no data"}), 400

    df = pd.DataFrame(data_live)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)

    return send_file(
        output,
        download_name="hasil_scraping.xlsx",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)