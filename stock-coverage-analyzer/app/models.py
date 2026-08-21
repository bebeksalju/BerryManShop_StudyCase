from datetime import datetime

from . import db
from sqlalchemy.orm import validates


class SKU(db.Model):
    __tablename__ = "sku"

    kode_barang = db.Column(db.String(50), primary_key=True)
    nama_barang = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(10), nullable=False)

    stok_gudang = db.Column(db.Integer, nullable=False, default=0)
    dipesan = db.Column(db.Integer, nullable=False, default=0)
    dijual = db.Column(db.Integer, nullable=False, default=0)

    penjualan_mei = db.Column(db.Integer, nullable=False, default=0)
    penjualan_juni = db.Column(db.Integer, nullable=False, default=0)
    penjualan_juli = db.Column(db.Integer, nullable=False, default=0)
    penjualan_agustus = db.Column(db.Integer, nullable=False, default=0)

    @validates(
        "stok_gudang", "dipesan", "dijual",
        "penjualan_mei", "penjualan_juni", "penjualan_juli", "penjualan_agustus"
    )
    def validate_non_negative(self, key, value):
        if value is not None and int(value) < 0:
            raise ValueError(f"{key} tidak boleh negatif")
        return int(value) if value is not None else 0

    @validates("supplier")
    def validate_supplier(self, key, value):
        if value not in ("IMPOR", "LOKAL"):
            raise ValueError("Supplier harus IMPOR atau LOKAL")
        return value

    def to_dict(self):
        return {
            "kode_barang": self.kode_barang,
            "nama_barang": self.nama_barang,
            "supplier": self.supplier,
            "stok_gudang": self.stok_gudang,
            "dipesan": self.dipesan,
            "dijual": self.dijual,
            "penjualan_mei": self.penjualan_mei,
            "penjualan_juni": self.penjualan_juni,
            "penjualan_juli": self.penjualan_juli,
            "penjualan_agustus": self.penjualan_agustus,
        }


class ColumnMapping(db.Model):
    __tablename__ = "column_mapping"

    id = db.Column(db.Integer, primary_key=True)
    target_field = db.Column(db.String(50), nullable=False, unique=True)
    field_label = db.Column(db.String(100), nullable=False)
    aliases = db.Column(db.Text, nullable=False, default="")

    def get_alias_list(self):
        if not self.aliases:
            return []
        return [a.strip().lower() for a in self.aliases.split(",") if a.strip()]

    def set_alias_list(self, alias_list):
        self.aliases = ", ".join([a.strip() for a in alias_list if a.strip()])


class AnalysisSetting(db.Model):
    """Parameter periode analisis agar formula study case tidak terkunci pada satu tanggal."""

    __tablename__ = "analysis_setting"

    id = db.Column(db.Integer, primary_key=True, default=1)
    period_label = db.Column(db.String(100), nullable=False, default="Agustus 2026")
    days_elapsed = db.Column(db.Integer, nullable=False, default=15)
    days_in_month = db.Column(db.Integer, nullable=False, default=31)
    historical_days = db.Column(db.Integer, nullable=False, default=92)

    @property
    def total_days(self):
        return self.historical_days + self.days_in_month

    def to_dict(self):
        return {
            "period_label": self.period_label,
            "days_elapsed": self.days_elapsed,
            "days_in_month": self.days_in_month,
            "historical_days": self.historical_days,
            "total_days": self.total_days,
        }


class ImportLog(db.Model):
    """Ringkasan import untuk memastikan freshness dan audit sederhana data Purchasing."""

    __tablename__ = "import_log"

    id = db.Column(db.Integer, primary_key=True)
    imported_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    file_count = db.Column(db.Integer, nullable=False, default=0)
    total_skus = db.Column(db.Integer, nullable=False, default=0)
    created_count = db.Column(db.Integer, nullable=False, default=0)
    updated_count = db.Column(db.Integer, nullable=False, default=0)
    warning_count = db.Column(db.Integer, nullable=False, default=0)
    error_count = db.Column(db.Integer, nullable=False, default=0)


class DailySnapshot(db.Model):
    """Salinan dataset aktif sebelum diganti import berikutnya; dashboard tetap memakai tabel SKU terbaru."""

    __tablename__ = "daily_snapshot"
    __table_args__ = (
        db.UniqueConstraint("snapshot_date", "kode_barang", name="uq_snapshot_date_sku"),
    )

    id = db.Column(db.Integer, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False, index=True)
    captured_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    kode_barang = db.Column(db.String(50), nullable=False, index=True)
    nama_barang = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(10), nullable=False)
    stok_gudang = db.Column(db.Integer, nullable=False, default=0)
    dipesan = db.Column(db.Integer, nullable=False, default=0)
    dijual = db.Column(db.Integer, nullable=False, default=0)
    penjualan_mei = db.Column(db.Integer, nullable=False, default=0)
    penjualan_juni = db.Column(db.Integer, nullable=False, default=0)
    penjualan_juli = db.Column(db.Integer, nullable=False, default=0)
    penjualan_agustus = db.Column(db.Integer, nullable=False, default=0)

    def to_sku_like(self):
        """Objek snapshot punya field yang sama dengan SKU sehingga calculator dapat dipakai ulang."""
        return self
