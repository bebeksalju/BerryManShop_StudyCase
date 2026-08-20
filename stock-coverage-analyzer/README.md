# Stock Coverage Analyzer

Web application MVP untuk membantu tim Purchasing memantau kondisi stok SKU, mengotomatiskan pengolahan data harian dari **Accurate ERP** (dengan **Pengaturan Pemetaan Kolom Fleksibel** & **Unlimited File Upload**), dan menentukan prioritas reorder secara instan.

---

## 🛠️ Stack & Teknologi

- **Backend**: Python 3.11 + Flask + Pandas
- **Database**: SQLite (persisten via Volume Docker)
- **Frontend**: HTML5 + Tailwind CSS + Lucide Icons
- **Deployment**: Docker & Docker Compose

---

## 📁 Struktur Folder Project

```text
stock-coverage-analyzer/
├── app/
│   ├── __init__.py           # Flask App Factory & database init
│   ├── calculator.py         # Formula metrik ADS, Safety Stock, Coverage & Status
│   ├── importer.py           # Smart Parser (Dynamic Column Mapping, Unlimited Multi-file merge)
│   ├── models.py             # Model SQLAlchemy SKU & ColumnMapping
│   ├── routes.py             # Route Dashboard, CRUD SKU, Smart Import, Settings & Export
│   ├── seed.py               # Auto-seeding data contoh & default column mappings
│   ├── static/
│   │   └── js/main.js        # Interaktivitas JS (modal hapus, auto filter, validasi number)
│   └── templates/
│       ├── base.html         # Layout utama + Navbar + Navigasi Settings
│       ├── form_sku.html     # Form Tambah & Edit Data SKU
│       ├── import.html       # UI Smart Upload Laporan Accurate (Drag & Drop)
│       ├── index.html        # Dashboard & Tabel Analisis Stock Coverage
│       └── settings.html     # UI Pengaturan Pemetaan Kolom Accurate
├── Dockerfile                # Konfigurasi containerization Python 3.11
├── docker-compose.yml        # Orchestration Docker service & volume SQLite
├── requirements.txt          # Dependensi Flask, Pandas, Openpyxl, dll.
├── run.py                    # Entry point aplikasi Flask
├── test_importer.py          # Script pengujian otomatis Smart Impor Multi-File
├── test_settings_importer.py# Script pengujian otomatis Dynamic Column Mapping
└── README.md                 # Dokumentasi proyek
```

---

## ✨ Fitur-Fitur Utama

1. **Pengaturan Pemetaan Kolom Accurate (`/settings`)**:
   - User/Purchasing dapat secara bebas menentukan nama header kolom file dari Accurate.
   - Contoh: Menentukan bahwa kolom `Kode Barang` di Accurate perusahaan Anda bernama `Kode Accurate`, `No_Induk_Barang`, atau `Item_Code`.
   - Kata kunci tersimpan di database SQLite (`column_mapping`), dilengkapi tombol **Reset ke Default**.
2. **Smart Impor Accurate (Unlimited Multi-File Upload)**:
   - Mendukung pengunggahan **file Excel/CSV dalam jumlah berapa pun (bebas berapa pun file)** sekaligus (`.xlsx`, `.xls`, `.csv`).
   - Engine parser akan membaca semua file, memetakan header berdasarkan pengaturan user, dan secara otomatis menggabungkan data berdasarkan `Kode SKU`.
3. **Dashboard Summary & Alerts**:
   - Indicator Card: Total SKU, Critical, Need Order, Sufficient, dan No Sales Data.
   - Peringatan Otomatis (Red Alert) jika ada barang berstatus `Critical`.
4. **Tabel Analisis Stock Coverage**:
   - Menampilkan Stok Gudang, Dipesan (PO), Dijual (SO), Stok Dapat Dijual, ADS, Coverage Days (2 desimal), Status & Rekomendasi.
   - Urutan Default: `Critical` → `Need Order` → `Sufficient` → `No Sales Data`.
5. **Ekspor Hasil Analisis ke Excel**:
   - Download hasil kalkulasi coverage terbaru ke file `.xlsx` untuk laporan Manajemen.
6. **Manajemen Data SKU (CRUD)**:
   - Tambah, Edit, dan Hapus SKU dengan konfirmasi modal.

---

## 📐 Formula & Metrik Perhitungan

| Metrik | Formula | Keterangan |
|---|---|---|
| **Stok Dapat Dijual** | `Stok Gudang − Dijual` | Stok fisik bebas alokasi |
| **Proyeksi Agustus** | `(Penjualan Agustus ÷ 15) × 31` | Asumsi 15 hari berjalan dari 31 hari |
| **ADS (Average Daily Sales)** | `(Mei + Juni + Juli + Proyeksi Agustus) ÷ 123` | Total 123 hari (31+30+31+31) |
| **Safety Stock Days** | `Lead Time × 20%` | IMPOR = 80 hari, LOKAL = 15 hari |
| **Coverage Days** | `(Stok Dapat Dijual + Dipesan) ÷ ADS` | Ditampilkan dalam 2 angka desimal |

### Ketentuan Status & Rekomendasi

| Status | Kondisi | Rekomendasi | Badge |
|---|---|---|---|
| 🔴 **Critical** | `Coverage Days < Lead Time` | Segera lakukan reorder | Merah |
| 🟡 **Need Order** | `Lead Time ≤ Coverage Days < Lead Time + Safety Stock` | Disarankan melakukan reorder | Kuning |
| 🟢 **Sufficient** | `Coverage Days ≥ Lead Time + Safety Stock` | Stok masih mencukupi | Hijau |
| ⚫ **No Sales Data** | `ADS = 0` | Tidak ada data penjualan, evaluasi manual | Abu-abu |

---

## 🚀 Cara Menjalankan (Docker Compose)

### 1. Build & Jalankan Container
```bash
docker compose up -d --build
```

### 2. Cek Status Container
```bash
docker compose ps
```

### 3. Jalankan Pengujian Otomatis
```bash
# Pengujian Impor Multi-File
docker exec stock-coverage-analyzer python test_importer.py

# Pengujian Dynamic Column Mapping Settings
docker exec stock-coverage-analyzer python test_settings_importer.py
```

---

## 🌐 Akses Aplikasi

Buka browser: **[http://localhost:5000](http://localhost:5000)**
- **Dashboard**: `http://localhost:5000/`
- **Smart Impor**: `http://localhost:5000/import`
- **Pengaturan Kolom**: `http://localhost:5000/settings`
