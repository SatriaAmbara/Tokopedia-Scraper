# Tokopedia Scraper (Flask + Playwright)

Aplikasi web sederhana berbasis Flask untuk melakukan scraping data toko dari Tokopedia berdasarkan kategori dan wilayah Kab/Kota di Provinsi Kalimantan Tengah.

Fitur

- Scraping toko berdasarkan kategori Tokopedia
- Filter berdasarkan Kab/Kota
- Ambil data:
  - Domain toko
  - Nama toko
  - Kota
  - Kecamatan
  - Tanggal buka
  - Total produk aktif
- Real-time update di web
- Export hasil ke Excel
- Start / Stop scraping

Teknologi

- Python (Flask)
- Playwright (Web Automation)
- Pandas (Data Processing)
- Bootstrap (Frontend UI)

## Instalasi

### 1. Install Dependency

pip install -r requirements.txt

### 2. Install Browser Playwright

playwright install

## Cara Menjalankan

python app.py

Buka di browser:
http://127.0.0.1:5000

## Cara Penggunaan

1. Pilih Kab/Kota
2. Tentukan Max Page
3. Klik Start
4. Tunggu data muncul
5. Klik Download untuk export Excel
6. Klik Stop untuk menghentikan scraping

## Catatan

- Scraping menggunakan browser automation
- Gunakan secara bijak agar tidak kena limit
