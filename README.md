# My Triathlon

Track how much the triathlon hobby costs — swim, bike, run and general.

**Open the app:** https://ronen1m.github.io/MyTriathlon-/ (on the phone: Share → "Add to Home Screen").

## What it does
- **Expenses tab** – add / edit / delete expenses. Each expense has an amount, date, sport (🏊 Swim, 🚴 Bike, 🏃 Run, 🏅 General), category (gear, race entry, coaching, club/pool, maintenance, nutrition, travel, health, apps, other) and notes.
- **One-time or 🔁 monthly** – a monthly expense is counted once every month from its first month until its last month (or until this month while it's still active).
- **Filters** – by year, by sport and by type. They apply to both tabs.
- **Statistics tab** – total spent, average per year (or per month for a single year), change vs. the previous year, what you're paying monthly right now, biggest purchase, spending per year (or month by month) split by sport, by sport, by category, one-time vs monthly, and top expenses. Every chart can be switched to a table.

## Your data
Everything is saved **only in the browser on that device** (localStorage). Nothing is sent anywhere.
- **💾 Backup** downloads `TriExpenses_YYYYMMDD_HHMM.json` with all expenses.
- **📂 Import** loads a backup (`.json`) or a spreadsheet (`.csv`). Only expenses that aren't already in the app are added, so importing the same file twice is safe.
- **Settings → CSV** exports everything for Excel. The CSV columns are `date,title,amount,sport,category,freq,endDate,notes,id`, which is also the format Import accepts.
- The app reminds you to back up when the last backup is more than 30 days old.

## Publishing (GitHub Pages)
Settings → Pages → Deploy from branch → `main` / root.
When you publish an update, bump `CACHE` in `sw.js` (e.g. `triexpenses-v2`).

## Files
- `index.html` – the whole app (HTML, CSS, JS in one file)
- `manifest.json`, `sw.js`, `icons/` – installable app + offline support
