// Повний обхід курсів DL, яких немає в пакеті групи (нова вибіркова тощо) -> kurs_crawl.json у «Завантаженнях».
// Claude in Chrome, javascript_tool, на сторінці dl.nure.ua. У масив COURSES нижче вписати id курсів.
// Працює у фоні (пауза 2,5 с між сторінками); опитувати window.__kurs.status до 'done' / 'BLOCKED' / 'LOGIN'.
// Далі: python _tools/lms/outline.py kurs_crawl.json <тека> – читабельний зміст курсу для аналізу.
// Файли курсу (mod/resource) качає moodle_resources.js; посилання на Google Drive – з поля files / url.
window.__kurs = { status: 'start' };
(async () => {
  const COURSES = [];
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const P = h => new DOMParser().parseFromString(h, 'text/html');
  const txt = e => e ? e.textContent.replace(/[ \t ]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim() : '';
  const links = e => e ? [...e.querySelectorAll('a[href]')].map(a => ({ t: a.textContent.trim(), h: a.href }))
    .filter(l => /pluginfile|\/mod\/(resource|folder|url)\/|google\.com/.test(l.h)) : [];
  const get = async url => {
    const r = await fetch(url); await sleep(2500);
    if (r.url.includes('/login/')) throw 'LOGIN';
    const ct = r.headers.get('content-type') || '';
    if (!ct.includes('html')) return { direct: r.url, ct };
    const d = P(await r.text());
    if (d.title.includes('Human Verification')) throw 'BLOCKED';
    return { d, url: r.url };
  };
  const crawl = {};
  for (const id of COURSES) {
    const { d } = await get('/course/view.php?id=' + id);
    const sections = [...d.querySelectorAll('li.section, li.course-section')].map(s => ({
      name: txt(s.querySelector('.sectionname, h3')), summary: txt(s.querySelector('.summarytext, .summary')),
      files: links(s.querySelector('.summarytext, .summary')),
      acts: [...s.querySelectorAll('li.activity')].map(li => ({
        type: (li.className.match(/modtype_(\w+)/) || [])[1], name: txt(li.querySelector('.instancename')).replace(/\s+/g, ' '),
        href: (li.querySelector('a.aalink, .activityname a') || {}).href,
        desc: txt(li.querySelector('.description, .contentafterlink, .activity-altcontent')),
        files: links(li.querySelector('.description, .contentafterlink, .activity-altcontent')) })) }));
    for (const s of sections) for (const a of s.acts) {
      if (!a.href || !['page', 'assign', 'quiz', 'url', 'folder', 'book'].includes(a.type)) continue;
      window.__kurs.status = `course ${id}: ${a.name.slice(0, 40)}`;
      const r = await get(a.href);
      if (r.direct) { a.direct = r.direct; continue; }
      const main = r.d.querySelector('[role=main]') || r.d.body;
      a.page = txt(main).slice(0, 15000); a.files = a.files.concat(links(main));
      if (a.type === 'url') a.target = (r.d.querySelector('.urlworkaround a') || {}).href || (r.url.includes('dl.nure.ua') ? null : r.url);
    }
    crawl[id] = { title: txt(d.querySelector('h1')), sections };
  }
  const blob = new Blob([JSON.stringify(crawl, null, 1)], { type: 'application/json' });
  const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'kurs_crawl.json' });
  document.body.appendChild(link); link.click(); link.remove();
  window.__kurs.status = 'done';
})().catch(e => { window.__kurs.status = String(e).startsWith('BLOCKED') || e === 'LOGIN' ? e : 'ERR ' + e; });
'started';
