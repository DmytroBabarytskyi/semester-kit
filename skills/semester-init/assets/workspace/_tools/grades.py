"""Облік оцінок і середній бал семестру.

    python _tools/grades.py import moodle_grades.json     оцінки з Moodle (поточний «Підсумок курсу» кожної дисципліни)
    python _tools/grades.py set ТВО 92                    підсумкова оцінка з відомості (100-бальна) – має пріоритет
    python _tools/grades.py set ТВО --credits 5            кредити ЄКТС дисципліни (з силабусу)
    python _tools/grades.py                               звіт: таблиця + середній і зважений за кредитами бал

Дані – _grades/grades.json; звіт також записується в _grades/Оцінки.md.
Середній бал = середнє арифметичне підсумкових (100-бальних) оцінок; зважений = Σ(оцінка·кредити) / Σ кредити.
Дисципліни без підсумку рахуються за поточним балом Moodle лише як «прогноз» (окремий рядок).
"""
import argparse
import json
import os
import re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, '_grades', 'grades.json')
WORKS = os.path.join(ROOT, '_calendar', 'works.json')
# шкала ХНУРЕ (типова для ЗВО України): бали -> національна / ЄКТС
SCALE = [(96, 'відмінно', 'A'), (90, 'відмінно', 'B'), (75, 'добре', 'C'), (66, 'задовільно', 'D'),
         (60, 'задовільно', 'E'), (35, 'незадовільно', 'FX'), (0, 'незадовільно', 'F')]


def scale(points):
    return next((nat, ects) for lo, nat, ects in SCALE if points >= lo)


def num(text):
    m = re.search(r'-?\d+(?:[.,]\d+)?', text or '')
    return float(m.group().replace(',', '.')) if m else None


def load():
    if os.path.exists(DATA):
        return json.load(open(DATA, encoding='utf-8'))
    data = {'disciplines': {}}
    if os.path.exists(WORKS):  # кредити й курси – з works.json, якщо там є
        for d in json.load(open(WORKS, encoding='utf-8'))['disciplines']:
            m = re.search(r'id=(\d+)', d.get('dl') or '')
            data['disciplines'][d['key']] = {'name': d['name'], 'course_id': m and m.group(1),
                                             'credits': d.get('credits'), 'final': None, 'moodle': None}
    return data


def save(data):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def import_moodle(data, path):
    snap = json.load(open(path, encoding='utf-8'))
    by_course = {v.get('course_id'): k for k, v in data['disciplines'].items()}
    for cid, course in snap['courses'].items():
        key = by_course.get(cid)
        if not key:
            print(f'курс {cid} ({course["title"]}) не прив\'язаний до дисципліни – пропущено')
            continue
        total = next((i for i in course['items'] if i['total']), None)
        g, rng = (num(total['grade']), total['range']) if total else (None, '')
        top = max((num(x) or 0 for x in re.split(r'[–-]', rng)), default=0) if rng else 0
        items = [{'name': i['name'], 'grade': i['grade'], 'range': i['range']} for i in course['items']
                 if not i['total'] and num(i['grade']) is not None]
        data['disciplines'][key]['moodle'] = {
            'total': g, 'max': top or None, 'percent': round(100 * g / top, 1) if g is not None and top else None,
            'items': items, 'fetched': snap['fetched'][:10]}
        print(f'{key}: поточний бал Moodle {g if g is not None else "–"}' + (f' з {top:g}' if top else '') +
              f', оцінених елементів {len(items)}')


def report(data):
    lines = [f'# Оцінки ({date.today():%d.%m.%Y})', '',
             '| Дисципліна | Кредити | Підсумок | Шкала | Поточний бал Moodle | Оцінені елементи |', '|---|---|---|---|---|---|']
    fin, cur = [], []
    for key, d in data['disciplines'].items():
        m = d.get('moodle') or {}
        final = d.get('final')
        nat = '{} / {}'.format(*scale(final)) if final is not None else '–'
        moodle = f"{m['total']:g} з {m['max']:g} ({m['percent']:g} %)" if m.get('percent') is not None else '–'
        credits = f"{d['credits']:g}" if d.get('credits') else '?'
        final_s = f'{final:g}' if final is not None else '–'
        lines.append(f"| {key} | {credits} | {final_s} | {nat} | {moodle} | {len(m.get('items', []))} |")
        if final is not None:
            fin.append((final, d.get('credits')))
        elif m.get('percent') is not None:
            cur.append((m['percent'], d.get('credits')))

    def avg(pairs):
        if not pairs:
            return '–', '–'
        plain = sum(g for g, _ in pairs) / len(pairs)
        cr = [(g, c) for g, c in pairs if c]
        weighted = sum(g * c for g, c in cr) / sum(c for _, c in cr) if cr and len(cr) == len(pairs) else None
        return f'{plain:.2f}', (f'{weighted:.2f}' if weighted is not None else 'бракує кредитів')

    a, w = avg(fin)
    lines += ['', f'**Середній бал (підсумкові оцінки, {len(fin)} дисц.):** {a} · **зважений за кредитами:** {w}']
    if cur:
        a2, w2 = avg(fin + cur)
        lines.append(f'Прогноз з урахуванням поточних балів Moodle ({len(cur)} дисц. без підсумку, у %): {a2} · зважений: {w2}')
    lines += ['', 'Поточний бал Moodle («Загальне за курс») – не підсумкова оцінка: Moodle зазвичай рахує його лише з уже',
              'оцінених елементів (два тести на 10/10 дають 100 %), а частину балів (захисти, іспит, залік) викладачі',
              'ставлять поза LMS. Підсумкову оцінку з відомості вносити: `python _tools/grades.py set <ДИСЦ> <бали>`.',
              'Оцінки окремих робіт – у `_grades/grades.json` (поле moodle.items).']
    text = '\n'.join(lines) + '\n'
    open(os.path.join(ROOT, '_grades', 'Оцінки.md'), 'w', encoding='utf-8').write(text)
    print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', nargs='?', default='report', choices=['report', 'import', 'set'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--credits', type=float)
    a = ap.parse_args()
    data = load()
    if a.cmd == 'import':
        import_moodle(data, a.args[0])
    elif a.cmd == 'set':
        key = a.args[0]
        d = data['disciplines'].setdefault(key, {'name': key, 'credits': None, 'final': None, 'moodle': None})
        if len(a.args) > 1:
            d['final'] = float(a.args[1])
        if a.credits is not None:
            d['credits'] = a.credits
    save(data)
    report(data)


main()
