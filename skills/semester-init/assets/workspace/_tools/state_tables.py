"""Оновити таблиці «Стан» у CLAUDE.md кожної дисципліни з _calendar/works.json.

    python _tools/state_tables.py

Переписує лише блок між <!-- kurs:state ... --> і <!-- /kurs:state -->; решту CLAUDE.md не чіпає.
"""
import json
import os
import re
import sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '_calendar'))
import build_calendar as bc  # noqa: E402

STATUS = {'todo': 'не здано', 'submitted': 'здано', 'defended': 'захищено'}
BLOCK = re.compile(r'(<!-- kurs:state[^>]*-->\n).*?(<!-- /kurs:state -->)', re.S)


def main():
    cfg = json.load(open(bc.WORKS, encoding='utf-8'))
    local = os.path.join(ROOT, '_calendar', 'schedule.json')
    events = json.load(open(local if os.path.exists(local) else os.path.expandvars(
        r'%USERPROFILE%\ClassReminder\schedule.json'), encoding='utf-8'))
    rows = bc.compute(cfg, events)
    for d in cfg['disciplines']:
        path = os.path.join(ROOT, d['folder'], 'CLAUDE.md')
        if not os.path.exists(path):
            continue
        lines = [f"Станом на {date.today():%d.%m.%Y} (DL + розклад; «здати до» – раніше з правила занять і дедлайну DL).", '',
                 '| Робота | Тема | Здати до | Захист | Стан |', '|---|---|---|---|---|']
        for r in (x for x in rows if x['disc'] == d['key']):
            f = lambda s: datetime.fromisoformat(s).strftime('%d.%m %H:%M') if s else '–'
            lines.append(f"| {r['id']} | {r['title']} | {f(r['due'])} | {f(r['defense'])} | {STATUS.get(r['status'], r['status'])} |")
        text = open(path, encoding='utf-8').read()
        new, n = BLOCK.subn(lambda m: m.group(1) + '\n'.join(lines) + '\n' + m.group(2), text)
        if n:
            open(path, 'w', encoding='utf-8').write(new)
            print('оновлено', path)


main()
