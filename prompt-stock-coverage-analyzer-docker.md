# Prompt — Stock Coverage Analyzer MVP (Estimasi 4–5 Jam)

Buatkan web application MVP bernama **Stock Coverage Analyzer** untuk membantu tim Purchasing mengetahui kondisi stok tiap SKU dan menentukan SKU yang perlu segera di-reorder.

Konteksnya: Purchasing saat ini mengolah data stok dan penjualan secara manual di Excel. Aplikasi ini adalah versi awal yang fokus pada analisis stock coverage dan demo alur kerja, bukan sistem ERP lengkap.

## Batasan waktu dan prioritas

Pengerjaan dibatasi **4–5 jam**. Prioritaskan aplikasi yang fungsional, rapi, dan siap didemokan. Jangan menghabiskan waktu pada fitur enterprise seperti login, multi-role user, audit log, import Excel kompleks, chart rumit, Nginx, atau deployment production yang berlebihan.

## Stack

- Backend: Python + Flask
- Database: SQLite dengan volume Docker persisten
- Frontend: Bootstrap 5
- Deployment: Docker + Docker Compose

Gunakan struktur project sederhana tetapi rapi: route, model/database, helper atau service perhitungan, template, static assets, dan konfigurasi environment.

## Data SKU

Setiap SKU memuat:

- Kode Barang / SKU (unik)
- Nama Barang
- Tipe Supplier: `IMPOR` atau `LOKAL`
- Stok Gudang
- Dipesan: barang yang sudah dipesan ke supplier dan masih dalam perjalanan
- Dijual: barang yang sudah dipesan customer tetapi belum diproses/dikirim
- Penjualan Mei
- Penjualan Juni
- Penjualan Juli
- Penjualan Agustus / bulan berjalan

Pastikan data angka tidak boleh negatif dan SKU tidak boleh duplikat.

## Aturan perhitungan

Gunakan asumsi awal berikut agar dapat langsung didemokan:

- Hari berjalan Agustus: `15 hari`
- Jumlah hari Agustus: `31 hari`
- Lead time IMPOR: `80 hari`
- Lead time LOKAL: `15 hari`
- Safety stock: `20% dari lead time`

1. **Stok Dapat Dijual**

```text
Stok Dapat Dijual = Stok Gudang - Dijual
```

2. **Proyeksi Penjualan Bulan Berjalan**

```text
Proyeksi Penjualan = (Penjualan Bulan Berjalan / Hari Berjalan) × Jumlah Hari Bulan
```

3. **Average Daily Sales (ADS)**

```text
ADS = (Penjualan Mei + Juni + Juli + Proyeksi Penjualan Bulan Berjalan) / 123
```

Angka 123 berasal dari 31 hari Mei + 30 hari Juni + 31 hari Juli + 31 hari Agustus.

4. **Safety Stock Days**

```text
Safety Stock Days = Lead Time × 20%
```

5. **Stock Coverage Days**

```text
Stock Coverage Days = (Stok Dapat Dijual + Dipesan) / ADS
```

Jika ADS = 0, tampilkan coverage sebagai `N/A` dan jangan lakukan pembagian.

## Status dan rekomendasi

| Kondisi | Status | Rekomendasi |
|---|---|---|
| ADS = 0 | No Sales Data | Tidak ada data penjualan, perlu evaluasi manual |
| Coverage < Lead Time | Critical | Segera lakukan reorder |
| Coverage ≥ Lead Time dan < Lead Time + Safety Stock Days | Need Order | Disarankan melakukan reorder |
| Coverage ≥ Lead Time + Safety Stock Days | Sufficient | Stok masih mencukupi |

Gunakan badge: merah untuk `Critical`, kuning/oranye untuk `Need Order`, hijau untuk `Sufficient`, dan abu-abu untuk `No Sales Data`.

## Fitur wajib dalam MVP

1. **Dashboard sederhana**
   - Total SKU.
   - Jumlah SKU Critical.
   - Jumlah SKU Need Order.
   - Jumlah SKU Sufficient.
   - Jumlah SKU No Sales Data.

2. **Tabel analisis stock coverage**
   - Tampilkan SKU, nama barang, supplier, stok gudang, dipesan, dijual, stok dapat dijual, ADS, coverage days, status, dan rekomendasi.
   - Urutkan default: Critical → Need Order → Sufficient → No Sales Data.
   - Format angka memakai pemisah ribuan dan coverage maksimal dua angka desimal.

3. **Pencarian dan filter sederhana**
   - Cari berdasarkan kode atau nama barang.
   - Filter berdasarkan supplier.
   - Filter berdasarkan status.

4. **Manajemen data SKU**
   - Tambah SKU.
   - Edit SKU.
   - Hapus SKU dengan konfirmasi.
   - Data tersimpan di SQLite.

5. **Seed data**
   - Aplikasi harus otomatis memiliki data contoh ketika pertama kali dijalankan.

## Seed data untuk demo

| Kode Barang | Nama Barang | Supplier | Stok Gudang | Dipesan | Dijual | Mei | Juni | Juli | Agustus |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 100118 | Tempat Rak Bumbu Dapur 6IN1 | IMPOR | 2400 | 0 | 26 | 3953 | 3636 | 3329 | 1273 |
| 100155 | Senter Tangan SOLAR V-5020 | LOKAL | 1844 | 0 | 0 | 997 | 960 | 909 | 288 |
| 100169 | Headset / Handsfree Hi-fi Branded | LOKAL | 1531 | 0 | 243 | 5325 | 7011 | 7041 | 3097 |
| 100173 | Smart Watch Y1 Support SIM Card & Memory Card | IMPOR | 3915 | 0 | 0 | 3590 | 5539 | 6297 | 2839 |
| 100174 | Tripod GMC 01 + Universal Holder for smartphones | LOKAL | 679 | 6402 | 0 | 2503 | 2527 | 2208 | 930 |

## Docker

Sediakan kebutuhan deployment Docker yang sederhana:

```text
Dockerfile
docker-compose.yml
.dockerignore
requirements.txt
README.md
```

Ketentuan:

- Cukup gunakan satu service aplikasi Flask.
- Gunakan volume Docker agar file database SQLite tidak hilang saat container di-restart.
- Gunakan environment variable `PORT` dengan default `5000`.
- Aplikasi harus dapat dijalankan dengan:

```bash
docker compose up -d --build
```

- Aplikasi dapat diakses melalui `http://localhost:5000` secara default.
- README harus menjelaskan cara build, menjalankan, menghentikan, dan melihat log container.

## Tidak perlu dikerjakan pada MVP ini

- Login dan manajemen role user.
- Import/export Excel.
- PostgreSQL, Nginx, Gunicorn, SSL, dan reverse proxy.
- Konfigurasi lead time dan safety stock melalui halaman khusus.
- Chart kompleks, notifikasi otomatis, audit log, atau automated test suite lengkap.

## Output yang harus diberikan

1. Struktur folder project.
2. Daftar fitur yang sudah selesai.
3. Penjelasan singkat formula yang dipakai.
4. Cara menjalankan aplikasi menggunakan Docker:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

Pastikan hasil akhir adalah aplikasi MVP yang berfungsi, mudah dipresentasikan, dan realistis selesai dalam 4–5 jam.
