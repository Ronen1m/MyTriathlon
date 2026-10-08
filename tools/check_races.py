"""Looks up Ronen Maimon's triathlon results on 4sport-live.com and writes races.json.

Runs every day on GitHub (see .github/workflows/races.yml). The app's
"Check for new races" button reads races.json and asks before adding anything.

Local test with saved pages:  python tools/check_races.py --offline debug
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

SEARCH_NAME = 'רונן מימון'
MY_NAME = 'מימון רונן'
BASE = 'https://www.4sport-live.com'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}


def get(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:  # network hiccup: wait and retry
            print('retry', url, e)
            time.sleep(5)
    raise RuntimeError('could not load ' + url)


def text(fragment):
    """Inner text of an HTML fragment, whitespace collapsed."""
    t = re.sub(r'<[^>]+>', ' ', fragment)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def cells(row_html):
    return [text(c) for c in re.findall(r'<t[dh][^>]*>([\s\S]*?)</t[dh]>', row_html)]


def parse_search(page):
    """Rows of the name search: event id, bib, time, places, event name, date."""
    out = []
    for m in re.finditer(r'<tr[^>]*onclick="goHome3\((\d+)\s*,\s*(\d+)\)"[^>]*>([\s\S]*?)</tr>', page):
        c = cells(m.group(3))
        if len(c) < 6:
            continue
        d = datetime.strptime(c[5], '%d/%m/%y').strftime('%Y-%m-%d') if re.match(r'\d\d/\d\d/\d\d$', c[5]) else ''
        out.append({'event': int(m.group(1)), 'bib': int(m.group(2)), 'name': c[0], 'total': c[1],
                    'overall': c[2], 'catPlace': c[3], 'eventName': c[4], 'date': d})
    return out


def race_type(category):
    c = category.lower()
    if 'ספרינט' in c or 'sprint' in c:
        return 'sprint'
    if 'אולימפי' in c or 'olympic' in c:
        return 'olympic'
    if 'חצי' in c or '70.3' in c or 'half' in c:
        return 'half'
    if 'מלא' in c or 'ברזל' in c or 'ironman' in c or 'full' in c:
        return 'full'
    return 'sprint'


def parse_personal(page):
    page = re.sub(r'<(script|style)[\s\S]*?</\1>', '', page)
    r = {}
    # details: מספר / שנת לידה / מקצה / קטגוריה / מועדון
    details = {}
    for lab, val in re.findall(r'class="details-label"[^>]*>([\s\S]*?)</th>\s*<th[^>]*class="details-value"[^>]*>([\s\S]*?)</th>', page):
        details[text(lab).rstrip(':')] = text(val)
    r['heat'] = details.get('מקצה', '')
    r['category'] = details.get('קטגוריה', '') or r['heat']
    club = details.get('מועדון', '')
    r['club'] = '' if club in ('', '_') else club
    m = re.search(r'result-metric__label">\s*תוצאה\s*</div>\s*<div class="result-metric__value">([^<]+)<', page)
    if m:
        r['total'] = m.group(1).strip()
    m = re.search(r'<table\s+id="PosTabe2"[^>]*>([\s\S]*?)</table>', page)
    if m:
        rows = re.findall(r'<tr>([\s\S]*?)</tr>', m.group(1))
        if len(rows) > 1:
            v = cells(rows[1])
            if len(v) >= 2:
                r['catPlace'], r['overall'] = v[0], v[1]
    legs = {}
    for title, tm, pos in re.findall(r'triathlon-title">\s*([^<]+?)\s*</div>\s*<div class="triathlon-pill triathlon-pill--time">\s*([^<]*?)\s*</div>\s*<div class="triathlon-pill triathlon-pill--pos">\s*([^<]*?)\s*</div>', page):
        legs[title.strip().lower()] = (tm, pos)
    for lab, tm, pos in re.findall(r'triathlon-transition-label">\s*([^<]+?):?\s*</span>\s*<span class="triathlon-transition-value">\s*([^<]*?)\s*</span>\s*<span class="triathlon-transition-pos">\s*([^<]*?)\s*</span>', page):
        legs[lab.strip().rstrip(':').lower()] = (tm, pos)
    r['legs'] = [[k, legs[k][0], legs[k][1]] for k in ('swim', 't1', 'bike', 't2', 'run') if k in legs and legs[k][0]]
    # checkpoints: the first splits table (the page repeats it for mobile)
    m = re.search(r'<table\s+class="WholeTable[^"]*splits-table"[^>]*>([\s\S]*?)</table>', page)
    if m:
        r['splits'] = [c for c in (cells(x) for x in re.findall(r'<tr>([\s\S]*?)</tr>', m.group(1).split('</thead>')[-1])) if len(c) == 4]
    m = re.search(r'<table\s+id="competitorsTable"[^>]*>([\s\S]*?)</table>', page)
    if m:
        riv = []
        for row in re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', m.group(1).split('</thead>')[-1]):
            c = cells(row)
            if len(c) == 4:
                club = '' if c[2] in ('', '_') else c[2]
                riv.append([c[3], club, c[1]] + ([1] if c[3] == MY_NAME else []))
        r['rivals'] = riv
    m = re.search(r'id="personalImg"[^>]*src="([^"]+)"', page)
    if m:
        r['photo'] = m.group(1)
    m = re.search(r'<source src="([^"]+\.mp4)"', page)
    if m:
        r['video'] = m.group(1)
    return r


def secs(t):
    p = [int(x) for x in t.split(':')]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def fill_t1(race):
    """Some races don't time T1 separately: show it as total minus the other parts (marked as calculated)."""
    legs = race.get('legs') or []
    keys = [l[0] for l in legs]
    if not legs or 't1' in keys or 'swim' not in keys or 'bike' not in keys or not race.get('total'):
        return
    rest = secs(race['total']) - sum(secs(l[1]) for l in legs)
    if rest <= 0:
        return
    t1 = ['t1', '%02d:%02d:%02d' % (rest // 3600, rest % 3600 // 60, rest % 60), '—', 1]
    legs.insert(keys.index('swim') + 1, t1)


def main():
    offline = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == '--offline' else None
    if offline:
        search = open(os.path.join(offline, 'search.html'), encoding='utf-8').read()
    else:
        search = get(BASE + '/results/bigSearch?search=' + urllib.parse.quote(SEARCH_NAME))
    rows = [x for x in parse_search(search) if 'טריאתלון' in x['eventName'] and x['name'] == MY_NAME]
    races = []
    for x in rows:
        url = f"{BASE}/personal/home3?event={x['event']}&bib={x['bib']}&lan=H"
        race = {'id': 'ev%d' % x['event'], 'name': x['eventName'], 'he': x['eventName'], 'date': x['date'],
                'event': x['event'], 'bib': x['bib'], 'url': url,
                'total': x['total'], 'overall': x['overall'], 'catPlace': x['catPlace']}
        try:
            if offline:
                p = os.path.join(offline, 'home3_%d.html' % x['event'])
                page = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
            else:
                page = get(url)
                time.sleep(1)
            if page:
                race.update({k: v for k, v in parse_personal(page).items() if v})
        except Exception as e:
            print('could not read', url, e)
        fill_t1(race)
        race['type'] = race_type(race.get('heat', '') + ' ' + race.get('category', ''))
        races.append(race)
        print(race['date'], race['name'], race['type'], race['total'], len(race.get('legs', [])), 'legs',
              len(race.get('splits', [])), 'splits', len(race.get('rivals', [])), 'rivals')
    if not races and not offline:
        print('no races found - keeping the previous races.json')
        return
    races.sort(key=lambda r: r['date'], reverse=True)
    out = {'source': 'https://www.4sport-live.com', 'checked': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'races': races}
    path = 'races.test.json' if offline else 'races.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('wrote', path, len(races), 'races')


if __name__ == '__main__':
    main()
