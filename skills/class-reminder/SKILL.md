---
name: class-reminder
description: Нагадувач про пари для Windows – вікно поверх усіх за 5 хв до кожного заняття (дисципліна, вид, час) і одразу після ввімкнення ПК, якщо пара ще йде; не зникає, доки не натиснути «Закрити». Встановити, оновити розклад, змінити виключені дисципліни, з'ясувати, чому немає сповіщення, видалити.
---

# Нагадувач про пари

`A` = `%USERPROFILE%\.claude\skills\class-reminder\assets`. Встановлюється в `%USERPROFILE%\ClassReminder`,
запускається завданням Планувальника **ClassReminder** при вході в систему.

- **Встановити / оновити:** розклад воркспейсу (`_calendar/schedule.json`, з `_tools/timetable/*.py`) →
  `powershell -NoProfile -ExecutionPolicy Bypass -File A\install.ps1 -Schedule <воркспейс>\_calendar\schedule.json -Skip ФВ`
  (`-Skip` – абревіатури без нагадувань). Повторний запуск безпечний.
- **Немає сповіщення:** процес –
  `Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ? CommandLine -like '*ClassReminder*'`;
  `Get-ScheduledTaskInfo ClassReminder`; перезапуск – `Start-ScheduledTask ClassReminder`. Не запускати
  reminder.ps1 напряму із сесії Claude (процес закриється разом із застосунком) і не класти файли в AppData
  (застосунок Claude пакетний – ці записи невидимі решті Windows). Наявність файлів перевіряти з реального термінала
  (run_in_terminal), не з shell сесії.
- **Видалити:** `Unregister-ScheduledTask ClassReminder -Confirm:$false`, зупинити процес, видалити теку.
