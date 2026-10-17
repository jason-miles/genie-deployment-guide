(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Storage: falls back to memory when localStorage is blocked
  const store = (() => {
    try { const t = '__genie'; localStorage.setItem(t, '1'); localStorage.removeItem(t); return localStorage; }
    catch (e) { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, removeItem: k => { delete m[k]; } }; }
  })();

  // Theme
  const root = document.documentElement;
  const saved = store.getItem('genie-theme');
  if (saved) root.dataset.theme = saved;
  else if (matchMedia('(prefers-color-scheme: dark)').matches) root.dataset.theme = 'dark';
  $('#theme').addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    store.setItem('genie-theme', next);
  });

  $('#print').addEventListener('click', () => print());

  // Mobile menu
  const tog = $('#navtoggle'), side = $('#sidenav');
  const setMenu = open => { side.classList.toggle('open', open); tog.setAttribute('aria-expanded', open); tog.textContent = open ? 'Close' : 'Menu'; };
  tog.addEventListener('click', () => setMenu(!side.classList.contains('open')));
  $$('#sidenav nav a').forEach(a => a.addEventListener('click', () => { if (matchMedia('(max-width: 940px)').matches) setMenu(false); }));

  // Reading progress
  const bar = $('#progress span');
  const onScroll = () => {
    const h = document.documentElement;
    bar.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight || 1)) * 100 + '%';
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Scrollspy
  const links = new Map($$('.sidebar nav a').map(a => [a.getAttribute('href').slice(1), a]));
  const spy = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      links.forEach(a => a.classList.remove('active'));
      links.get(e.target.id)?.classList.add('active');
    });
  }, { rootMargin: '-15% 0px -75% 0px' });
  $$('section.step').forEach(s => spy.observe(s));

  // Sidebar filter
  $('#filter').addEventListener('input', e => {
    const q = e.target.value.trim().toLowerCase();
    $$('.sidebar nav li').forEach(li => {
      const sec = document.getElementById(li.firstElementChild.getAttribute('href').slice(1));
      const hit = !q || sec.textContent.toLowerCase().includes(q);
      li.classList.toggle('hide', !hit);
    });
  });

  // Scrollable tables: keyboard reachable and named by the heading above
  $$('.table-wrap').forEach((w, i) => {
    let prev = w.previousElementSibling;
    while (prev && !/^H[23]$/.test(prev.tagName)) prev = prev.previousElementSibling;
    const sec = w.closest('section')?.querySelector('h2')?.textContent || '';
    w.tabIndex = 0; w.setAttribute('role', 'region');
    w.setAttribute('aria-label', ((prev ? prev.textContent : sec) + ' table ' + (i + 1)).trim());
  });

  // Copy buttons
  $$('pre').forEach(pre => {
    const b = document.createElement('button');
    b.className = 'copy'; b.type = 'button'; b.textContent = 'Copy';
    b.addEventListener('click', async () => {
      await navigator.clipboard.writeText(pre.innerText.replace(/\nCopy$/, ''));
      b.textContent = 'Copied'; setTimeout(() => (b.textContent = 'Copy'), 1400);
    });
    pre.appendChild(b);
  });

  // Step gates: persisted, shown in the sidebar
  const gates = $$('input[data-gate]');
  const gateTally = () => {
    gates.forEach(g => links.get(g.dataset.gate)?.classList.toggle('done', g.checked));
    const done = gates.filter(g => g.checked).length;
    $('#gate-tally').textContent = `Gates passed: ${done} of ${gates.length}`;
    if (typeof overall === 'function') overall();
  };
  gates.forEach(g => {
    g.checked = store.getItem('genie-gate-' + g.dataset.gate) === '1';
    g.addEventListener('change', () => { store.setItem('genie-gate-' + g.dataset.gate, g.checked ? '1' : '0'); gateTally(); });
  });
  gateTally();

  // Light syntax highlighting (comments, strings, keywords)
  const esc = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const SQL = 'SELECT|FROM|WHERE|GROUP BY|HAVING|CREATE|ALTER|DROP|TABLE|VIEW|CATALOG|SCHEMA|CONNECTION|AS|SET|UNSET|MANAGED|EXTERNAL|MOVE|COPY|SYNC|DRY RUN|CONVERT TO DELTA|DEEP CLONE|SHALLOW CLONE|GRANT|REVOKE|ON|TO|INTO|USE|SHOW|DESCRIBE|INSERT|OVERWRITE|LIKE|AND|OR|NOT|IF EXISTS|IF NOT EXISTS|WITH|OPTIONS|TYPE|USING|LOCATION|PARTITIONED BY|COUNT|MAX|MIN|INTERVAL|DAYS';
  const rx = {
    sql: new RegExp("(--[^\\n]*)|('(?:[^'\\\\\\n]|\\\\.)*')|\\b(" + SQL + ")\\b", 'gi'),
    sh: /(^|\s)(#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'[^'\n]*')/g,
    py: /(#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')|\b(import|from|def|return|for|in|if|else|with|as|try|except|print|True|False|None)\b/g
  };
  // Code samples: {{var:default}} tokens take values from "Your environment"
  const envKey = 'genie-env';
  let env = {};
  try { env = JSON.parse(store.getItem(envKey) || '{}'); } catch (e) { env = {}; }
  const clean = v => v.replace(/[^\w-]/g, '');
  const codes = $$('pre[data-lang] code').map(code => ({ code, lang: code.parentElement.dataset.lang.toLowerCase(), src: code.textContent }));
  const paint = ({ code, lang, src }) => {
    const text = src.replace(/\{\{(\w+):([^}]*)\}\}/g, (m, k, d) => '\uE000' + (env[k] || d) + '\uE001');
    let html = esc(text);
    if (lang === 'sql') html = html.replace(rx.sql, (m, c, st, k) => c ? `<span class="c">${c}</span>` : st ? `<span class="s">${st}</span>` : `<span class="k">${k}</span>`);
    else if (lang === 'bash' || lang === 'sh' || lang === 'shell') html = html.replace(rx.sh, (m, pre, c, st) => c ? `${pre}<span class="c">${c}</span>` : `<span class="s">${st}</span>`);
    else if (lang === 'python' || lang === 'py') html = html.replace(rx.py, (m, c, st, k) => c ? `<span class="c">${c}</span>` : st ? `<span class="s">${st}</span>` : `<span class="k">${k}</span>`);
    code.innerHTML = html.replace(/\uE000/g, '<mark class="v">').replace(/\uE001/g, '</mark>');
  };
  const paintAll = () => codes.forEach(paint);
  paintAll();
  $$('input[data-var]').forEach(inp => {
    if (env[inp.dataset.var]) inp.value = env[inp.dataset.var];
    inp.addEventListener('input', () => {
      const v = clean(inp.value);
      if (v !== inp.value) inp.value = v;
      env[inp.dataset.var] = v;
      store.setItem(envKey, JSON.stringify(env));
      paintAll();
    });
  });
  $('#env-reset').addEventListener('click', () => {
    env = {}; store.removeItem(envKey);
    $$('input[data-var]').forEach(i => { i.value = i.defaultValue; });
    paintAll();
  });

  // Persisted checklists
  $$('ul.check input').forEach((box, i) => {
    const key = 'genie-chk-' + i;
    box.checked = store.getItem(key) === '1';
    box.addEventListener('change', () => {
      store.setItem(key, box.checked ? '1' : '0');
      tally();
    });
  });
  function tally() {
    const all = $$('ul.check input');
    const done = all.filter(b => b.checked).length;
    const tl = $('#tally'); if (tl) tl.textContent = `${done} / ${all.length} checklist items complete`;
    overall();
  }
  tally();
  $('#reset')?.addEventListener('click', () => {
    $$('ul.check input').forEach((b, i) => { b.checked = false; store.removeItem('genie-chk-' + i); });
    tally();
  });

  // Overall progress: gates plus checklist items
  function overall() {
    const items = [...$$('input[data-gate]'), ...$$('ul.check input')];
    const done = items.filter(i => i.checked).length;
    const pct = items.length ? Math.round(done / items.length * 100) : 0;
    $('.meter span').style.width = pct + '%';
    $('.meter').setAttribute('aria-valuenow', pct);
    $('#overall-label').textContent = `${pct}% complete`;
  }
  overall();

  // Next-step links
  const order = $$('section.step');
  order.forEach((sec, i) => {
    const nx = order[i + 1];
    if (!nx || !/^step-\d$/.test(sec.id)) return;
    const a = document.createElement('a');
    a.className = 'next'; a.href = '#' + nx.id;
    a.textContent = 'Next: ' + nx.querySelector('h2').textContent + ' \u2192';
    sec.appendChild(a);
  });

  // Search palette
  const pal = $('#palette'), pq = $('#pal-q'), pl = $('#pal-list');
  let idx = null, hits = [], sel = 0;
  const build = () => {
    idx = $$('main section.step').flatMap(sec => {
      const sname = sec.querySelector('h2').textContent;
      return $$('h3, p, li, td, summary, .gate, .callout, pre', sec).map(el => ({ el, sname, h: /^H3|SUMMARY$/.test(el.tagName), text: el.innerText.replace(/\s+/g, ' ').replace(/Copy$/, '').trim() }));
    }).filter(r => r.text.length > 2);
  };
  const render = () => {
    pl.innerHTML = '';
    hits.forEach((r, i) => {
      const li = document.createElement('li');
      li.setAttribute('role', 'option'); li.id = 'pal-o' + i; li.setAttribute('aria-selected', i === sel);
      const t = document.createElement('span'); t.className = 'pal-sec'; t.textContent = r.sname;
      const x = document.createElement('span'); x.textContent = r.snip;
      li.append(t, x);
      li.addEventListener('click', () => go(i));
      pl.appendChild(li);
    });
    if (!hits.length && pq.value.trim()) pl.innerHTML = '<li class="pal-empty" role="option" aria-disabled="true" aria-selected="false">No matches</li>';
    pq.setAttribute('aria-expanded', hits.length > 0);
    if (hits.length) pq.setAttribute('aria-activedescendant', 'pal-o' + sel); else pq.removeAttribute('aria-activedescendant');
  };
  const search = () => {
    if (!idx) build();
    const terms = pq.value.toLowerCase().split(/\s+/).filter(Boolean);
    sel = 0;
    if (!terms.length) { hits = []; return render(); }
    hits = idx.filter(r => terms.every(t => r.text.toLowerCase().includes(t)))
      .sort((a, b) => (b.h - a.h) || (a.text.length - b.text.length)).slice(0, 8)
      .map(r => {
        const at = Math.max(0, r.text.toLowerCase().indexOf(terms[0]) - 40);
        return { ...r, snip: (at ? '\u2026' : '') + r.text.slice(at, at + 120) };
      });
    render();
  };
  const go = i => {
    const r = hits[i]; if (!r) return;
    pal.close();
    r.el.scrollIntoView({ block: 'center' });
    r.el.classList.add('flash'); setTimeout(() => r.el.classList.remove('flash'), 1800);
  };
  const openPal = () => { pq.value = ''; hits = []; render(); pal.showModal(); pq.focus(); };
  $('#search-open').addEventListener('click', openPal);
  addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); pal.open ? pal.close() : openPal(); }
  });
  pq.addEventListener('input', search);
  pq.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + hits.length) % (hits.length || 1);
      $$('#pal-list li').forEach((li, i) => li.setAttribute('aria-selected', i === sel));
      pq.setAttribute('aria-activedescendant', 'pal-o' + sel);
      $$('#pal-list li')[sel]?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') { e.preventDefault(); go(sel); }
  });
  pal.addEventListener('click', e => { if (e.target === pal) pal.close(); });

})();
