# ─── Konstanta ────────────────────────────────────────────────────────────────
HARI_BERJALAN = 15       # hari berjalan bulan Agustus
HARI_BULAN_AGS = 31      # jumlah hari bulan Agustus
TOTAL_HARI = 123         # 31 (Mei) + 30 (Juni) + 31 (Juli) + 31 (Agustus)

LEAD_TIME = {
    "IMPOR": 80,
    "LOKAL": 15,
}
SAFETY_STOCK_PCT = 0.20

STATUS_ORDER = {
    "Critical": 0,
    "Need Order": 1,
    "Sufficient": 2,
    "No Sales Data": 3,
}

STATUS_BADGE = {
    "Critical": "danger",
    "Need Order": "warning",
    "Sufficient": "success",
    "No Sales Data": "secondary",
}


# ─── Formula ──────────────────────────────────────────────────────────────────

def hitung_proyeksi_agustus(penjualan_agustus: int) -> float:
    """Proyeksi = (penjualan berjalan / hari berjalan) × jumlah hari bulan."""
    return (penjualan_agustus / HARI_BERJALAN) * HARI_BULAN_AGS


def hitung_ads(mei: int, juni: int, juli: int, penjualan_agustus: int) -> float:
    """ADS = (Mei + Juni + Juli + Proyeksi Agustus) / 123."""
    proyeksi = hitung_proyeksi_agustus(penjualan_agustus)
    return (mei + juni + juli + proyeksi) / TOTAL_HARI


def hitung_coverage(sku) -> dict:
    """
    Hitung semua metrik coverage untuk satu SKU.
    Mengembalikan dict berisi: stok_dapat_dijual, ads, coverage_days,
    lead_time, safety_stock_days, status, rekomendasi, badge.
    """
    stok_dapat_dijual = sku.stok_gudang - sku.dijual

    ads = hitung_ads(
        sku.penjualan_mei,
        sku.penjualan_juni,
        sku.penjualan_juli,
        sku.penjualan_agustus,
    )

    lead_time = LEAD_TIME.get(sku.supplier, 15)
    safety_stock_days = lead_time * SAFETY_STOCK_PCT

    if ads == 0:
        coverage_days = None
        status = "No Sales Data"
        rekomendasi = "Tidak ada data penjualan, perlu evaluasi manual"
    else:
        coverage_days = (stok_dapat_dijual + sku.dipesan) / ads
        if coverage_days < lead_time:
            status = "Critical"
            rekomendasi = "Segera lakukan reorder"
        elif coverage_days < lead_time + safety_stock_days:
            status = "Need Order"
            rekomendasi = "Disarankan melakukan reorder"
        else:
            status = "Sufficient"
            rekomendasi = "Stok masih mencukupi"

    return {
        "stok_dapat_dijual": stok_dapat_dijual,
        "ads": ads,
        "coverage_days": coverage_days,
        "lead_time": lead_time,
        "safety_stock_days": safety_stock_days,
        "status": status,
        "rekomendasi": rekomendasi,
        "badge": STATUS_BADGE[status],
        "sort_order": STATUS_ORDER[status],
    }


def hitung_semua(skus: list) -> list:
    """Hitung coverage semua SKU dan urutkan Critical → Need Order → Sufficient → No Sales Data."""
    hasil = []
    for sku in skus:
        data = sku.to_dict()
        data.update(hitung_coverage(sku))
        hasil.append(data)
    hasil.sort(key=lambda x: x["sort_order"])
    return hasil
