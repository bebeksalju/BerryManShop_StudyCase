// ── Delete confirmation modal (Bootstrap 5) ───────────────────────────────
(function () {
  'use strict';

  const modalEl = document.getElementById('modalHapus');
  if (!modalEl) return;

  const bsModal   = new bootstrap.Modal(modalEl);
  const formHapus = document.getElementById('form-hapus');
  const namaEl    = document.getElementById('modal-nama-sku');

  document.querySelectorAll('.btn-hapus').forEach(btn => {
    btn.addEventListener('click', () => {
      const kode = btn.dataset.kode;
      const nama = btn.dataset.nama;
      namaEl.textContent = `${kode} – ${nama}`;
      formHapus.action   = `/sku/${encodeURIComponent(kode)}/delete`;
      bsModal.show();
    });
  });
})();

// ── Auto-submit filter dropdowns ───────────────────────────────────────────
(function () {
  'use strict';
  const form = document.getElementById('filter-form');
  if (!form) return;

  ['supplier', 'status'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => form.submit());
  });
})();

// ── Number input: prevent negative values ──────────────────────────────────
(function () {
  'use strict';
  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('input', () => {
      if (parseFloat(input.value) < 0) input.value = 0;
    });
  });
})();
