import os
import pandas as pd
from app import create_app, db
from app.models import SKU, ColumnMapping
from app.seed import seed_default_mappings
from app.importer import process_uploaded_files

def run_tests():
    print("=== START TESTING DYNAMIC COLUMN MAPPING SETTINGS ===")

    app = create_app()

    with app.app_context():
        # 1. Seed default mappings
        seed_default_mappings(force_reset=True)

        # 2. Tambahkan alias khusus yang di-input user (simulasi via UI /settings)
        # Misal user menambahkan alias "no_induk_barang" untuk Kode Barang, dan "stok_fisik_gudang_utama" untuk Stok Gudang
        m_kode = ColumnMapping.query.filter_by(target_field="kode_barang").first()
        m_kode.aliases += ", no_induk_barang"

        m_stok = ColumnMapping.query.filter_by(target_field="stok_gudang").first()
        m_stok.aliases += ", stok_fisik_gudang_utama"

        db.session.commit()

        # 3. Buat file dummy Excel dengan header custom pengguna
        df_custom = pd.DataFrame([
            {"no_induk_barang": "CUSTOM888", "Nama Barang": "Lampu LED Sorot 50W", "Supplier": "IMPOR", "stok_fisik_gudang_utama": 3500},
        ])
        file_path = "test_custom_alias.xlsx"
        df_custom.to_excel(file_path, index=False)

        with open(file_path, "rb") as f:
            f.filename = file_path
            result = process_uploaded_files([f])
            print("Hasil Process Upload dengan Dynamic Custom Aliases:", result)

            assert result["total"] == 1, "Harus memproses 1 SKU custom"
            assert len(result["errors"]) == 0, f"Error: {result['errors']}"

            sku = SKU.query.get("CUSTOM888")
            assert sku is not None, "SKU CUSTOM888 harus berhasil masuk ke database"
            assert sku.nama_barang == "Lampu LED Sorot 50W"
            assert sku.stok_gudang == 3500

            print("✓ SUCCESS: Custom Alias 'no_induk_barang' & 'stok_fisik_gudang_utama' berhasil dikenali secara dinamis dari DB!")

        # Cleanup file dummy
        if os.path.exists(file_path):
            os.remove(file_path)

    print("=== ALL DYNAMIC SETTINGS TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
