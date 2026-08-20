from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from sqlalchemy import or_

from . import db
from .models import SKU, ColumnMapping, AnalysisSetting, ImportLog
from .calculator import hitung_semua
from .importer import process_uploaded_files, generate_excel_template, export_analysis_to_excel
from .seed import seed_default_mappings

bp = Blueprint("main", __name__)


def get_analysis_setting():
    """Ambil singleton pengaturan analisis; buat default study case jika belum ada."""
    setting = db.session.get(AnalysisSetting, 1)
    if setting is None:
        setting = AnalysisSetting(
            id=1,
            period_label="Agustus 2026",
            days_elapsed=15,
            days_in_month=31,
            historical_days=92,
        )
        db.session.add(setting)
        db.session.commit()
    return setting


@bp.route("/")
def index():
    search = request.args.get("search", "").strip()
    filter_supplier = request.args.get("supplier", "")
    filter_status = request.args.get("status", "")

    analysis_setting = get_analysis_setting()
    analysis = analysis_setting.to_dict()

    query = SKU.query
    if search:
        like = f"%{search}%"
        query = query.filter(or_(SKU.kode_barang.ilike(like), SKU.nama_barang.ilike(like)))
    if filter_supplier in ("IMPOR", "LOKAL"):
        query = query.filter(SKU.supplier == filter_supplier)

    rows = hitung_semua(query.all(), analysis)
    if filter_status:
        rows = [r for r in rows if r["status"] == filter_status]

    all_rows = hitung_semua(SKU.query.all(), analysis)
    summary = {
        "total": len(all_rows),
        "critical": sum(1 for r in all_rows if r["status"] == "Critical"),
        "need_order": sum(1 for r in all_rows if r["status"] == "Need Order"),
        "sufficient": sum(1 for r in all_rows if r["status"] == "Sufficient"),
        "no_sales": sum(1 for r in all_rows if r["status"] == "No Sales Data"),
    }

    last_import = ImportLog.query.order_by(ImportLog.imported_at.desc()).first()
    return render_template(
        "index.html",
        rows=rows,
        summary=summary,
        search=search,
        filter_supplier=filter_supplier,
        filter_status=filter_status,
        analysis=analysis,
        last_import=last_import,
    )


@bp.route("/sku/add", methods=["GET", "POST"])
def add_sku():
    if request.method == "POST":
        kode = request.form.get("kode_barang", "").strip()
        if db.session.get(SKU, kode):
            flash(f"Kode Barang '{kode}' sudah ada.", "danger")
            return render_template("form_sku.html", sku=None, action="Tambah")

        try:
            sku = SKU(
                kode_barang=kode,
                nama_barang=request.form.get("nama_barang", "").strip(),
                supplier=request.form.get("supplier"),
                stok_gudang=request.form.get("stok_gudang", 0),
                dipesan=request.form.get("dipesan", 0),
                dijual=request.form.get("dijual", 0),
                penjualan_mei=request.form.get("penjualan_mei", 0),
                penjualan_juni=request.form.get("penjualan_juni", 0),
                penjualan_juli=request.form.get("penjualan_juli", 0),
                penjualan_agustus=request.form.get("penjualan_agustus", 0),
            )
            db.session.add(sku)
            db.session.commit()
            flash(f"SKU '{kode}' berhasil ditambahkan.", "success")
            return redirect(url_for("main.index"))
        except Exception as exc:
            db.session.rollback()
            flash(f"Error: {exc}", "danger")

    return render_template("form_sku.html", sku=None, action="Tambah")


@bp.route("/sku/<kode>/edit", methods=["GET", "POST"])
def edit_sku(kode):
    sku = db.get_or_404(SKU, kode)

    if request.method == "POST":
        try:
            sku.nama_barang = request.form.get("nama_barang", "").strip()
            sku.supplier = request.form.get("supplier")
            sku.stok_gudang = request.form.get("stok_gudang", 0)
            sku.dipesan = request.form.get("dipesan", 0)
            sku.dijual = request.form.get("dijual", 0)
            sku.penjualan_mei = request.form.get("penjualan_mei", 0)
            sku.penjualan_juni = request.form.get("penjualan_juni", 0)
            sku.penjualan_juli = request.form.get("penjualan_juli", 0)
            sku.penjualan_agustus = request.form.get("penjualan_agustus", 0)
            db.session.commit()
            flash(f"SKU '{kode}' berhasil diperbarui.", "success")
            return redirect(url_for("main.index"))
        except Exception as exc:
            db.session.rollback()
            flash(f"Error: {exc}", "danger")

    return render_template("form_sku.html", sku=sku, action="Edit")


@bp.route("/sku/<kode>/delete", methods=["POST"])
def delete_sku(kode):
    sku = db.get_or_404(SKU, kode)
    db.session.delete(sku)
    db.session.commit()
    flash(f"SKU '{kode}' berhasil dihapus.", "success")
    return redirect(url_for("main.index"))


@bp.route("/import", methods=["GET", "POST"])
def import_accurate():
    if request.method == "POST":
        files = request.files.getlist("files")
        valid_files = [f for f in files if f and f.filename]
        if not valid_files:
            flash("Silakan pilih minimal 1 file laporan Accurate (.xlsx, .xls, atau .csv).", "warning")
            return redirect(url_for("main.import_accurate"))

        result = process_uploaded_files(valid_files)

        log = ImportLog(
            file_count=result["processed_files"],
            total_skus=result["total"],
            created_count=result["created"],
            updated_count=result["updated"],
            warning_count=len(result["warnings"]),
            error_count=len(result["errors"]),
        )
        db.session.add(log)
        db.session.commit()

        if result["saved"]:
            flash(
                f"Import selesai: {result['processed_files']} file, {result['total']} SKU "
                f"(baru {result['created']}, diperbarui {result['updated']}).",
                "success",
            )

        for warning in result["warnings"][:5]:
            flash(warning, "warning")
        if len(result["warnings"]) > 5:
            flash(
                f"Masih ada {len(result['warnings']) - 5} warning lain. Periksa data sumber sebelum mengambil keputusan Purchasing.",
                "warning",
            )
        for error in result["errors"][:5]:
            flash(error, "danger")

        if result["saved"]:
            return redirect(url_for("main.index"))
        return render_template("import.html", result=result)

    return render_template("import.html", result=None)


@bp.route("/import/template")
def download_template():
    excel_stream = generate_excel_template()
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Template_Master_Stok_Accurate.xlsx",
    )


@bp.route("/export")
def export_excel():
    analysis = get_analysis_setting().to_dict()
    rows = hitung_semua(SKU.query.all(), analysis)
    excel_stream = export_analysis_to_excel(rows)
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Hasil_Analisis_Stock_Coverage.xlsx",
    )


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    seed_default_mappings(force_reset=False)
    mappings = ColumnMapping.query.order_by(ColumnMapping.id).all()
    analysis_setting = get_analysis_setting()

    if request.method == "POST":
        try:
            for mapping in mappings:
                form_key = f"alias_{mapping.target_field}"
                mapping.aliases = request.form.get(form_key, "").strip()

            period_label = request.form.get("period_label", "").strip() or "Periode Analisis"
            days_elapsed = int(request.form.get("days_elapsed", 15))
            days_in_month = int(request.form.get("days_in_month", 31))
            historical_days = int(request.form.get("historical_days", 92))

            if days_elapsed < 1 or days_in_month < 1 or historical_days < 1:
                raise ValueError("Jumlah hari harus lebih besar dari 0.")
            if days_elapsed > days_in_month:
                raise ValueError("Hari berjalan tidak boleh melebihi jumlah hari dalam bulan.")

            analysis_setting.period_label = period_label
            analysis_setting.days_elapsed = days_elapsed
            analysis_setting.days_in_month = days_in_month
            analysis_setting.historical_days = historical_days
            db.session.commit()
            flash("Pengaturan analisis dan pemetaan kolom berhasil disimpan.", "success")
            return redirect(url_for("main.settings"))
        except Exception as exc:
            db.session.rollback()
            flash(f"Gagal menyimpan pengaturan: {exc}", "danger")

    return render_template("settings.html", mappings=mappings, analysis_setting=analysis_setting)


@bp.route("/settings/reset", methods=["POST"])
def reset_settings():
    try:
        seed_default_mappings(force_reset=True)
        flash("Pemetaan kolom berhasil dikembalikan ke default bawaan Accurate.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Gagal mereset pengaturan: {exc}", "danger")
    return redirect(url_for("main.settings"))
