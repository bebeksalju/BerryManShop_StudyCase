import io
import re
import pandas as pd
from .models import SKU, ColumnMapping
from . import db


def get_current_field_aliases() -> dict:
    """Mengambil dict alias {canonical_field: [alias1, alias2, ...]} dari DB ColumnMapping."""
    field_aliases = {}
    try:
        mappings = ColumnMapping.query.all()
        for m in mappings:
            field_aliases[m.target_field] = m.get_alias_list()
    except Exception:
        pass

    # Jika database belum berisi mapping, gunakan default bawaan
    if not field_aliases or "kode_barang" not in field_aliases:
        from .seed import DEFAULT_MAPPINGS
        for m in DEFAULT_MAPPINGS:
            tf = m["target_field"]
            alias_str = m["aliases"]
            field_aliases[tf] = [a.strip().lower() for a in alias_str.split(",") if a.strip()]

    return field_aliases


def _clean_header(header_str: str) -> str:
    """Membersihkan string header: lowercase, strip, ganti karakter khusus."""
    if not isinstance(header_str, str):
        header_str = str(header_str)
    cleaned = header_str.lower().strip()
    cleaned = re.sub(r'[\s\-_]+', ' ', cleaned)
    return cleaned


def match_columns(df_columns: list) -> dict:
    """
    Memetakan nama kolom di DataFrame ke field internal aplikasi berdasarkan konfigurasi user di DB.
    Mengembalikan dict: {canonical_field: df_column_name}
    """
    mapped = {}
    cleaned_headers = {col: _clean_header(col) for col in df_columns}
    current_aliases = get_current_field_aliases()

    for canonical, aliases in current_aliases.items():
        for col, cleaned_h in cleaned_headers.items():
            if col in mapped.values():
                continue  # Kolom sudah terpakai
            # Cek exact match atau substring match dengan alias
            for alias in aliases:
                cleaned_alias = _clean_header(alias)
                if cleaned_alias and (cleaned_alias == cleaned_h or cleaned_alias in cleaned_h):
                    mapped[canonical] = col
                    break
            if canonical in mapped:
                break
    return mapped




def read_file_to_df(file_storage_or_path):
    """Membaca file .xlsx, .xls, atau .csv menjadi pandas DataFrame."""
    filename = getattr(file_storage_or_path, 'filename', str(file_storage_or_path)).lower()
    
    if filename.endswith('.csv'):
        return pd.read_csv(file_storage_or_path)
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(file_storage_or_path)
    else:
        raise ValueError(f"Format file tidak didukung: {filename}. Gunakan .xlsx, .xls, atau .csv")


def process_uploaded_files(file_list) -> dict:
    """
    Memproses satu atau beberapa file laporan dari Accurate.
    Menggabungkan data berdasarkan Kode Barang dan meng-upsert ke SQLite DB.
    """
    errors = []
    created_count = 0
    updated_count = 0
    sku_data_map = {}  # {kode_barang: dict_of_fields}

    for file_obj in file_list:
        if not file_obj or not getattr(file_obj, 'filename', ''):
            continue

        try:
            df = read_file_to_df(file_obj)
            if df.empty:
                continue

            col_map = match_columns(df.columns.tolist())

            if "kode_barang" not in col_map:
                errors.append(f"File '{file_obj.filename}' tidak memiliki kolom 'Kode Barang / SKU' yang dapat dikenali.")
                continue

            for _, row in df.iterrows():
                raw_kode = row[col_map["kode_barang"]]
                if pd.isna(raw_kode) or not str(raw_kode).strip():
                    continue

                kode = str(raw_kode).strip()
                # Jika SKU sudah ada di dict penggabungan sementara
                if kode not in sku_data_map:
                    sku_data_map[kode] = {}

                item_dict = sku_data_map[kode]

                # Petakan field yang ditemukan di file ini
                for field in [
                    "nama_barang", "supplier", "stok_gudang", "dipesan", "dijual",
                    "penjualan_mei", "penjualan_juni", "penjualan_juli", "penjualan_agustus"
                ]:
                    if field in col_map and not pd.isna(row[col_map[field]]):
                        val = row[col_map[field]]
                        if field == "supplier":
                            sup_str = str(val).upper().strip()
                            item_dict[field] = "IMPOR" if "IMPOR" in sup_str or "IMPORT" in sup_str else "LOKAL"
                        elif field == "nama_barang":
                            item_dict[field] = str(val).strip()
                        else:
                            try:
                                item_dict[field] = max(0, int(float(val)))
                            except (ValueError, TypeError):
                                item_dict[field] = 0

        except Exception as e:
            errors.append(f"Gagal memproses file '{getattr(file_obj, 'filename', 'unknown')}': {str(e)}")

    if not sku_data_map:
        return {
            "created": 0,
            "updated": 0,
            "total": 0,
            "errors": errors if errors else ["Tidak ada data SKU valid yang ditemukan dalam file."]
        }

    # Upsert data ke Database SQLite
    for kode, data in sku_data_map.items():
        existing_sku = SKU.query.get(kode)
        if existing_sku:
            if "nama_barang" in data: existing_sku.nama_barang = data["nama_barang"]
            if "supplier" in data: existing_sku.supplier = data["supplier"]
            if "stok_gudang" in data: existing_sku.stok_gudang = data["stok_gudang"]
            if "dipesan" in data: existing_sku.dipesan = data["dipesan"]
            if "dijual" in data: existing_sku.dijual = data["dijual"]
            if "penjualan_mei" in data: existing_sku.penjualan_mei = data["penjualan_mei"]
            if "penjualan_juni" in data: existing_sku.penjualan_juni = data["penjualan_juni"]
            if "penjualan_juli" in data: existing_sku.penjualan_juli = data["penjualan_juli"]
            if "penjualan_agustus" in data: existing_sku.penjualan_agustus = data["penjualan_agustus"]
            updated_count += 1
        else:
            new_sku = SKU(
                kode_barang=kode,
                nama_barang=data.get("nama_barang", f"Barang {kode}"),
                supplier=data.get("supplier", "LOKAL"),
                stok_gudang=data.get("stok_gudang", 0),
                dipesan=data.get("dipesan", 0),
                dijual=data.get("dijual", 0),
                penjualan_mei=data.get("penjualan_mei", 0),
                penjualan_juni=data.get("penjualan_juni", 0),
                penjualan_juli=data.get("penjualan_juli", 0),
                penjualan_agustus=data.get("penjualan_agustus", 0),
            )
            db.session.add(new_sku)
            created_count += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append(f"Gagal menyimpan ke database: {str(e)}")

    return {
        "created": created_count,
        "updated": updated_count,
        "total": len(sku_data_map),
        "errors": errors
    }


def generate_excel_template() -> io.BytesIO:
    """Membuat template file Excel (.xlsx) contoh untuk dikirimkan ke user."""
    sample_data = [
        {
            "Kode Barang": "100118",
            "Nama Barang": "Tempat Rak Bumbu Dapur 6IN1",
            "Supplier": "IMPOR",
            "Stok Gudang": 2400,
            "Dipesan (PO)": 0,
            "Dijual (SO)": 26,
            "Penjualan Mei": 3953,
            "Penjualan Juni": 3636,
            "Penjualan Juli": 3329,
            "Penjualan Agustus": 1273,
        },
        {
            "Kode Barang": "100155",
            "Nama Barang": "Senter Tangan SOLAR V-5020",
            "Supplier": "LOKAL",
            "Stok Gudang": 1844,
            "Dipesan (PO)": 0,
            "Dijual (SO)": 0,
            "Penjualan Mei": 997,
            "Penjualan Juni": 960,
            "Penjualan Juli": 909,
            "Penjualan Agustus": 288,
        }
    ]
    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Master Stock Accurate")
    output.seek(0)
    return output


def export_analysis_to_excel(rows: list) -> io.BytesIO:
    """Mengekspor daftar hasil analisis stock coverage ke file Excel .xlsx."""
    export_data = []
    for r in rows:
        coverage_str = "N/A" if r["coverage_days"] is None else round(r["coverage_days"], 2)
        ads_val = round(r["ads"], 2) if r["ads"] > 0 else 0
        export_data.append({
            "Kode Barang": r["kode_barang"],
            "Nama Barang": r["nama_barang"],
            "Supplier": r["supplier"],
            "Stok Gudang": r["stok_gudang"],
            "Dipesan (PO)": r["dipesan"],
            "Dijual (SO)": r["dijual"],
            "Stok Dapat Dijual": r["stok_dapat_dijual"],
            "ADS (Harian)": ads_val,
            "Coverage Days": coverage_str,
            "Status": r["status"],
            "Rekomendasi": r["rekomendasi"],
        })

    df = pd.DataFrame(export_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Hasil Analisis Coverage")
    output.seek(0)
    return output
