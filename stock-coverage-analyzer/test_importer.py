import os
import pandas as pd
from app import create_app, db
from app.importer import process_uploaded_files
from app.models import SKU

def run_tests():
    print("=== START TESTING SMART IMPOR ACCURATE ===")
    
    app = create_app()

    # 1. Buat Dummy File 1: Laporan Stok Gudang Accurate (.xlsx) dengan header "No. SKU", "Nama Item", "Saldo Akhir"
    df_stok = pd.DataFrame([
        {"No. SKU": "TEST991", "Nama Item": "Kamera CCTV Smart HD", "Supplier": "IMPOR", "Saldo Akhir": 1200},
        {"No. SKU": "TEST992", "Nama Item": "Kabel HDMI 4K 3 Meter", "Supplier": "LOKAL", "Saldo Akhir": 500},
    ])
    stok_file_path = "test_stok_accurate.xlsx"
    df_stok.to_excel(stok_file_path, index=False)

    # 2. Buat Dummy File 2: Laporan PO Dalam Perjalanan Accurate (.csv) dengan header "Item Code", "Qty PO Outstanding"
    df_po = pd.DataFrame([
        {"Item Code": "TEST991", "Qty PO Outstanding": 800},
        {"Item Code": "TEST992", "Qty PO Outstanding": 0},
    ])
    po_file_path = "test_po_accurate.csv"
    df_po.to_csv(po_file_path, index=False)

    # 3. Buat Dummy File 3: Laporan Penjualan Accurate (.xlsx) dengan header "Kode", "SO Pending", "Sales May", "Sales June", "Sales July", "Sales August"
    df_sales = pd.DataFrame([
        {"Kode": "TEST991", "SO Pending": 50, "Sales May": 1000, "Sales June": 1200, "Sales July": 1100, "Sales August": 500},
        {"Kode": "TEST992", "SO Pending": 10, "Sales May": 300, "Sales June": 400, "Sales July": 350, "Sales August": 150},
    ])
    sales_file_path = "test_sales_accurate.xlsx"
    df_sales.to_excel(sales_file_path, index=False)

    with app.app_context():
        # Buka file dalam mode binary
        with open(stok_file_path, "rb") as f1, open(po_file_path, "rb") as f2, open(sales_file_path, "rb") as f3:
            f1.filename = stok_file_path
            f2.filename = po_file_path
            f3.filename = sales_file_path

            result = process_uploaded_files([f1, f2, f3])
            print("Hasil Impor Smart Parser:", result)

            assert result["total"] == 2, "Harus memproses 2 SKU"
            assert len(result["errors"]) == 0, f"Harus tidak ada error: {result['errors']}"

            # Verifikasi di DB SQLite
            sku1 = SKU.query.get("TEST991")
            assert sku1 is not None, "SKU TEST991 harus tersimpan di DB"
            assert sku1.nama_barang == "Kamera CCTV Smart HD"
            assert sku1.supplier == "IMPOR"
            assert sku1.stok_gudang == 1200
            assert sku1.dipesan == 800
            assert sku1.dijual == 50
            assert sku1.penjualan_mei == 1000
            assert sku1.penjualan_agustus == 500

            print("✓ SAKSI KUNCI: SKU TEST991 berhasil digabung dari 3 file terpisah secara sempurna!")

    # Cleanup file dummy
    for p in [stok_file_path, po_file_path, sales_file_path]:
        if os.path.exists(p):
            os.remove(p)

    print("=== ALL IMPOR TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
