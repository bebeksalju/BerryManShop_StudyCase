# Stock Coverage Analyzer

Web application MVP untuk membantu tim Purchasing mengurangi proses analisa stok manual dari laporan **Accurate ERP**. Fokus aplikasi adalah mengubah data stok, outstanding PO/SO, dan histori penjualan menjadi **stock coverage** serta prioritas tindakan: `Critical`, `Need Order`, `Sufficient`, atau `No Sales Data`.

## Problem yang Diselesaikan

Pada study case, Purchasing setiap pagi perlu mengambil beberapa laporan dari Accurate, memodifikasi/menggabungkannya di Excel, lalu melakukan analisa untuk mengetahui SKU mana yang membutuhkan perhatian.

Workflow aplikasi:

```text
Laporan Accurate
      ↓
Upload Multi-File
      ↓
Validasi Header & Nilai
      ↓
Merge berdasarkan SKU
      ↓
Hitung ADS & Stock Coverage
      ↓
Prioritas: Critical / Need Order / Sufficient
      ↓
Purchasing Action
```

## Requirement Mapping

| Requirement Study Case | Implementasi |
|---|---|
| Import/input data SKU | Smart multi-file import + CRUD SKU |
| Menyimpan data | SQLite + SQLAlchemy |
| Menghitung Stock Coverage | `app/calculator.py` |
| Menampilkan SKU berdasarkan kondisi stok | Priority-first dashboard |
| Filter/search SKU | Search kode/nama + filter supplier/status |
| Rekomendasi reorder sederhana | Rekomendasi otomatis berdasarkan coverage |

## Stack

- Backend: Python 3.11, Flask, SQLAlchemy, Pandas
- Database: SQLite
- Frontend: Jinja2, Bootstrap 5, Bootstrap Icons
- Deployment: Docker & Docker Compose

## Fitur Utama

1. **Smart Import Accurate**
   - `.xlsx`, `.xls`, `.csv`
   - multi-file upload
   - dynamic column aliases
   - merge berdasarkan SKU
   - warning untuk nilai negatif/invalid
   - conflict detection antar-file agar tidak silent overwrite

2. **Configurable Analysis Period**
   - default tetap mengikuti dataset study case: Agustus 2026, hari berjalan 15, 31 hari/bulan, 92 hari historis
   - parameter dapat diubah melalui `/settings` tanpa mengubah formula inti

3. **Priority Dashboard**
   - Critical → Need Order → Sufficient → No Sales Data
   - search/filter SKU
   - last import timestamp
   - jumlah file/SKU pada import terakhir
   - warning indicator
   - penjelasan "Kenapa status ini?" per SKU

4. **Export Excel**
   - hasil coverage
   - lead time
   - safety stock days
   - status dan rekomendasi

## Formula

Default dataset study case:

```text
Stok Dapat Dijual = Stok Gudang - Dijual

Proyeksi Bulan Berjalan
= (Penjualan Bulan Berjalan / Hari Berjalan) × Jumlah Hari Bulan

ADS
= (Penjualan 3 Bulan Historis + Proyeksi Bulan Berjalan) / Total Hari Analisis

Safety Stock Days
= Lead Time × 20%

Coverage Days
= (Stok Dapat Dijual + Dipesan) / ADS
```

Lead time sesuai study case:

```text
IMPOR = 80 hari
LOKAL = 15 hari
```

Status:

| Status | Kondisi | Action |
|---|---|---|
| Critical | Coverage < Lead Time | Segera reorder |
| Need Order | Lead Time ≤ Coverage < Lead Time + Safety | Review dan siapkan reorder |
| Sufficient | Coverage ≥ Lead Time + Safety | Stok masih mencukupi |
| No Sales Data | ADS = 0 | Evaluasi manual |

## Requirement vs Asumsi MVP

### Langsung dari study case

- stok gudang
- dipesan / outstanding PO
- dijual / outstanding SO
- histori penjualan 3 bulan + 1 bulan berjalan
- lead time impor 80 hari
- lead time lokal 15 hari
- safety stock 20%
- formula coverage dan status dasar

### Asumsi implementasi MVP

- `Safety Stock Days = Lead Time × 20%`. Study case menyebut safety stock 20%, tetapi basis persentasenya perlu dikonfirmasi dengan stakeholder sebelum production.
- default periode mengikuti contoh dataset Agustus dengan cut-off hari ke-15.
- file dengan field SKU yang sama dan nilai berbeda dianggap konflik; sistem mempertahankan nilai pertama dan memberikan warning. Aturan merge final perlu divalidasi terhadap struktur 3 laporan Accurate asli perusahaan.

## Menjalankan Aplikasi

```bash
docker compose up -d --build
```

Akses:

```text
Dashboard  : http://localhost:5000/
Import     : http://localhost:5000/import
Settings   : http://localhost:5000/settings
```

## Testing

```bash
# Multi-file import + validation/conflict
docker exec stock-coverage-analyzer python test_importer.py

# Dynamic column mapping
docker exec stock-coverage-analyzer python test_settings_importer.py

# Formula dan boundary status
docker exec stock-coverage-analyzer python test_calculator.py
```

## Production Improvement yang Sengaja Belum Masuk MVP

- validasi langsung terhadap format 3 export Accurate asli perusahaan
- ETA outstanding PO untuk mendeteksi projected stockout sebelum barang datang
- reorder quantity, MOQ, budget, supplier pack size
- authentication/role-based access
- integrasi langsung Accurate API

Fitur-fitur tersebut tidak ditambahkan ke MVP karena data/rule pendukungnya tidak tersedia pada study case dan sebaiknya divalidasi bersama user Purchasing terlebih dahulu.
