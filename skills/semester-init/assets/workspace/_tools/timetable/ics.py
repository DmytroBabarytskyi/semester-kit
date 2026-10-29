"""Розклад з .ics (Google Calendar, Outlook, експорт розкладу ВНЗ) -> _calendar/schedule.json.

    python _tools/timetable/ics.py <розклад.ics> [--out _calendar/schedule.json] [--map "Повна назва=АБР" ...] [--skip АБР ...]
    python _tools/timetable/ics.py <розклад.ics> --list

Вид заняття визначається за словами в SUMMARY/DESCRIPTION (лекція / практ / лаб / Лк / Пз / Лб).
Абревіатура: з --map (підрядок назви = абревіатура), інакше SUMMARY без слова-виду. Час переводиться в київський.
"""
import argparse
import collections
import json
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KYIV = ZoneInfo('Europe/Kyiv')
KINDS = [(r'\b(Лк|лекц\w*|lecture)\b', 'Лекція'), (r'\b(Пз|практ\w*|семінар\w*|practice|seminar)\b', 'Практика'),
         (r'\b(Лб|лаб\w*|lab\w*)\b', 'Лабораторна')]


def events(path):
    text = open(path, encoding='utf-8-sig').read().replace('\r\n', '\n').replace('\n ', '').replace('\n\t', '')
    for block in re.findall(r'BEGIN:VEVENT\n(.*?)END:VEVENT', text, re.S):
        props = {}
        for line in block.split('\n'):
            m = re.match(r'([A-Z-]+)((?:;[^:]*)?):(.*)', line)
            if m:
                props[m.group(1)] = (m.group(2), m.group(3).replace('\\,', ',').replace('\\n', ' ').replace('\\;', ';'))
        if 'DTSTART' in props:
            yield props


def when(prop):
    params, value = prop
    tz = re.search(r'TZID=([^;:]+)', params)
    if 'T' not in value:
        return None  # подія на весь день – не пара
    dt = datetime.strptime(value.rstrip('Z')[:15], '%Y%m%dT%H%M%S')
    if value.endswith('Z'):
        dt = dt.replace(tzinfo=timezone.utc)
    elif tz:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(tz.group(1)))
        except Exception:
            dt = dt.replace(tzinfo=KYIV)
    else:
        dt = dt.replace(tzinfo=KYIV)
    return dt.astimezone(KYIV).strftime('%Y-%m-%dT%H:%M')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ics')
    ap.add_argument('--out', default='_calendar/schedule.json')
    ap.add_argument('--map', nargs='*', default=[])
    ap.add_argument('--skip', nargs='*', default=[])
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    mapping = [m.split('=', 1) for m in a.map]
    out = []
    for p in events(a.ics):
        summary = p.get('SUMMARY', ('', ''))[1].strip()
        info = summary + ' ' + p.get('DESCRIPTION', ('', ''))[1]
        kind = next((k for rx, k in KINDS if re.search(rx, info, re.I)), '')
        abbr = next((ab for sub, ab in mapping if sub.lower() in summary.lower()), None) or \
            re.sub(r'\s+', ' ', re.sub(KINDS[0][0] + '|' + KINDS[1][0] + '|' + KINDS[2][0], '', summary, flags=re.I)).strip(' .,-–()')
        start, end = when(p['DTSTART']), when(p.get('DTEND', p['DTSTART']))
        if start and abbr not in a.skip:
            out.append({'start': start, 'end': end, 'abbr': abbr, 'name': summary, 'kind': kind, 'raw': summary})
    out.sort(key=lambda e: e['start'])
    if a.list:
        c = collections.Counter((e['abbr'], e['kind']) for e in out)
        for (abbr, kind), n in sorted(c.items()):
            print(f'{abbr}\t{kind or "?"}\t{n}')
        return
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(out)} занять -> {a.out}')


main()
