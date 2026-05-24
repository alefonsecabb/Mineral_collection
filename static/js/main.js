document.addEventListener('DOMContentLoaded', () => {

  // ── Image preview (upload tab) ───────────────────────────────
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

  // ── Image source tabs ────────────────────────────────────────
  document.querySelectorAll('.img-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.img-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.img-tab-panel').forEach(p => p.style.display = 'none');
      tab.classList.add('active');
      const panel = document.getElementById('tab-' + tab.dataset.tab);
      if (panel) panel.style.display = 'block';

      // Pre-fill search input with mineral name if switching to search tab
      if (tab.dataset.tab === 'search') {
        const nameInput = document.getElementById('name') || document.querySelector('input[name="name"]');
        const searchInput = document.getElementById('img-search-input');
        if (searchInput && nameInput && nameInput.value.trim() && !searchInput.value.trim()) {
          searchInput.value = nameInput.value.trim();
        }
      }
    });
  });

  // ── Image search ─────────────────────────────────────────────
  const searchBtn    = document.getElementById('img-search-btn');
  const searchInput  = document.getElementById('img-search-input');
  const resultsGrid  = document.getElementById('img-search-results');
  const statusDiv    = document.getElementById('img-search-status');
  const imageUrlInput = document.getElementById('image_url_input');
  const selectedPreview = document.getElementById('img-selected-preview');
  const selectedImg     = document.getElementById('selected-img');
  const clearBtn        = document.getElementById('clear-img-btn');

  function setStatus(msg, loading = false) {
    if (!statusDiv) return;
    statusDiv.style.display = msg ? 'flex' : 'none';
    statusDiv.innerHTML = loading
      ? `<span class="spinner"></span> ${msg}`
      : msg;
  }

  function selectImage(url, thumbUrl, item) {
    if (!imageUrlInput) return;
    imageUrlInput.value = url;
    document.querySelectorAll('.img-result-item').forEach(el => el.classList.remove('selected'));
    item.classList.add('selected');
    if (selectedImg)     selectedImg.src = thumbUrl;
    if (selectedPreview) selectedPreview.style.display = 'flex';
    // Clear file input so URL is used instead
    if (photoInput) photoInput.value = '';
    if (previewBox) previewBox.style.display = 'none';
  }

  function clearSelection() {
    if (imageUrlInput)    imageUrlInput.value = '';
    if (selectedPreview)  selectedPreview.style.display = 'none';
    if (selectedImg)      selectedImg.src = '';
    document.querySelectorAll('.img-result-item').forEach(el => el.classList.remove('selected'));
  }

  async function doSearch() {
    const q = searchInput ? searchInput.value.trim() : '';
    if (!q) return;
    if (resultsGrid) resultsGrid.innerHTML = '';
    clearSelection();
    setStatus('Buscando imagens…', true);

    try {
      const res  = await fetch(`/buscar-imagem?q=${encodeURIComponent(q)}`);
      const data = await res.json();

      if (data.error) { setStatus(`Erro: ${data.error}`); return; }
      if (!data.length) { setStatus('Nenhuma imagem encontrada. Tente outro nome.'); return; }

      setStatus('');
      data.forEach(item => {
        const el = document.createElement('div');
        el.className = 'img-result-item';
        el.title = item.title;
        el.innerHTML = `
          <img src="${item.thumb}" alt="${item.title}" loading="lazy">
          <span class="img-check"><i class="ph ph-check"></i></span>
        `;
        el.addEventListener('click', () => selectImage(item.url, item.thumb, el));
        if (resultsGrid) resultsGrid.appendChild(el);
      });
    } catch (e) {
      setStatus('Erro ao buscar imagens. Verifique sua conexão.');
    }
  }

  if (searchBtn)   searchBtn.addEventListener('click', doSearch);
  if (clearBtn)    clearBtn.addEventListener('click', clearSelection);
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); doSearch(); } });
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
              if (grid && grid.children.length === 0) window.location.reload();
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
