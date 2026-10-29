"""Converts a NURE TimeTable_*.xls (SpreadsheetML export from cist.nure.ua) into schedule.json.

Usage:
  python -I parse_timetable.py <TimeTable.xls> --list              disciplines in the timetable (abbr, subgroup, name)
  python -I parse_timetable.py <TimeTable.xls> [--skip ABBR ...] [--out schedule.json]
--skip drops disciplines the student does not attend (other electives / subgroups, or ones without reminders).
--out defaults to schedule.json next to this script (that is where reminder.ps1 reads it).
"""
import argparse, collections, json, os, re
import xml.etree.ElementTree as ET
from datetime import datetime

SS = '{urn:schemas-microsoft-com:office:spreadsheet}'
DAYS = {'Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця", 'Субота', 'Неділя'}
KINDS = {'Лк': 'Лекція', 'Пз': 'Практика', 'Лб': 'Лабораторна'}


def rows(path):
    ws = ET.parse(path).getroot().find(SS + 'Worksheet')
    for row in ws.iter(SS + 'Row'):
        cells, col = {}, 0
        for c in row.findall(SS + 'Cell'):
            col = int(c.get(SS + 'Index') or col + 1)
            d = c.find(SS + 'Data')
            span = int(c.get(SS + 'MergeAcross') or 0)
            text = ''.join(d.itertext()).strip() if d is not None else ''
            # A class cell merged across N weeks means the class is held every one of those weeks
            for k in range(span + 1):
                if text and (k == 0 or col > 2):
                    cells[col + k] = text
            col += span
        yield cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('timetable')
    ap.add_argument('--skip', nargs='*', default=[])
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.json'))
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()
    skip = set(args.skip)
    all_rows = list(rows(args.timetable))

    # Legend: "ABBR | Full name : ..." rows after the grid
    names = {}
    for r in all_rows:
        if 2 in r and 4 in r and ':' in r[4]:
            names[r[2].lstrip('*').strip()] = r[4].split(':')[0].lstrip('*').strip()

    events, dates = [], {}
    for r in all_rows:
        if r.get(1) in DAYS:
            dates = {c: v for c, v in r.items() if re.fullmatch(r'\d\d\.\d\d\.\d{4}', v)}
            continue
        m = re.fullmatch(r'(\d\d:\d\d)\s+(\d\d:\d\d)', r.get(2, ''))
        if not (dates and m):
            continue
        for col, text in r.items():
            if col < 3 or col not in dates:
                continue
            cm = re.match(r'\*?(.+?)\s+(Лк|Пз|Лб)\b', text)
            abbr = cm.group(1).strip() if cm else text
            if abbr in skip:
                continue
            day = datetime.strptime(dates[col], '%d.%m.%Y').strftime('%Y-%m-%d')
            events.append({
                'start': f'{day}T{m.group(1)}', 'end': f'{day}T{m.group(2)}',
                'abbr': abbr, 'name': names.get(abbr, abbr),
                'kind': KINDS.get(cm.group(2), '') if cm else '', 'raw': text,
            })

    events.sort(key=lambda e: e['start'])
    if args.list:
        stats = collections.defaultdict(lambda: {'n': 0, 'sub': set(), 'kinds': set(), 'elective': False})
        for e in events:
            s = stats[e['abbr']]
            s['n'] += 1
            s['kinds'].add(e['kind'])
            s['sub'].update(re.findall(r'\(№(\d+)\)', e['raw']))
            s['elective'] |= e['raw'].startswith('*')
        for abbr, s in sorted(stats.items()):
            sub = f" підгрупа №{','.join(sorted(s['sub']))}" if s['sub'] else ''
            print(f"{abbr}\t{'вибіркова' if s['elective'] else 'обов.'}{sub}\t{s['n']} пар\t{names.get(abbr, abbr)}")
        return
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=1)
    print(f'{len(events)} занять -> {args.out}')


main()
