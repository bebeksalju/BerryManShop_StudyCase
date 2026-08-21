import math

# ─── Default Study Case Parameters ───────────────────────────────────────────
DEFAULT_ANALYSIS = {
    "period_label": "Agustus 2026",
    "days_elapsed": 15,
    "days_in_month": 31,
    "historical_days": 92,  # Mei (31) + Juni (30) + Juli (31)
    "total_days": 123,
}

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


def normalize_analysis(analysis=None) -> dict:
    """Gabungkan parameter analisis user dengan default study case secara aman."""
    cfg = DEFAULT_ANALYSIS.copy()
    if analysis:
        cfg.update({k: v for k, v in analysis.items() if v is not None})

    cfg["days_elapsed"] = max(1, int(cfg["days_elapsed"]))
    cfg["days_in_month"] = max(1, int(cfg["days_in_month"]))
    cfg["historical_days"] = max(1, int(cfg["historical_days"]))
    if cfg["days_elapsed"] > cfg["days_in_month"]:
        cfg["days_elapsed"] = cfg["days_in_month"]
    cfg["total_days"] = cfg["historical_days"] + cfg["days_in_month"]
    return cfg


# ─── Formula ──────────────────────────────────────────────────────────────────

def hitung_proyeksi_bulan_berjalan(penjualan_bulan_berjalan: int, analysis=None) -> float:
    """Proyeksi = (penjualan berjalan / hari berjalan) × jumlah hari bulan."""
    cfg = normalize_analysis(analysis)
    return (penjualan_bulan_berjalan / cfg["days_elapsed"]) * cfg["days_in_month"]


def hitung_proyeksi_agustus(penjualan_agustus: int, analysis=None) -> float:
    """Backward-compatible alias untuk dataset study case yang memakai Agustus."""
    return hitung_proyeksi_bulan_berjalan(penjualan_agustus, analysis)


def hitung_ads(mei: int, juni: int, juli: int, penjualan_agustus: int, analysis=None) -> float:
    """ADS = (3 bulan historis + proyeksi bulan berjalan) / total hari analisis."""
    cfg = normalize_analysis(analysis)
    proyeksi = hitung_proyeksi_bulan_berjalan(penjualan_agustus, cfg)
    return (mei + juni + juli + proyeksi) / cfg["total_days"]


def hitung_coverage(sku, analysis=None) -> dict:
    """
    Hitung metrik coverage dan rekomendasi restock untuk satu SKU.

    Formula coverage tetap mengikuti study case.
    Qty restock adalah extension MVP: sistem mengisi gap agar persediaan
    mencapai target Lead Time + Safety Stock.
    """
    cfg = normalize_analysis(analysis)
    stok_dapat_dijual = sku.stok_gudang - sku.dijual

    proyeksi_bulan_berjalan = hitung_proyeksi_bulan_berjalan(
        sku.penjualan_agustus,
        cfg,
    )
    ads = hitung_ads(
        sku.penjualan_mei,
        sku.penjualan_juni,
        sku.penjualan_juli,
        sku.penjualan_agustus,
        cfg,
    )

    lead_time = LEAD_TIME.get(sku.supplier, 15)
    safety_stock_days = lead_time * SAFETY_STOCK_PCT
    safe_threshold = lead_time + safety_stock_days
    projected_stock_units = stok_dapat_dijual + sku.dipesan

    if ads == 0:
        coverage_days = None
        target_stock_units = None
        recommended_restock_qty = None
        status = "No Sales Data"
        rekomendasi = "Tidak ada data penjualan; qty restock perlu evaluasi manual"
    else:
        coverage_days = projected_stock_units / ads
        target_stock_units = math.ceil(ads * safe_threshold)
        recommended_restock_qty = max(0, target_stock_units - projected_stock_units)

        if coverage_days < lead_time:
            status = "Critical"
            rekomendasi = f"Segera reorder sekitar {recommended_restock_qty:,} unit"
        elif coverage_days < safe_threshold:
            status = "Need Order"
            rekomendasi = f"Siapkan reorder sekitar {recommended_restock_qty:,} unit"
        else:
            status = "Sufficient"
            rekomendasi = "Belum perlu restock"

    return {
        "stok_dapat_dijual": stok_dapat_dijual,
        "projected_stock_units": projected_stock_units,
        "proyeksi_bulan_berjalan": proyeksi_bulan_berjalan,
        "ads": ads,
        "coverage_days": coverage_days,
        "lead_time": lead_time,
        "safety_stock_days": safety_stock_days,
        "safe_threshold": safe_threshold,
        "target_stock_units": target_stock_units,
        "recommended_restock_qty": recommended_restock_qty,
        "status": status,
        "rekomendasi": rekomendasi,
        "badge": STATUS_BADGE[status],
        "sort_order": STATUS_ORDER[status],
        "analysis": cfg,
    }


def hitung_semua(skus: list, analysis=None) -> list:
    """Hitung coverage semua SKU dan urutkan berdasarkan prioritas Purchasing."""
    hasil = []
    for sku in skus:
        data = sku.to_dict()
        data.update(hitung_coverage(sku, analysis))
        hasil.append(data)
    hasil.sort(key=lambda x: (x["sort_order"], x["coverage_days"] is None, x["coverage_days"] or 0))
    return hasil
