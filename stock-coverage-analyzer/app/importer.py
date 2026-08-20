import io
import re
import pandas as pd
from .models import SKU, ColumnMapping
from . import db


NUMERIC_FIELDS = {
    "stok_gudang", "dipesan", "dijual",
    "penjualan_mei", "penjualan_juni", "penjualan_juli", "penjualan_agustus"
}


def get_current_field_aliases() -> dict:
    """Mengambil dict alias {canonical_field: [alias1, alias2, ...]} dari DB ColumnMapping."""
    field_aliases = {}
    try:
        mappings = ColumnMapping.query.all()
        for m in mappings:
            field_aliases[m.target_field] = m.get_alias_list()
    except Exception:
        pass

    if not field_aliases or "kode_barang" not in field_aliases:
        from .seed import DEFAULT_MAPPINGS
        for m in DEFAULT_MAPPINGS:
            tf = m["target_field"]
            alias_str = m["aliases"]
            field_aliases[tf] = [a.strip().lower() for a in alias_str.split(",") if a.strip()]

    return field_aliases


def _clean_header(header_str: str) -> str:
    if not isinstance(header_str, str):
        header_str = str(header_str)
    cleaned = header_str.lower().strip()
    return re.sub(r'[\s\-_]+', ' ', cleaned)


def match_columns(df_columns: list) -> dict:
    """Petakan header file Accurate ke field internal berdasarkan alias aktif."""
    mapped = {}
    cleaned_headers = {col: _clean_header(col) for col in df_columns}
    current_aliases = get_current_field_aliases()

    for canonical, aliases in current_aliases.items():
        for col, cleaned_h in cleaned_headers.items():
            if col in mapped.values():
                continue
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
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(file_storage_or_path)
    raise ValueError(f"Format file tidak didukung: {filename}. Gunakan .xlsx, .xls, atau .csv")


def _parse_numeric(value, kode, field, filename, warnings):
    """Parse angka tanpa menyembunyikan anomali data menjadi nol."""
    try:
        parsed = int(float(value))
    except (ValueError, TypeError):
        warnings.append(
            f"SKU {kode} pada '{filename}': nilai '{field}' tidak valid ({value!r}); field diabaikan."
        )
        return None

    if parsed < 0:
        warnings.append(
            f"SKU {kode} pada '{filename}': nilai '{field}' negatif ({parsed}); field diabaikan untuk mencegah koreksi data diam-diam."
        )
        return None
    return parsed


def _set_merged_value(sku_data_map, source_map, kode, field, value, filename, warnings):
    """Merge field per SKU. Konflik beda nilai dilaporkan dan nilai pertama dipertahankan."""
    if kode not in sku_data_map:
        sku_data_map[kode] = {}
        source_map[kode] = {}

    item = sku_data_map[kode]
    sources = source_map[kode]

    if field in item and item[field] != value:
        previous_source = sources.get(field, "file sebelumnya")
        warnings.append(
            f"Konflik SKU {kode}, field '{field}': {item[field]!r} dari '{previous_source}' vs {value!r} dari '{filename}'. Nilai pertama dipertahankan."
        )
        return

    item[field] = value
    sources[field] = filename


def process_uploaded_files(file_list) -> dict:
    """
    Proses multi-file Accurate, validasi, merge berdasarkan SKU, lalu upsert ke SQLite.
    Return juga warnings agar Purchasing dapat menilai kualitas data import.
    """
    errors = []
    warnings = []
    created_count = 0
    updated_count = 0
    processed_files = 0
    skipped_rows = 0
    sku_data_map = {}
    source_map = {}

    for file_obj in file_list:
        if not file_obj or not getattr(file_obj, 'filename', ''):
            continue

        filename = file_obj.filename
        try:
            df = read_file_to_df(file_obj)
            processed_files += 1
            if df.empty:
                warnings.append(f"File '{filename}' kosong dan dilewati.")
                continue

            col_map = match_columns(df.columns.tolist())
            if "kode_barang" not in col_map:
                errors.append(f"File '{filename}' tidak memiliki kolom 'Kode Barang / SKU' yang dapat dikenali.")
                continue

            recognized_fields = sorted(set(col_map) - {"kode_barang"})
            if not recognized_fields:
                warnings.append(f"File '{filename}' hanya mengenali Kode Barang; tidak ada field data lain yang dapat dipetakan.")

            for row_index, row in df.iterrows():
                raw_kode = row[col_map["kode_barang"]]
                if pd.isna(raw_kode) or not str(raw_kode).strip():
                    skipped_rows += 1
                    warnings.append(f"File '{filename}' baris {row_index + 2}: Kode Barang kosong; baris dilewati.")
                    continue

                kode = str(raw_kode).strip()
                if kode not in sku_data_map:
                    sku_data_map[kode] = {}
                    source_map[kode] = {}

                for field in [
                    "nama_barang", "supplier", "stok_gudang", "dipesan", "dijual",
                    "penjualan_mei", "penjualan_juni", "penjualan_juli", "penjualan_agustus"
                ]:
                    if field not in col_map or pd.isna(row[col_map[field]]):
                        continue

                    raw_value = row[col_map[field]]
                    if field == "supplier":
                        sup_str = str(raw_value).upper().strip()
                        if "IMPOR" in sup_str or "IMPORT" in sup_str:
                            value = "IMPOR"
                        elif "LOKAL" in sup_str or "LOCAL" in sup_str:
                            value = "LOKAL"
                        else:
                            warnings.append(
                                f"SKU {kode} pada '{filename}': tipe supplier '{raw_value}' tidak dikenali; field diabaikan."
                            )
                            continue
                    elif field == "nama_barang":
                        value = str(raw_value).strip()
                        if not value:
                            continue
                    elif field in NUMERIC_FIELDS:
                        value = _parse_numeric(raw_value, kode, field, filename, warnings)
                        if value is None:
                            continue
                    else:
                        value = raw_value

                    _set_merged_value(
                        sku_data_map, source_map, kode, field, value, filename, warnings
                    )

        except Exception as exc:
            errors.append(f"Gagal memproses file '{filename}': {exc}")

    if not sku_data_map:
        return {
            "created": 0,
            "updated": 0,
            "total": 0,
            "processed_files": processed_files,
            "skipped_rows": skipped_rows,
            "warnings": warnings,
            "errors": errors if errors else ["Tidak ada data SKU valid yang ditemukan dalam file."],
        }

    for kode, data in sku_data_map.items():
        existing_sku = db.session.get(SKU, kode)
        if existing_sku:
            for field, value in data.items():
                if field != "kode_barang":
                    setattr(existing_sku, field, value)
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
    except Exception as exc:
        db.session.rollback()
        errors.append(f"Gagal menyimpan ke database: {exc}")
        created_count = 0
        updated_count = 0

    return {
        "created": created_count,
        "updated": updated_count,
        "total": len(sku_data_map),
        "processed_files": processed_files,
        "skipped_rows": skipped_rows,
        "warnings": warnings,
        "errors": errors,
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
            "Lead Time": r["lead_time"],
            "Safety Stock Days": round(r["safety_stock_days"], 2),
            "Status": r["status"],
            "Rekomendasi": r["rekomendasi"],
        })

    df = pd.DataFrame(export_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Hasil Analisis Coverage")
    output.seek(0)
    return output
