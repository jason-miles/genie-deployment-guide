(() => {
  'use strict';
  /* renderShelf builds the resource cards from the JSON block in index.html.
     Each resource: {type: "pdf" | "blog", title, href, icon, blurb}. */
  const LABEL = { pdf: 'PDF', blog: 'Blog' };
  const HINT = { pdf: 'Downloads a PDF file', blog: 'Opens in a new tab' };

  function renderShelf(resources, root) {
    root.replaceChildren();
    resources.forEach(r => {
      const a = document.createElement('a');
      a.className = 'res-card';
      a.dataset.type = r.type;
      a.href = r.href;
      if (r.type === 'pdf') a.setAttribute('download', '');
      else { a.target = '_blank'; a.rel = 'noopener noreferrer'; }

      const frame = document.createElement('span');
      frame.className = 'res-frame';
      const img = document.createElement('img');
      img.src = r.icon; img.alt = ''; img.width = 96; img.height = 96;
      frame.appendChild(img);

      const badge = document.createElement('span');
      badge.className = 'res-badge ' + r.type;
      badge.textContent = LABEL[r.type];
      const title = document.createElement('span');
      title.className = 'res-title'; title.textContent = r.title;
      const blurb = document.createElement('span');
      blurb.className = 'res-blurb'; blurb.textContent = r.blurb;

      const hint = document.createElement('span');
      hint.className = 'res-sr'; hint.textContent = HINT[r.type];

      a.append(frame, badge, title, blurb, hint);
      root.appendChild(a);
    });
  }

  const data = document.getElementById('shelf-data');
  const list = document.querySelector('section.shelf .res-list');
  if (data && list) {
    try { renderShelf(JSON.parse(data.textContent), list); } catch (e) { /* leave the shelf empty */ }
  }
  window.renderShelf = renderShelf;
})();
