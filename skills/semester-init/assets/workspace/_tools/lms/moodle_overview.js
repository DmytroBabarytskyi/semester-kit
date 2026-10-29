// Знімок стану всіх завдань і тестів курсів DL (dl.nure.ua) -> файл kurs_overview.json у «Завантаженнях».
// Як використовувати (Claude in Chrome, javascript_tool, на будь-якій сторінці dl.nure.ua, де студент залогінений):
//   1. у масив COURSES нижче вписати id курсів (з _profile.json), напр. [1234, 5678]
//   2. виконати; скрипт працює у фоні (сторінки – по одній з паузою 3 с, щоб не спрацював захист від ботів)
//   3. опитувати `window.__kurs.status` до 'done' (або 'BLOCKED' – попросити студента пройти перевірку,
//      'LOGIN' – попросити увійти), потім `python _tools/lms/apply_overview.py <шлях до kurs_overview.json>`
// Не навігувати вкладку, поки скрипт працює: перехід на іншу сторінку його зупинить.
window.__kurs = { status: 'start' };
(async () => {
  const COURSES = [];
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { fetched: new Date().toISOString(), courses: {} };
  for (const id of COURSES) {
    window.__kurs.status = 'course ' + id;
    const r = await fetch(`/course/overview.php?id=${id}&expand[]=assign&expand[]=quiz`);
    if (r.url.includes('/login/')) { window.__kurs.status = 'LOGIN'; return; }
    const d = new DOMParser().parseFromString(await r.text(), 'text/html');
    if (d.title.includes('Human Verification')) { window.__kurs.status = 'BLOCKED'; return; }
    const items = [];
    for (const tr of d.querySelectorAll('table tbody tr')) {
      const a = tr.querySelector('a.activityname, a[href*="/mod/"]');
      const m = a && a.href.match(/\/mod\/(\w+)\/view\.php\?id=(\d+)/);
      if (!m) continue;
      const cells = {};
      for (const td of tr.querySelectorAll('td[data-mdl-overview-item]'))
        cells[td.dataset.mdlOverviewItem] = { value: td.dataset.mdlOverviewValue || '', text: clean(td.textContent) };
      const section = tr.querySelector('td[data-mdl-overview-item="name"] .small');
      items.push({ mod: m[1], cmid: m[2], name: clean(a.textContent), section: clean(section && section.textContent), cells });
    }
    out.courses[id] = { title: clean(d.title), items };
    await sleep(3000);
  }
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: 'application/json' });
  const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'kurs_overview.json' });
  document.body.appendChild(link); link.click(); link.remove();
  window.__kurs.status = 'done';
})().catch(e => { window.__kurs.status = 'ERR ' + e; });
'started';
