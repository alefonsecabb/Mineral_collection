document.addEventListener('DOMContentLoaded', () => {

  // ── Image preview ────────────────────────────────────────────
  const photoInput = document.getElementById('photo-input');
  const previewBox  = document.getElementById('image-preview');
  const previewImg  = document.getElementById('preview-img');

  if (photoInput && previewBox && previewImg) {
    photoInput.addEventListener('change', () => {
      const file = photoInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewBox.style.display = 'block';
      };
      reader.readAsDataURL(file);
    });
  }

  // ── Drag-and-drop styling ────────────────────────────────────
  const uploadZone = document.getElementById('upload-zone');
  if (uploadZone) {
    uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadZone.classList.add('drag-over');
    });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadZone.classList.remove('drag-over');
      if (e.dataTransfer.files.length && photoInput) {
        photoInput.files = e.dataTransfer.files;
        photoInput.dispatchEvent(new Event('change'));
      }
    });
  }

  // ── Form loading state ───────────────────────────────────────
  const form       = document.getElementById('add-form') || document.getElementById('edit-form');
  const submitBtn  = document.getElementById('submit-btn');
  const submitText = document.getElementById('submit-text');
  const spinner    = document.getElementById('submit-spinner');

  if (form && submitBtn) {
    form.addEventListener('submit', () => {
      submitBtn.disabled = true;
      if (submitText) submitText.textContent = 'Processando...';
      if (spinner)    spinner.style.display = 'inline-block';
    });
  }

  // ── Delete mineral ───────────────────────────────────────────
  document.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id   = btn.dataset.id;
      const name = btn.dataset.name;
      if (!confirm(`Excluir "${name}" da coleção? Esta ação não pode ser desfeita.`)) return;

      try {
        const res  = await fetch(`/mineral/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          const card = document.getElementById(`card-${id}`);
          if (card) {
            card.style.transition = 'opacity 0.3s, transform 0.3s';
            card.style.opacity    = '0';
            card.style.transform  = 'scale(0.9)';
            setTimeout(() => {
              card.remove();
              const grid = document.querySelector('.mineral-grid');
              if (grid && grid.children.length === 0) {
                window.location.reload();
              }
            }, 300);
          } else {
            window.location.href = data.redirect || '/';
          }
        }
      } catch (err) {
        alert('Erro ao excluir o mineral. Tente novamente.');
      }
    });
  });

  // ── Mohs scale bar ───────────────────────────────────────────
  document.querySelectorAll('.mohs-bar').forEach(bar => {
    const h = parseFloat(bar.dataset.hardness);
    if (isNaN(h)) return;
    const filled = Math.round(h);
    for (let i = 1; i <= 10; i++) {
      const seg = document.createElement('div');
      seg.className = 'mohs-seg' + (i <= filled ? ' active' : '');
      seg.title = `${i} Mohs`;
      bar.appendChild(seg);
    }
  });

});
