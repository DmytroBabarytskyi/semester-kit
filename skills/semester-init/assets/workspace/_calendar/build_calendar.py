"""Builds «calendar.html» and «calendar.ics» from works.json + the class timetable.

Rule (from works.json): a work issued at practical/lab session N is due before session N+1 starts
and is defended there; if DL has its own deadline, the earlier of the two wins.

Usage:
  python build_calendar.py                                   rebuild only
  python build_calendar.py --set ТВО ЛБ2 status=submitted    change fields of a work in works.json, then rebuild
  python build_calendar.py --set ІТРОІ ПЗ3 dl=2026-11-30T23:59 --set ТВО ПЗ3 status=defended
  python build_calendar.py --schedule path\\to\\schedule.json
Statuses: todo / submitted / defended. `dl=` (empty) clears a deadline; `issued=3` re-binds a work to session 3.
schedule.json: _calendar/schedule.json of the workspace (made by /kurs-init), else the class reminder's copy in
%USERPROFILE%\\ClassReminder (never %LOCALAPPDATA%: the Claude desktop app is a packaged app, and its writes
there are invisible to the rest of Windows).
"""
import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORKS = os.path.join(HERE, 'works.json')
KYIV = ZoneInfo('Europe/Kyiv')
STATUSES = ('todo', 'submitted', 'defended')

PALETTE = ['#2563eb', '#0d9488', '#c026d3', '#d97706', '#16a34a', '#dc2626', '#7c3aed', '#64748b',
           '#0891b2', '#be123c', '#65a30d', '#9333ea']  # a discipline may pin its own with "color" in works.json


def sessions_for(abbr, events):
    """Practical/lab days for one discipline: [(date, first pair start)], consecutive pairs merged."""
    days = {}
    for e in events:
        if e['abbr'] == abbr and e['kind'] != 'Лекція':
            day = e['start'][:10]
            days[day] = min(days.get(day, e['start']), e['start'])
    return [datetime.fromisoformat(days[d]) for d in sorted(days)]


def compute(cfg, events):
    rows = []
    for i, d in enumerate(cfg['disciplines']):
        color = d.get('color') or PALETTE[i % len(PALETTE)]
        sess = sessions_for(d['schedule_abbr'], events) if d.get('schedule_abbr') else []
        for w in d['works']:
            rule = defense = None
            if w.get('issued') is not None and w['issued'] < len(sess):
                rule = sess[w['issued']]          # issued at session N (1-based) -> session N+1 is index N
                if w.get('defense', True):
                    defense = rule
            dl = datetime.fromisoformat(w['dl']) if w.get('dl') else None
            due = min(x for x in (rule, dl) if x) if (rule or dl) else None
            rows.append({
                'disc': d['key'], 'name': d['name'], 'folder': d['folder'], 'color': color,
                'id': w['id'], 'title': w['title'], 'status': w.get('status', 'todo'),
                'due': due.isoformat(timespec='minutes') if due else None,
                'basis': None if not due else ('орієнтир' if w.get('soft') and due == dl
                                               else 'DL' if dl and due == dl and (not rule or dl < rule) else 'правило'),
                'rule': rule.isoformat(timespec='minutes') if rule else None,
                'dl': dl.isoformat(timespec='minutes') if dl else None,
                'defense': defense.isoformat(timespec='minutes') if defense else None,
                'url': w.get('url') or d.get('dl'), 'note': w.get('note', ''),
            })
    return rows


def ics(rows):
    def esc(s):
        return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

    def utc(dt):
        return dt.replace(tzinfo=KYIV).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    out = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//IV kurs//Kalendar zdachi//UK', 'CALSCALE:GREGORIAN',
           'X-WR-CALNAME:Здача робіт — IV курс', 'X-WR-TIMEZONE:Europe/Kyiv']
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for r in rows:
        if not r['due'] or r['status'] in ('submitted', 'defended'):
            continue
        due = datetime.fromisoformat(r['due'])
        desc = [r['title'], f"Здати до: {due:%d.%m.%Y %H:%M} ({r['basis']})"]
        if r['dl']:
            desc.append(f"Дедлайн DL: {datetime.fromisoformat(r['dl']):%d.%m.%Y %H:%M}")
        if r['defense']:
            desc.append(f"Захист: {datetime.fromisoformat(r['defense']):%d.%m.%Y %H:%M}")
        if r['note']:
            desc.append(r['note'])
        desc.append(r['url'] or '')
        uid = f"{r['disc']}-{r['id']}@iv-kurs".encode('ascii', 'xmlcharrefreplace').decode()
        summary = f"⏰ {r['disc']} {r['id']} — здати"
        out += ['BEGIN:VEVENT', f'UID:{uid}', f'DTSTAMP:{stamp}',
                f'DTSTART:{utc(due - timedelta(minutes=30))}', f'DTEND:{utc(due)}',
                f'SUMMARY:{esc(summary)}', 'DESCRIPTION:' + esc('\n'.join(desc))]
        if r['url']:
            out.append(f"URL:{r['url']}")
        for trig in ('-P2D', '-PT3H'):
            out += ['BEGIN:VALARM', 'ACTION:DISPLAY', f"DESCRIPTION:{esc(r['disc'] + ' ' + r['id'])}",
                    f'TRIGGER:{trig}', 'END:VALARM']
        out.append('END:VEVENT')
    out.append('END:VCALENDAR')
    return ''.join(fold(line) + '\r\n' for line in out)


def fold(line):
    """RFC 5545 line folding: at most 75 octets per physical line."""
    parts, cur = [], b''
    for ch in line:
        b = ch.encode('utf-8')
        if len(cur) + len(b) > (75 if not parts else 74):
            parts.append(cur.decode('utf-8'))
            cur = b''
        cur += b
    parts.append(cur.decode('utf-8'))
    return '\r\n '.join(parts)


def apply_sets(cfg, sets):
    """--set DISC ID key=value ... -> edit works.json in place; returns printable change log."""
    log = []
    for disc, wid, *pairs in sets:
        d = next((x for x in cfg['disciplines'] if x['key'] == disc), None)
        w = d and next((x for x in d['works'] if x['id'] == wid), None)
        if not w:
            raise SystemExit(f'Немає роботи {disc} {wid} у works.json')
        for pair in pairs:
            key, _, val = pair.partition('=')
            if key == 'status' and val not in STATUSES:
                raise SystemExit(f'status має бути одним з {STATUSES}')
            if key == 'dl' and val:
                datetime.fromisoformat(val)
            w[key] = int(val) if key == 'issued' and val else (val or None)
            log.append(f'{disc} {wid}: {key} = {w[key]}')
    cfg['updated'] = date.today().isoformat()
    return log


def save_works(cfg):
    """Same layout as the hand-written file: one line per work, so diffs stay readable."""
    lines = ['{', f'  "updated": {json.dumps(cfg["updated"])},', f'  "rule": {json.dumps(cfg["rule"], ensure_ascii=False)},',
             '  "disciplines": [']
    for i, d in enumerate(cfg['disciplines']):
        head = {k: v for k, v in d.items() if k != 'works'}
        lines.append('    {')
        lines += [f'      {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},' for k, v in head.items()]
        lines.append('      "works": [')
        works = [json.dumps(w, ensure_ascii=False) for w in d['works']]
        lines += [f'        {w}{"," if j < len(works) - 1 else ""}' for j, w in enumerate(works)]
        lines += ['      ]', '    }' + (',' if i < len(cfg['disciplines']) - 1 else '')]
    lines += ['  ]', '}', '']
    open(WORKS, 'w', encoding='utf-8').write('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', nargs='+', action='append', default=[], metavar='DISC ID key=value')
    local = os.path.join(HERE, 'schedule.json')
    ap.add_argument('--schedule', default=local if os.path.exists(local)
                    else os.path.expandvars(r'%USERPROFILE%\ClassReminder\schedule.json'))
    args = ap.parse_args()
    cfg = json.load(open(WORKS, encoding='utf-8'))
    if args.set:
        print('\n'.join(apply_sets(cfg, args.set)))
        save_works(cfg)
    events = json.load(open(args.schedule, encoding='utf-8'))
    rows = compute(cfg, events)
    data = json.dumps({'rows': rows, 'updated': cfg['updated'], 'rule': cfg['rule']}, ensure_ascii=False)
    tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    open(os.path.join(ROOT, 'calendar.html'), 'w', encoding='utf-8').write(tpl.replace('/*__DATA__*/null', data))
    open(os.path.join(ROOT, 'calendar.ics'), 'w', encoding='utf-8', newline='').write(ics(rows))
    dated = sum(1 for r in rows if r['due'])
    print(f'{len(rows)} робіт ({dated} з датою) -> calendar.html, calendar.ics')


if __name__ == "__main__":
    main()
