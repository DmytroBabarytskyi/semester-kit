---
name: semester-sync
description: Синхронізувати навчальний воркспейс з LMS (Moodle) – дедлайни, статуси здачі, нові завдання, оцінки – і перебудувати календар здачі, таблиці «Стан» та звіт оцінок. Використовувати на «онови з DL/Moodle», «що нового», «синхронізуй», перед плануванням тижня і перед роботою над завданням.
---

# Синхронізація з LMS

Воркспейс з `_profile.json` (інакше – `/semester-init`). Браузер – Claude in Chrome. Курси – з полів `dl`
у `_calendar/works.json`.

1. Вкладка на `<lms_url>/my/courses.php`. Сторінка входу → попросити студента увійти (пароль не вводити).
   «Let's confirm you are human» → попросити пройти перевірку. Не обходити.
2. **Дедлайни і статуси:** `_tools/lms/moodle_overview.js` (вписати COURSES) через `javascript_tool`; не
   навігувати вкладку; кожні ~10 с `window.__kurs.status` до `done`. Файл
   `%USERPROFILE%\Downloads\kurs_overview.json` → `_calendar/`; `python _tools/lms/apply_overview.py
   _calendar/kurs_overview.json`. Нові завдання з виводу: робота студента → дописати у works.json; чужа група /
   службове → `ignore_cmids`. Спільне завдання на кілька робіт → спитати, що саме здано.
   Потребує Moodle зі сторінкою «Огляд діяльності» (course/overview.php, Moodle 4.5+/5.x); якщо її немає –
   прочитати сторінки завдань курсу й оновити works.json вручну.
3. **Оцінки:** `_tools/lms/moodle_grades.js` (ті самі COURSES) → `moodle_grades.json` → `python _tools/grades.py
   import <файл>`. Кредити дисциплін – `grades.py set <ДИСЦ> --credits N` (з силабусу), підсумкові оцінки з
   відомості – `grades.py set <ДИСЦ> <бали>` (лише зі слів студента).
4. `python _tools/state_tables.py`; `python _calendar/build_calendar.py`.
5. Коротко: що змінилось (дедлайни, статуси, нові завдання, нові оцінки), найближчі дедлайни, прострочене.
