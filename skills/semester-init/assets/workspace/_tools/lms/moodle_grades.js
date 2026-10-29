// Оцінки студента з Moodle (звіт «Оцінки користувача» кожного курсу) -> moodle_grades.json у «Завантаженнях».
// Claude in Chrome, javascript_tool, на сторінці LMS, де студент залогінений. У масив COURSES вписати id курсів.
// Пауза 3 с між курсами; опитувати window.__kurs.status до 'done' / 'BLOCKED' / 'LOGIN'.
// Далі: python _tools/grades.py import <шлях до moodle_grades.json>
window.__kurs = { status: 'start' };
(async () => {
  const COURSES = [];
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { fetched: new Date().toISOString(), courses: {} };
  for (const id of COURSES) {
    window.__kurs.status = 'course ' + id;
    const r = await fetch(`/grade/report/user/index.php?id=${id}`);
    if (r.url.includes('/login/')) { window.__kurs.status = 'LOGIN'; return; }
    const d = new DOMParser().parseFromString(await r.text(), 'text/html');
    if (d.title.includes('Human Verification')) { window.__kurs.status = 'BLOCKED'; return; }
    const t = d.querySelector('table.user-grade');
    const items = [];
    for (const tr of t ? t.querySelectorAll('tbody tr') : []) {
      const cell = c => clean((tr.querySelector('.column-' + c) || {}).textContent);
      const first = c => (cell(c).match(/^-?\d+(?:[.,]\d+)?|^[-–]/) || [''])[0];  // без меню «Дії / Аналіз балів»
      if (!tr.querySelector('.column-grade')) continue;
      const a = tr.querySelector('.column-itemname a[href*="/mod/"]');
      const head = tr.querySelector('.column-itemname .gradeitemheader, .column-itemname a');
      const name = clean(head ? head.textContent : cell('itemname'));
      const m = a && a.href.match(/\/mod\/(\w+)\/(?:view|grade)\.php\?id=(\d+)/);
      items.push({ name, cmid: m ? m[2] : null, mod: m ? m[1] : null, grade: first('grade'), range: cell('range'),
                   letter: cell('lettergrade'), contribution: cell('contributiontocoursetotal'),
                   total: /Загальне за курс|Підсумок курсу|Course total/i.test(cell('itemname')) });
    }
    out.courses[id] = { title: clean(d.title), items };
    await sleep(3000);
  }
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: 'application/json' });
  const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'moodle_grades.json' });
  document.body.appendChild(link); link.click(); link.remove();
  window.__kurs.status = 'done';
})().catch(e => { window.__kurs.status = 'ERR ' + e; });
'started';
