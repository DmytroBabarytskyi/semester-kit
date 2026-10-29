"""kurs_crawl.json (moodle_course_crawl.js) -> читабельний зміст кожного курсу: <тека>/<id>.txt

    python _tools/lms/outline.py kurs_crawl.json <тека>
"""
import json
import os
import sys

crawl = json.load(open(sys.argv[1], encoding='utf-8'))
os.makedirs(sys.argv[2], exist_ok=True)
for cid, c in crawl.items():
    L = [f"# {c['title']} (id={cid})"]
    for s in c['sections']:
        L.append(f"\n## {s['name']}")
        if s['summary']:
            L.append('  ' + s['summary'][:2000].replace('\n', ' / '))
        L += [f"  файл: {f['t']} -> {f['h']}" for f in s['files']]
        for a in s['acts']:
            L.append(f"- [{a['type']}] {a['name']} -> {a.get('href')}" + (f" (файл: {a['direct']})" if a.get('direct') else '')
                     + (f" => {a['target']}" if a.get('target') else ''))
            if a.get('desc'):
                L.append('    опис: ' + a['desc'][:1000].replace('\n', ' / '))
            L += [f"    файл: {f['t']} -> {f['h']}" for f in a.get('files', [])]
            if a.get('page') and a['type'] in ('page', 'assign', 'quiz', 'book', 'folder'):
                L.append('    сторінка: ' + a['page'][:3000].replace('\n', ' / '))
    path = os.path.join(sys.argv[2], f'{cid}.txt')
    open(path, 'w', encoding='utf-8').write('\n'.join(L))
    print(path)
