"""Розкласти файли, скачані moodle_resources.js, з «Завантажень» у materials дисципліни.

    python _tools/lms/place_downloads.py <ПРЕФІКС> <тека>/materials [--downloads ШЛЯХ]

Файл <ПРЕФІКС>__<cmid>__<назва> потрапляє в <тека>/materials/_нерозібрані/<назва>; далі агент розкладає їх по
«методички і завдання» / «лекції» / «програма і силабус» і дає зрозумілі назви (АКТУАЛЬНА / застаріла).
Довгі назви скорочуються (обмеження шляху Windows).
"""
import argparse
import os
import re
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prefix')
    ap.add_argument('dest')
    ap.add_argument('--downloads', default=os.path.join(os.path.expanduser('~'), 'Downloads'))
    a = ap.parse_args()
    out = os.path.join(a.dest, '_нерозібрані')
    os.makedirs(out, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(a.downloads)):
        m = re.match(rf'^{re.escape(a.prefix)}__(\d+)__(.+)$', f)
        if not m:
            continue
        stem, ext = os.path.splitext(m.group(2))
        name = (stem[:80] + ext) if len(stem) > 80 else m.group(2)
        shutil.move(os.path.join(a.downloads, f), os.path.join(out, name))
        print(f'{m.group(1)} -> {name}')
        n += 1
    print(f'{n} файлів -> {out}')


main()
