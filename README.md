# ⚽ Football Data Analytics & Visualisation

Football data projects in Python: collecting raw match data, parsing & cleaning it, and turning it into publication-ready visuals.

> Click a project name below to jump to its folder.

## Projects

| # | Project | Focus |
|---|---------|-------|
| 1 | [Sofascore: UCL 2025/26 Shot Maps](Sofascore) | Self-built API wrapper, xG cluster analysis and  shot maps |
| 2 | [Understat](Understat) | Quick analysis on already-available data |

---

## 1. [Sofascore](Sofascore): UCL 2025/26 Shot Maps

[![Bellingham UCL 2025/26 shot map](Sofascore/Shotmap%20UCL.2025-26/Bellingham_ucl_shotmap.png)](Sofascore/Shotmap%20UCL.2025-26/Bellingham_ucl_shotmap.png)
           
A complete pipeline, from finding the data source to publishing the visual as the viz so created above: I located Sofascore's APIs, which pointed towards several dataset endpoints such as goals, Xg, shots, Minutes played etc,  wrapped it into a reusable Python module, converted its coordinates adjusted to data pitch size, and plotted holistic dynamic shot maps. It started as a single **Bellingham / Real Madrid** visual and grew into a **player-configurable tool** [Shotmap UCL 2025-26](Sofascore/shotmap.ipynb) where you can just type players accurate name and code just seemingly generates shotmap for the entire season real time.

The visual style is inspired by Opta-style shot maps. The **whole pipeline behind it** (data discovery, wrapper, parsing, coordinate conversion and plotting) is self built and designed.

**Jump to:** [How the data works](#-how-sofascore-keeps-its-data) · [Finding the API](#-finding-the-api) · [The wrapper](#-the-wrapper-sofascoreapipy) · [Data flow](#-from-request-to-plot) · [Files](#-files-in-this-folder) · [Run it](#-run-it) · [Journey](#-the-journey)

### ✨ What it does

- 🎯 xG-based color gradient so shot quality is visible at a glance
- 🧱 Blocked shots drawn with T-bar tick marks
- 🔄 Converts Sofascore coordinates to the StatsBomb 120×80 pitch
- 🪪 Resolves player IDs automatically from a name
- 📅 Collects matches round by round (group stage) and page by page (knockouts)
- 🏷️ Adds club logos with PIL
- 🐦 Exports in Twitter/X-optimized sizing

### 🛠️ Tech stack

`Python` · `requests` · `pandas` · `mplsoccer` · `Matplotlib` · `Pillow` · `Selenium` · `Playwright` · `dnspython`

---

### 🌐 How Sofascore keeps its data

Sofascore's website is a front end. Every page you see (a match, a team, a player) is filled in by **JSON requests sent to an internal API** behind the scenes. Open a match page and the browser quietly asks that API for the shotmap, lineups, statistics and incidents, then draws them as the page you see.

That means the real data is already structured and sitting at predictable URLs like:

```text
https://www.sofascore.com/api/v1/event/{match_id}/shotmap
https://www.sofascore.com/api/v1/team/{team_id}/players
https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/standings/total
```

There is no public documentation for it, so the job was to **find out what the site itself asks for**.

### 🔎 Finding the API

1. **Capture the traffic.** I loaded Sofascore pages through an automated Chrome (Selenium with the Chrome DevTools Protocol) and logged every network request the page made.
2. **Untangle the log.** A page makes hundreds of requests (images, ads, trackers). I filtered the capture down to the ones returning JSON from the `/api/v1/` path.
3. **Map IDs to endpoints.** Each endpoint takes an ID that can be read straight from a Sofascore page URL (match, team, player, tournament, season).
4. **Wrap them.** Once the useful endpoints were known, I turned them into clean reusable code, so there is no browser needed at runtime.

The exploration lives in [`APIfinder.ipynb`](Sofascore/APIfinder.ipynb).

**When the site changed.** Chrome 115+ silently deprecated the `goog:loggingPrefs` performance logging I relied on, and Sofascore began returning **403 errors to headless browsers**. The fix was to use a **real browser's DevTools Network tab**, export a **HAR** file, and parse it in Python to recover the endpoints.

**If the API changes again, you can redo this yourself:** open a Sofascore page, press `F12`, go to the **Network** tab, filter by `Fetch/XHR`, and watch the `/api/v1/` calls appear. Copy the new URL pattern into the wrapper. The wrapper also has `test_endpoints()`, a built-in check that tells you exactly which endpoints still work.

---

### 📦 The wrapper: [`sofascoreapi.py`](Sofascore/sofascoreapi.py)

A small, self-written module that turns those hidden endpoints into plain Python classes. All of them go through one shared `_fetch()` function, so a broken endpoint gives a clear error with the URL and status code.

| Class | What it gives you | Example methods |
|-------|-------------------|-----------------|
| `MatchStats(match_id)` | Everything about one match | `get_shotmap()`, `get_lineups()`, `get_statistics()`, `get_incidents()`, `get_average_positions()`, `get_all()` |
| `League(tournament_id, season_id)` | A competition season | `get_standings()`, `get_top_players()`, `get_top_teams()`, `get_all_scorers()`, `get_matches(round)` |
| `Team(team_id)` | A club | `get_info()`, `get_squad()`, `get_season_stats()`, `get_season_matches()` |
| `Player(player_id)` | One player | `get_info()`, `get_season_stats()`, `get_heatmap()` |

Helpers: `pretty_print()` (explore raw JSON), `list_tournaments()` (built-in tournament IDs) and `test_endpoints()` (health check).

```python
from sofascoreapi import MatchStats, League, Team, Player

match = MatchStats("15452752")
shots = match.get_shotmap()                 # raw JSON for one match

team = Team("1644")                         # PSG
matches = team.get_season_matches("7", "76953")   # every finished UCL match
```

`get_season_matches()` pages through a team's full match history and filters by tournament and season, so **group stage and knockout matches come back in one list**, ready to feed into `MatchStats`.

> **Note:** the module also patches DNS resolution with `dnspython` at the top of the file, because some ISPs block Sofascore's hostname. If you don't have that issue, you can remove that block.

---

### 🔁 From request to plot

```text
Sofascore API ──► requests (sofascoreapi.py) ──► raw JSON
                                                    │
                                    parse + filter (player, shot type, match)
                                                    │
                                              pandas DataFrame
                                                    │
                           coordinate conversion (Sofascore → StatsBomb 120×80)
                                                    │
                       mplsoccer pitch + xG colors + blocked-shot T-bars + logos
                                                    │
                                        Twitter/X-optimized export
```

1. **Request:** `MatchStats(...).get_shotmap()` returns raw JSON.
2. **Parse and filter:** pull out the shot list, then keep only the player and shots you want.
3. **DataFrame:** one row per shot, with position, xG, outcome and shot type.
4. **Convert:** map Sofascore's pitch coordinates onto StatsBomb's 120×80 system so mplsoccer draws them correctly.
5. **Plot and export:** color by xG, mark blocked shots, add logos, save at social-media size.

---

### 📂 Files in this folder

| File / folder | What it is |
|---------------|------------|
| [`shotmap.ipynb`](Sofascore/shotmap.ipynb) | ⭐ **Main shot map script** (reusable, player-configurable) |
| [`sofascoreapi.py`](Sofascore/sofascoreapi.py) | The self-built API wrapper |
| [`APIfinder.ipynb`](Sofascore/APIfinder.ipynb) | API discovery notebook |
| [`Mbappeshotmap.ipynb`](Sofascore/Mbappeshotmap.ipynb) | First version: Mbappé / Real Madrid |
| [`sofascoretesting.ipynb`](Sofascore/sofascoretesting.ipynb) | Testing the wrapper |
| [`ucl25-26 (1).ipynb`](Sofascore/ucl25-26%20%281%29.ipynb) | UCL 2025/26 analysis |
| [`Shotmap UCL.2025-26/`](Sofascore/Shotmap%20UCL.2025-26) | Generated shot map images |
| [`Logo/`](Sofascore/Logo) | Club logos used on the maps |
| [`ucl_finishers.PNG`](Sofascore/ucl_finishers.PNG) | UCL 2025/26 finishers visual citing over and underperformance from Goal and Xg differences  |



🚀 Run it

```bash
git clone https://github.com/prajwalsigdel7/Football-Data-Analytics.git
cd Football-Data-Analytics
conda env create -f Footballenv_clean.yml
conda activate Footballenv
```

Then open [`Sofascore/shotmap.ipynb`](Sofascore/shotmap.ipynb), set the player and match, and run all cells.

### 💡 Lessons learned

- A website's own network traffic is the best documentation when there is no official API.
- Headless scraping is fragile; a real browser's HAR export is the dependable way to rediscover endpoints.
- Always verify an endpoint yourself in DevTools before building on it.
- A built-in `test_endpoints()` check turns "something broke" into "this exact endpoint broke".
- Reusable config (one player variable) saves far more time than polishing a one-off chart.

---

## 2. [Understat](Understat)

A simple analysis on data that was already available. Kept as a lightweight companion to the Sofascore project.

---

## 📁 Repo structure

```text
Football-Data-Analytics/
├── Sofascore/
│   ├── Logo/                     # club logos
│   ├── Shotmap UCL.2025-26/      # generated shot maps
│   ├── APIfinder.ipynb           # API discovery
│   ├── Mbappeshotmap.ipynb       # first version
│   ├── shotmap.ipynb             # main shot map script
│   ├── sofascoreapi.py           # self-built API wrapper
│   ├── sofascoretesting.ipynb
│   ├── ucl25-26 (1).ipynb
│   └── ucl_finishers.PNG
├── Understat/                    # Understat analysis
├── Footballenv_clean.yml         # Conda environment
└── README.md
```

## 👤 Author

**Prajwal Sigdel** · [GitHub](https://github.com/prajwalsigdel7)

*Data sourced from Sofascore for educational and portfolio purposes.*