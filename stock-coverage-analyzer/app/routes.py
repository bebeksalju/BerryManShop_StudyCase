from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from . import db
from .models import SKU, ColumnMapping
from .calculator import hitung_semua
from .importer import process_uploaded_files, generate_excel_template, export_analysis_to_excel
from .seed import seed_default_mappings

bp = Blueprint("main", __name__)




# ─── Dashboard & Tabel Analisis ───────────────────────────────────────────────

@bp.route("/")
def index():
    search = request.args.get("search", "").strip()
    filter_supplier = request.args.get("supplier", "")
    filter_status = request.args.get("status", "")

    query = SKU.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(SKU.kode_barang.ilike(like), SKU.nama_barang.ilike(like))
        )
    if filter_supplier in ("IMPOR", "LOKAL"):
        query = query.filter(SKU.supplier == filter_supplier)

    skus = query.all()
    rows = hitung_semua(skus)

    # Filter status dilakukan setelah kalkulasi (status hasil hitung, bukan kolom DB)
    if filter_status:
        rows = [r for r in rows if r["status"] == filter_status]

    # Summary cards (selalu dari seluruh data, bukan filtered)
    all_rows = hitung_semua(SKU.query.all())
    summary = {
        "total": len(all_rows),
        "critical": sum(1 for r in all_rows if r["status"] == "Critical"),
        "need_order": sum(1 for r in all_rows if r["status"] == "Need Order"),
        "sufficient": sum(1 for r in all_rows if r["status"] == "Sufficient"),
        "no_sales": sum(1 for r in all_rows if r["status"] == "No Sales Data"),
    }

    return render_template(
        "index.html",
        rows=rows,
        summary=summary,
        search=search,
        filter_supplier=filter_supplier,
        filter_status=filter_status,
    )


# ─── Tambah SKU ───────────────────────────────────────────────────────────────

@bp.route("/sku/add", methods=["GET", "POST"])
def add_sku():
    if request.method == "POST":
        kode = request.form.get("kode_barang", "").strip()
        if SKU.query.get(kode):
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
        except (ValueError, Exception) as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template("form_sku.html", sku=None, action="Tambah")


# ─── Edit SKU ─────────────────────────────────────────────────────────────────

@bp.route("/sku/<kode>/edit", methods=["GET", "POST"])
def edit_sku(kode):
    sku = SKU.query.get_or_404(kode)

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
        except (ValueError, Exception) as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template("form_sku.html", sku=sku, action="Edit")


# ─── Hapus SKU ────────────────────────────────────────────────────────────────

@bp.route("/sku/<kode>/delete", methods=["POST"])
def delete_sku(kode):
    sku = SKU.query.get_or_404(kode)
    db.session.delete(sku)
    db.session.commit()
    flash(f"SKU '{kode}' berhasil dihapus.", "success")
    return redirect(url_for("main.index"))


# ─── Smart Impor Accurate ──────────────────────────────────────────────────────

@bp.route("/import", methods=["GET", "POST"])
def import_accurate():
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            flash("Silakan pilih minimal 1 file laporan Accurate (.xlsx, .xls, atau .csv).", "warning")
            return redirect(url_for("main.import_accurate"))

        result = process_uploaded_files(files)

        if result["errors"]:
            for err in result["errors"]:
                flash(err, "danger")

        if result["total"] > 0:
            msg = f"Berhasil memproses {result['total']} SKU Accurate! (Ditambahkan: {result['created']}, Diperbarui: {result['updated']})"
            flash(msg, "success")
            return redirect(url_for("main.index"))

    return render_template("import.html")


@bp.route("/import/template")
def download_template():
    excel_stream = generate_excel_template()
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Template_Master_Stok_Accurate.xlsx"
    )


# ─── Ekspor Hasil Analisis Excel ──────────────────────────────────────────────

@bp.route("/export")
def export_excel():
    all_skus = SKU.query.all()
    rows = hitung_semua(all_skus)
    excel_stream = export_analysis_to_excel(rows)
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Hasil_Analisis_Stock_Coverage.xlsx"
    )


# ─── Pengaturan Pemetaan Kolom ────────────────────────────────────────────────

@bp.route("/settings", methods=["GET", "POST"])
def settings():
    seed_default_mappings(force_reset=False)
    mappings = ColumnMapping.query.order_by(ColumnMapping.id).all()

    if request.method == "POST":
        try:
            for m in mappings:
                form_key = f"alias_{m.target_field}"
                new_alias_text = request.form.get(form_key, "").strip()
                m.aliases = new_alias_text
            db.session.commit()
            flash("Pengaturan pemetaan kolom Accurate berhasil disimpan!", "success")
            return redirect(url_for("main.settings"))
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal menyimpan pengaturan: {str(e)}", "danger")

    return render_template("settings.html", mappings=mappings)


@bp.route("/settings/reset", methods=["POST"])
def reset_settings():
    try:
        seed_default_mappings(force_reset=True)
        flash("Pengaturan pemetaan kolom berhasil dikembalikan ke default bawaan Accurate!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal mereset pengaturan: {str(e)}", "danger")
    return redirect(url_for("main.settings"))


