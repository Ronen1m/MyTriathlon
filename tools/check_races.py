"""Debug pass: download the 4sport pages so their HTML structure can be inspected."""
import os, urllib.request, urllib.parse
os.makedirs('debug', exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'ERROR ' + repr(e)
q = urllib.parse.quote('רונן מימון')
pages = {
  'search.html': f'https://www.4sport-live.com/results/bigSearch?search={q}',
  'home2_4017.html': f'https://www.4sport-live.com/results/home2?event=4017&lan=H&search={urllib.parse.quote("מימון")}',
  'home3_3952.html': 'https://www.4sport-live.com/personal/home3?event=3952&bib=2585&lan=H',
}
for name, url in pages.items():
    open(os.path.join('debug', name), 'w', encoding='utf-8').write(get(url))
    print(name, os.path.getsize(os.path.join('debug', name)))
