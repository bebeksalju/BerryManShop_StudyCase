from types import SimpleNamespace

from app.calculator import hitung_coverage, hitung_ads


ANALYSIS = {
    "period_label": "Agustus 2026",
    "days_elapsed": 15,
    "days_in_month": 31,
    "historical_days": 92,
}


def make_sku(**overrides):
    data = {
        "stok_gudang": 100,
        "dipesan": 0,
        "dijual": 0,
        "penjualan_mei": 0,
        "penjualan_juni": 0,
        "penjualan_juli": 0,
        "penjualan_agustus": 0,
        "supplier": "LOKAL",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def run_tests():
    # Default formula study case harus tetap menghasilkan denominator 123 hari.
    ads = hitung_ads(31, 30, 31, 15, ANALYSIS)
    expected_projection = (15 / 15) * 31
    expected_ads = (31 + 30 + 31 + expected_projection) / 123
    assert abs(ads - expected_ads) < 1e-9

    # ADS = 0 harus menjadi No Sales Data, bukan division by zero.
    no_sales = hitung_coverage(make_sku(), ANALYSIS)
    assert no_sales["coverage_days"] is None
    assert no_sales["status"] == "No Sales Data"

    # Boundary supplier lokal: lead time 15, safety 3, safe threshold 18.
    # Buat ADS = 1 unit/hari secara langsung lewat penjualan historis/proyeksi total 123.
    base_sales = dict(
        penjualan_mei=31,
        penjualan_juni=30,
        penjualan_juli=31,
        penjualan_agustus=15,
    )

    critical = hitung_coverage(make_sku(stok_gudang=14, **base_sales), ANALYSIS)
    assert round(critical["ads"], 10) == 1
    assert critical["coverage_days"] == 14
    assert critical["status"] == "Critical"

    exact_lead = hitung_coverage(make_sku(stok_gudang=15, **base_sales), ANALYSIS)
    assert exact_lead["coverage_days"] == 15
    assert exact_lead["status"] == "Need Order"

    below_safe = hitung_coverage(make_sku(stok_gudang=17, **base_sales), ANALYSIS)
    assert below_safe["status"] == "Need Order"

    exact_safe = hitung_coverage(make_sku(stok_gudang=18, **base_sales), ANALYSIS)
    assert exact_safe["coverage_days"] == 18
    assert exact_safe["status"] == "Sufficient"

    print("✓ Formula ADS default study case konsisten")
    print("✓ ADS = 0 aman")
    print("✓ Boundary Critical / Need Order / Sufficient benar")
    print("=== ALL CALCULATOR TESTS PASSED ===")


if __name__ == "__main__":
    run_tests()
