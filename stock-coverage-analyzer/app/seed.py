from . import db
from .models import SKU, ColumnMapping

SEED_DATA = [
    {
        "kode_barang": "100118",
        "nama_barang": "Tempat Rak Bumbu Dapur 6IN1",
        "supplier": "IMPOR",
        "stok_gudang": 2400,
        "dipesan": 0,
        "dijual": 26,
        "penjualan_mei": 3953,
        "penjualan_juni": 3636,
        "penjualan_juli": 3329,
        "penjualan_agustus": 1273,
    },
    {
        "kode_barang": "100155",
        "nama_barang": "Senter Tangan SOLAR V-5020",
        "supplier": "LOKAL",
        "stok_gudang": 1844,
        "dipesan": 0,
        "dijual": 0,
        "penjualan_mei": 997,
        "penjualan_juni": 960,
        "penjualan_juli": 909,
        "penjualan_agustus": 288,
    },
    {
        "kode_barang": "100169",
        "nama_barang": "Headset / Handsfree Hi-fi Branded",
        "supplier": "LOKAL",
        "stok_gudang": 1531,
        "dipesan": 0,
        "dijual": 243,
        "penjualan_mei": 5325,
        "penjualan_juni": 7011,
        "penjualan_juli": 7041,
        "penjualan_agustus": 3097,
    },
    {
        "kode_barang": "100173",
        "nama_barang": "Smart Watch Y1 Support SIM Card & Memory Card",
        "supplier": "IMPOR",
        "stok_gudang": 3915,
        "dipesan": 0,
        "dijual": 0,
        "penjualan_mei": 3590,
        "penjualan_juni": 5539,
        "penjualan_juli": 6297,
        "penjualan_agustus": 2839,
    },
    {
        "kode_barang": "100174",
        "nama_barang": "Tripod GMC 01 + Universal Holder for smartphones",
        "supplier": "LOKAL",
        "stok_gudang": 679,
        "dipesan": 6402,
        "dijual": 0,
        "penjualan_mei": 2503,
        "penjualan_juni": 2527,
        "penjualan_juli": 2208,
        "penjualan_agustus": 930,
    },
]

DEFAULT_MAPPINGS = [
    {
        "target_field": "kode_barang",
        "field_label": "Kode Barang / SKU",
        "aliases": "kode barang, kode_barang, kode, sku, item no, no barang, item_code, item code, no. barang, no. sku, item_no, kode sku, kode accurate"
    },
    {
        "target_field": "nama_barang",
        "field_label": "Nama Barang",
        "aliases": "nama barang, nama_barang, nama, deskripsi, description, item name, nama item, item_name, nama produk, product name"
    },
    {
        "target_field": "supplier",
        "field_label": "Tipe Supplier (IMPOR / LOKAL)",
        "aliases": "supplier, tipe supplier, pemasok, tipe, origin, vendor, tipe_supplier"
    },
    {
        "target_field": "stok_gudang",
        "field_label": "Stok Gudang",
        "aliases": "stok gudang, stok_gudang, stok, qty gudang, saldo akhir, sal. akhir, quantity, on hand, stock, stok fisik, stok_fisik"
    },
    {
        "target_field": "dipesan",
        "field_label": "Dipesan (PO Dalam Perjalanan)",
        "aliases": "dipesan, po, on order, dalam perjalanan, qty po, outstanding po, po pending, pesanan pembelian, qty_po"
    },
    {
        "target_field": "dijual",
        "field_label": "Dijual (SO Pending)",
        "aliases": "dijual, so, reserved, pending so, qty so, unprocessed, so pending, pesanan penjualan, qty_so"
    },
    {
        "target_field": "penjualan_mei",
        "field_label": "Penjualan Mei",
        "aliases": "penjualan mei, penjualan_mei, mei, may, sales mei, sales_mei"
    },
    {
        "target_field": "penjualan_juni",
        "field_label": "Penjualan Juni",
        "aliases": "penjualan juni, penjualan_juni, juni, june, sales juni, sales_juni"
    },
    {
        "target_field": "penjualan_juli",
        "field_label": "Penjualan Juli",
        "aliases": "penjualan juli, penjualan_juli, juli, july, sales juli, sales_juli"
    },
    {
        "target_field": "penjualan_agustus",
        "field_label": "Penjualan Agustus",
        "aliases": "penjualan agustus, penjualan_agustus, agustus, august, sales agustus, sales_agustus"
    },
]


def seed_default_mappings(force_reset=False):
    """Mengisi database dengan pengaturan pemetaan default jika belum ada atau saat reset."""
    if force_reset:
        ColumnMapping.query.delete()
        db.session.commit()

    if ColumnMapping.query.count() == 0:
        for m in DEFAULT_MAPPINGS:
            db.session.add(ColumnMapping(**m))
        db.session.commit()


def seed_if_empty():
    """Isi database dengan data contoh & default mapping jika belum ada."""
    if SKU.query.count() == 0:
        for item in SEED_DATA:
            db.session.add(SKU(**item))
        db.session.commit()

    seed_default_mappings(force_reset=False)

