import io
import pandas as pd
from werkzeug.datastructures import FileStorage

from app import create_app, db
from app.importer import process_uploaded_files
from app.models import SKU


def dataframe_file(df, filename, kind="xlsx"):
    buffer = io.BytesIO()
    if kind == "csv":
        buffer.write(df.to_csv(index=False).encode("utf-8"))
    else:
        df.to_excel(buffer, index=False)
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=filename)


def run_tests():
    print("=== START TESTING SMART IMPOR ACCURATE ===")
    app = create_app()

    df_stok = pd.DataFrame([
        {"No. SKU": "TEST991", "Nama Item": "Kamera CCTV Smart HD", "Supplier": "IMPOR", "Saldo Akhir": 1200},
        {"No. SKU": "TEST992", "Nama Item": "Kabel HDMI 4K 3 Meter", "Supplier": "LOKAL", "Saldo Akhir": 500},
    ])
    df_po = pd.DataFrame([
        {"Item Code": "TEST991", "Qty PO Outstanding": 800},
        {"Item Code": "TEST992", "Qty PO Outstanding": 0},
    ])
    df_sales = pd.DataFrame([
        {"Kode": "TEST991", "SO Pending": 50, "Sales May": 1000, "Sales June": 1200, "Sales July": 1100, "Sales August": 500},
        {"Kode": "TEST992", "SO Pending": 10, "Sales May": 300, "Sales June": 400, "Sales July": 350, "Sales August": 150},
    ])

    with app.app_context():
        for kode in ["TEST991", "TEST992", "TESTNEG", "TESTCONFLICT"]:
            existing = db.session.get(SKU, kode)
            if existing:
                db.session.delete(existing)
        db.session.commit()

        result = process_uploaded_files([
            dataframe_file(df_stok, "stok.xlsx"),
            dataframe_file(df_po, "po.csv", "csv"),
            dataframe_file(df_sales, "sales.xlsx"),
        ])

        assert result["processed_files"] == 3
        assert result["total"] == 2
        assert result["errors"] == []
        assert result["warnings"] == []

        sku1 = db.session.get(SKU, "TEST991")
        assert sku1 is not None
        assert sku1.nama_barang == "Kamera CCTV Smart HD"
        assert sku1.supplier == "IMPOR"
        assert sku1.stok_gudang == 1200
        assert sku1.dipesan == 800
        assert sku1.dijual == 50
        assert sku1.penjualan_mei == 1000
        assert sku1.penjualan_agustus == 500

        # Nilai negatif tidak boleh diubah diam-diam menjadi nol.
        negative_df = pd.DataFrame([
            {"Kode Barang": "TESTNEG", "Nama Barang": "Negative Test", "Supplier": "LOKAL", "Stok Gudang": -10}
        ])
        negative_result = process_uploaded_files([dataframe_file(negative_df, "negative.xlsx")])
        assert negative_result["warnings"]
        negative_sku = db.session.get(SKU, "TESTNEG")
        assert negative_sku.stok_gudang == 0  # default field karena nilai invalid diabaikan

        # Konflik antar-file harus dilaporkan dan nilai pertama dipertahankan.
        first_df = pd.DataFrame([{"Kode Barang": "TESTCONFLICT", "Nama Barang": "Conflict", "Supplier": "LOKAL", "Stok Gudang": 100}])
        second_df = pd.DataFrame([{"Kode Barang": "TESTCONFLICT", "Stok Gudang": 200}])
        conflict_result = process_uploaded_files([
            dataframe_file(first_df, "first.xlsx"),
            dataframe_file(second_df, "second.xlsx"),
        ])
        assert any("Konflik SKU TESTCONFLICT" in w for w in conflict_result["warnings"])
        conflict_sku = db.session.get(SKU, "TESTCONFLICT")
        assert conflict_sku.stok_gudang == 100

        print("✓ Multi-file merge berhasil")
        print("✓ Nilai negatif menghasilkan warning")
        print("✓ Konflik antar-file terdeteksi dan tidak silent overwrite")

    print("=== ALL IMPORT TESTS PASSED ===")


if __name__ == "__main__":
    run_tests()
