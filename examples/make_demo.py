"""Демо-воркспейс на вигаданих даних (для README і для того, щоб подивитися, як виглядає результат).

    python examples/make_demo.py      -> examples/demo/ (calendar.html, calendar.ics, _grades/Оцінки.md, ...)

Студент, дисципліни, роботи й оцінки – вигадані. Дати відраховуються від сьогодні, щоб у календарі було видно
«цей тиждень», «через N дн.» і прострочене.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEMO = os.path.join(HERE, 'demo')
WS = os.path.join(REPO, 'skills', 'semester-init', 'assets', 'workspace')

COURSES = [  # ключ, назва, тека, день тижня (0 = пн), пара, кредити, роботи [(id, тема, issued)]
    ('АСД', 'Алгоритми та структури даних', 'АСД', 0, '09:30', 5,
     [('ЛБ1', 'Сортування: порівняльний аналіз', 1), ('ЛБ2', 'Хеш-таблиці', 2), ('ЛБ3', 'Графи: найкоротші шляхи', 3),
      ('ЛБ4', 'Динамічне програмування', 4)]),
    ('БД', 'Організація баз даних', 'БД', 2, '11:15', 4,
     [('ПЗ1', 'ER-модель предметної області', 1), ('ПЗ2', 'Нормалізація до 3НФ', 2), ('ПЗ3', 'SQL-запити і представлення', 3),
      ('Курсова', 'Курсова робота: БД інтернет-магазину', None)]),
    ('ВЕБ', 'Вебтехнології', 'ВЕБ', 3, '14:55', 4,
     [('ПЗ1', 'Адаптивна верстка', 1), ('ПЗ2', 'REST API на FastAPI', 2), ('ПЗ3', 'Клієнт на React', 3)]),
]


def main():
    if os.path.exists(DEMO):
        shutil.rmtree(DEMO)
    shutil.copytree(os.path.join(WS, '_calendar'), os.path.join(DEMO, '_calendar'))
    shutil.copytree(os.path.join(WS, '_tools'), os.path.join(DEMO, '_tools'))
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    json.dump({'pib': 'Коваленко Олена Ігорівна', 'title_name': 'КОВАЛЕНКО О. І.', 'surname': 'Коваленко',
               'group': 'КН-23-2', 'variant': 7, 'university': 'Національний університет «Приклад»',
               'department': 'Кафедра програмної інженерії', 'city': 'Київ', 'year': today.year,
               'semester': 'III курс, 1 семестр', 'lms_url': 'https://lms.example.edu.ua'},
              open(os.path.join(DEMO, '_profile.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    schedule, disciplines = [], []
    for key, name, folder, wd, start, credits, works in COURSES:
        first = monday - timedelta(weeks=5) + timedelta(days=wd)  # заняття раз на 2 тижні, 5 тижнів тому – перше
        for i in range(8):
            day = first + timedelta(weeks=2 * i)
            hh, mm = map(int, start.split(':'))
            end = (datetime(2000, 1, 1, hh, mm) + timedelta(minutes=95)).strftime('%H:%M')
            schedule.append({'start': f'{day}T{start}', 'end': f'{day}T{end}', 'abbr': key, 'name': name,
                             'kind': 'Практика', 'raw': key})
        items = []
        for wid, title, issued in works:
            items.append({'id': wid, 'title': title, 'issued': issued, 'dl': None, 'status': 'todo',
                          'url': 'https://lms.example.edu.ua/mod/assign/view.php?id=0',
                          **({'defense': False, 'dl': f'{monday + timedelta(weeks=7, days=4)}T23:59',
                              'note': 'Терміни – у бланку завдання від керівника'} if issued is None else {})})
        disciplines.append({'key': key, 'name': name, 'folder': folder, 'schedule_abbr': key, 'credits': credits,
                            'dl': 'https://lms.example.edu.ua/course/view.php?id=0', 'works': items})
        os.makedirs(os.path.join(DEMO, folder), exist_ok=True)
        open(os.path.join(DEMO, folder, 'CLAUDE.md'), 'w', encoding='utf-8').write(
            f'# {key} – {name}\n\nLMS: курс у Moodle · {credits} кредити ЄКТС · залік.\n\n'
            '## Оцінювання\n\n(вигаданий приклад) Семестр = Σ балів за роботи, ≥ 60; роботи захищаються.\n\n'
            '## Стан\n\n<!-- kurs:state -->\n<!-- /kurs:state -->\n')
    disciplines[0]['works'][0]['status'] = 'defended'
    disciplines[0]['works'][1]['dl'] = f'{monday + timedelta(days=1)}T23:59'
    disciplines[1]['works'][0]['status'] = 'submitted'
    disciplines[2]['works'][0]['status'] = 'submitted'
    json.dump(schedule, open(os.path.join(DEMO, '_calendar', 'schedule.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump({'updated': str(today), 'rule': 'Робота, видана на занятті N, здається до початку заняття N+1 і на ньому '
               'захищається. Якщо в LMS є свій дедлайн – береться раніший з двох.', 'disciplines': disciplines},
              open(os.path.join(DEMO, '_calendar', 'works.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    py = [sys.executable, '-X', 'utf8']
    subprocess.run(py + [os.path.join(DEMO, '_calendar', 'build_calendar.py')], check=True)
    subprocess.run(py + [os.path.join(DEMO, '_tools', 'state_tables.py')], check=True, stdout=subprocess.DEVNULL)
    for key, *_ , credits, _w in COURSES:
        subprocess.run(py + [os.path.join(DEMO, '_tools', 'grades.py'), 'set', key, '--credits', str(credits)],
                       check=True, stdout=subprocess.DEVNULL)
    subprocess.run(py + [os.path.join(DEMO, '_tools', 'grades.py'), 'set', 'АСД', '94'], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(py + [os.path.join(DEMO, '_tools', 'grades.py'), 'set', 'БД', '81'], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(py + [os.path.join(DEMO, '_tools', 'grades.py'), 'set', 'ВЕБ', '88'], check=True, stdout=subprocess.DEVNULL)
    shutil.rmtree(os.path.join(DEMO, '_tools'))  # у демо лише результат; інструменти – у skills/
    print('demo ->', DEMO)


main()
