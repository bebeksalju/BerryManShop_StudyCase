from . import db
from sqlalchemy.orm import validates


class SKU(db.Model):
    __tablename__ = "sku"

    kode_barang = db.Column(db.String(50), primary_key=True)
    nama_barang = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(10), nullable=False)  # IMPOR | LOKAL

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
        """Mengembalikan daftar alias dalam bentuk list string lowercase."""
        if not self.aliases:
            return []
        return [a.strip().lower() for a in self.aliases.split(",") if a.strip()]

    def set_alias_list(self, alias_list):
        """Menyimpan list alias menjadi string tersimpan dipisahkan koma."""
        self.aliases = ", ".join([a.strip() for a in alias_list if a.strip()])

