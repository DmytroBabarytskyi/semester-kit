"""Застосувати знімок DL (kurs_overview.json від moodle_overview.js) до _calendar/works.json.

    python _tools/lms/apply_overview.py <kurs_overview.json> [--dry-run]

Роботи зіставляються з рядками DL за id завдання (cmid з поля "url" роботи в works.json):
- дедлайн DL -> "dl" (unix-час з DL, Київ);
- «Здано на оцінення» / «Оцінено» -> status=submitted (якщо робота ще todo; defended не чіпає);
- кілька робіт на одне завдання DL (ТБ, ІТР, СОАПЗ – «усі звіти в одне завдання») -> дедлайн оновлюється для всіх,
  а статус НЕ ставиться автоматично (одне подання не означає, що здано всі роботи) – лише повідомлення.
Друкує зміни, завдання й тести DL, яких немає в works.json (їх треба додати вручну), і перебудовує календар.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKS = os.path.join(ROOT, '_calendar', 'works.json')
KYIV = ZoneInfo('Europe/Kyiv')
SUBMITTED = ('здано на оцінення', 'оцінено', 'submitted for grading', 'graded')


def cmid(url):
    m = re.search(r'/mod/\w+/view\.php\?id=(\d+)', url or '')
    return m and m.group(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('overview')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    snap = json.load(open(args.overview, encoding='utf-8'))
    cfg = json.load(open(WORKS, encoding='utf-8'))

    by_cmid, ignore = {}, set()
    for d in cfg['disciplines']:
        ignore.update(str(x) for x in d.get('ignore_cmids', []))  # чужі групи, службові тести, консультації
        for w in d['works']:
            if cmid(w.get('url')):
                by_cmid.setdefault(cmid(w['url']), []).append((d, w))

    sets, notes, unknown = [], [], []
    for course_id, course in snap['courses'].items():
        for it in course['items']:
            if it['mod'] not in ('assign', 'quiz') or it['cmid'] in ignore:
                continue
            targets = by_cmid.get(it['cmid'])
            due = it['cells'].get('duedate', {}).get('value')
            status = it['cells'].get('submissionstatus', {}).get('text', '').lower()
            grade = it['cells'].get('Оцінка', it['cells'].get('grade', {})).get('text', '')
            if not targets:
                unknown.append(f"  курс {course_id}: [{it['mod']} {it['cmid']}] {it['name']} ({it['section']})"
                               + (f", дедлайн {datetime.fromtimestamp(int(due), KYIV):%d.%m.%Y %H:%M}" if due and due.isdigit() else ''))
                continue
            for d, w in targets:
                if due and due.isdigit() and int(due) > 0:
                    dl = datetime.fromtimestamp(int(due), KYIV).strftime('%Y-%m-%dT%H:%M')
                    if w.get('dl') != dl and not w.get('soft'):
                        sets.append((d['key'], w['id'], f'dl={dl}'))
                if any(s in status for s in SUBMITTED) and w.get('status', 'todo') == 'todo':
                    if len(targets) == 1:
                        sets.append((d['key'], w['id'], 'status=submitted'))
                    else:
                        notes.append(f"  {d['key']} {w['id']}: на DL спільне завдання «{it['name']}» має статус «{status}» – "
                                     f"перевірити вручну, які саме роботи здано")
                if grade and grade not in ('-', '–'):
                    notes.append(f"  {d['key']} {w['id']}: оцінка на DL {grade}")

    print('Зміни:' if sets else 'Змін у дедлайнах і статусах немає.')
    for disc, wid, kv in sets:
        print(f'  {disc} {wid}: {kv}')
    if notes:
        print('Примітки:'); print('\n'.join(dict.fromkeys(notes)))
    if unknown:
        print('На DL є завдання/тести, яких немає в works.json (додати, якщо це робота студента):')
        print('\n'.join(unknown))
    if sets and not args.dry_run:
        cmd = [sys.executable, '-X', 'utf8', os.path.join(ROOT, '_calendar', 'build_calendar.py')]
        for disc, wid, kv in sets:
            cmd += ['--set', disc, wid, kv]
        subprocess.run(cmd, check=True)


main()
