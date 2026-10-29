---
name: semester-init
description: Підготувати навчальний воркспейс семестру – профіль студента, розклад, теки дисциплін з матеріалами й CLAUDE.md (оцінювання, актуальна методичка, роботи), стан робіт з LMS (Moodle), календар здачі (HTML + .ics), облік оцінок і нагадувач про пари. Використовувати на «налаштуй семестр», «/semester-init», або в порожній теці без _profile.json.
---

# Ініціалізація семестру

`A` = тека цього скіла (`%USERPROFILE%\.claude\skills\semester-init`). Воркспейс = поточна тека сесії.

## 0. Перевірки

- **Тека порожня.** Є `_profile.json` → воркспейс готовий, запропонувати `/semester-sync`. Є інші файли (CLAUDE.md,
  теки дисциплін) без профілю → зупинитися й попросити нову порожню теку. Не в `AppData` (пакетний застосунок).
- Python ≥ 3.10; `python -m pip install python-docx pymupdf openpyxl python-pptx latex2mathml lxml`.
  Microsoft Word – для PDF і рівнянь (без нього – лише .docx, попередити).
- Claude in Chrome підключений; студент залогінений у LMS. Без нього крок 4–5 пропустити й сказати.

## 1. Профіль (одне AskUserQuestion + уточнення текстом)

ПІБ; група; номер у списку групи (варіант за замовчуванням); ЗВО, кафедра (для титулу), місто; адреса LMS
(напр. `https://dl.nure.ua`); семестр (напр. «IV курс, 1 семестр (осінь 2026/27)»); чи потрібен нагадувач.
Записати `_profile.json` (UTF-8): `pib`, `title_name` («ПРІЗВИЩЕ І. Б.»), `surname`, `group`, `variant`,
`university`, `department`, `city`, `year`, `semester`, `lms_url`, `reminder`.
Якщо студент має **пакет групи** (тека або zip від одногрупника: `disciplines/`, `works.json`) – спитати шлях;
тоді кроки 4 і частина 5 беруться з пакета (див. «Пакет групи»).

## 2. Розклад

- ХНУРЕ: `TimeTable_*.xls` з cist.nure.ua → `python A/assets/workspace/_tools/timetable/cist_nure.py <xls> --list`.
- Інше: `.ics` (експорт розкладу / Google Calendar) → `python …/_tools/timetable/ics.py <ics> --list`
  (`--map "підрядок назви=АБР"` для коротких абревіатур).
Показати список, спитати, на які вибіркові / підгрупи студент **не** ходить → `--skip`; результат –
`_calendar/schedule.json` (`--out`). Немає розкладу – пропустити (календар лише за дедлайнами LMS).

## 3. Скелет

Скопіювати `A/assets/workspace/*` (`_tools/`, `_calendar/`); `_grades/` створить `grades.py`.

## 4. Дисципліни з LMS

1. Курси: `<lms>/my/courses.php` (Chrome, `find` посилань `course/view.php?id=`); спитати, які з них – цього
   семестру (минулі курси часто лишаються в списку).
2. `_tools/lms/moodle_course_crawl.js` (вписати COURSES; працює у фоні; `window.__kurs.status`) →
   `%USERPROFILE%\Downloads\kurs_crawl.json` → `python _tools/lms/outline.py kurs_crawl.json _lms/outline`.
3. Матеріали: файли LMS – `moodle_resources.js` + `place_downloads.py`; Google Drive – прямим посиланням
   `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t` (тек – перелічити файли
   на сторінці теки). Великі книги/відео – лише посилання.
4. Для кожної дисципліни – тека з коротким ім'ям (абревіатура з розкладу), `materials/` (методички і завдання /
   лекції / програма і силабус / застарілі) і `CLAUDE.md`: шапка (LMS, кредити ЄКТС, форма контролю, викладачі
   для «Прийняв»), **Оцінювання** (формула, ваги, штрафи, захист), **Яка методичка актуальна** (якщо їх кілька –
   за датою видання й відповідністю темам завдань LMS; ознаки неактуальності записати), **Роботи** (теми, зміст
   звіту, критерії), **Здача** (куди, імена файлів), блок `<!-- kurs:state -->\n<!-- /kurs:state -->`.
   Факти – лише з матеріалів; невідоме – так і писати («уточнити у викладача»).
5. `_calendar/works.json`: `{"updated", "rule", "disciplines": [{"key", "name", "folder", "schedule_abbr", "dl":
   <url курсу>, "credits", "ignore_cmids": [], "works": [{"id", "title", "issued", "dl", "status": "todo", "url",
   "note", "defense": true}]}]}`. `issued` – номер практичного/лабораторного заняття, на якому видають роботу
   (0 – до першого); робіт більше, ніж занять, – розподілити рівномірно й позначити як припущення.

## 5. Стан і оцінки

Процедура `/semester-sync` (дедлайни, статуси, оцінки), потім `python _calendar/build_calendar.py`.

## 6. CLAUDE.md і нагадувач

- Кореневий `CLAUDE.md` з `A/assets/templates/CLAUDE.md` (підставити `{{…}}` з профілю; таблиця дисциплін
  «Тека | Дисципліна | Кредити | Контроль | LMS»).
- Нагадувач (якщо треба): `powershell -NoProfile -ExecutionPolicy Bypass -File
  %USERPROFILE%\.claude\skills\class-reminder\assets\install.ps1 -Schedule _calendar\schedule.json -Skip <без нагадувань>`.

## 7. Підсумок

Що створено; 3–5 найближчих дедлайнів; що потребує рішення студента (теми проєктів, уточнення у викладачів).

## Пакет групи

Одногрупники можуть ділитися розібраними дисциплінами (приватно – там матеріали курсів і дані викладачів, **не
для публічних репозиторіїв**). Пакет: `disciplines/<тека>/` (CLAUDE.md + materials) і `works.json`. Скопіювати
потрібні теки, взяти works.json лише з обраних дисциплін, статуси скинути в `todo`; далі – `/semester-sync`.
