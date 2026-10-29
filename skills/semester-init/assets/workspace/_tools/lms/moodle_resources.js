// Завантажити файли курсу DL (mod/resource) у «Завантаження» з іменами <ПРЕФІКС>__<cmid>__<оригінальна назва>.
// Claude in Chrome, javascript_tool, на сторінці dl.nure.ua. Заповнити LIST: [['ПРЕФІКС', cmid], ...]
// (ПРЕФІКС – латиницею, напр. 'RMZ'). Пауза 3 с між файлами; Chrome може спитати дозвіл на кілька завантажень.
// Наприкінці – kurs_files_log.json. Опитувати window.__kurs.status до 'done'.
// Далі розкласти: python _tools/lms/place_downloads.py <ПРЕФІКС> <тека дисципліни>/materials
window.__kurs = { status: 'start' };
(async () => {
  const LIST = [];
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const log = [];
  for (const [tag, id] of LIST) {
    window.__kurs.status = `${log.length + 1}/${LIST.length} ${tag} ${id}`;
    try {
      let r = await fetch('/mod/resource/view.php?id=' + id);
      if ((r.headers.get('content-type') || '').includes('html')) {
        const d = new DOMParser().parseFromString(await r.text(), 'text/html');
        if (d.title.includes('Human Verification')) { window.__kurs.status = 'BLOCKED'; return; }
        const l = [...d.querySelectorAll('a,object,iframe,embed')].map(e => e.getAttribute('href') || e.getAttribute('data') || e.getAttribute('src') || '')
          .find(h => h.includes('pluginfile'));
        if (!l) { log.push({ tag, id, err: 'no file link' }); await sleep(3000); continue; }
        await sleep(1500); r = await fetch(l);
      }
      const name = decodeURIComponent(r.url.split('?')[0].split('/').pop());
      const blob = await r.blob();
      const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `${tag}__${id}__${name}` });
      document.body.appendChild(a); a.click(); a.remove();
      log.push({ tag, id, name, size: blob.size });
    } catch (e) { log.push({ tag, id, err: String(e) }); }
    await sleep(3000);
  }
  const b = new Blob([JSON.stringify(log, null, 1)], { type: 'application/json' });
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(b), download: 'kurs_files_log.json' });
  document.body.appendChild(a); a.click(); a.remove();
  window.__kurs.status = 'done';
})().catch(e => { window.__kurs.status = 'ERR ' + e; });
'started';
