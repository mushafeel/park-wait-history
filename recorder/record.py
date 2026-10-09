"""Records Tokyo Disney Resort standby wait times every run (GitHub Actions, every 5 min).

Data source: ThemeParks.wiki live API (free, no key) — https://themeparks.wiki
Output (one CSV per park per day, wide format, Japan time):
  data/<park>/<YYYY-MM>/<YYYY-MM-DD>.csv
    time, <ride id>, <ride id>, ...
    09:05, 45, 10, D, C, ...
  values: number = posted standby wait (min); D = down; C = closed; R = refurbishment; ? = unknown
  data/<park>/rides.json maps ride id -> name.
"""
import csv
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

PARKS = {
    "tdl": "3cc919f1-d16d-43e0-8c3f-1dd269bd1a42",  # Tokyo Disneyland
    "tds": "67b290d5-3478-4f23-b601-2f8fb71ba803",  # Tokyo DisneySea
}
JST = timezone(timedelta(hours=9))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "park-wait-history/1.0 (GitHub Actions)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def encode(entity):
    status = entity.get("status")
    wait = ((entity.get("queue") or {}).get("STANDBY") or {}).get("waitTime")
    if status == "OPERATING" and isinstance(wait, (int, float)):
        return str(int(wait))
    return {"DOWN": "D", "CLOSED": "C", "REFURBISHMENT": "R"}.get(status, "?")


def record_park(park, live, now, root=ROOT):
    values, names = {}, {}
    for e in live.get("liveData", []):
        if e.get("entityType") != "ATTRACTION":
            continue
        values[e["id"]] = encode(e)
        names[e["id"]] = e.get("name", "")
    if not values or all(v in ("C", "R", "?") for v in values.values()):
        return False  # park closed: nothing worth recording

    park_dir = os.path.join(root, park)
    os.makedirs(park_dir, exist_ok=True)
    names_path = os.path.join(park_dir, "rides.json")
    known = json.load(open(names_path, encoding="utf-8")) if os.path.exists(names_path) else {}
    if any(known.get(k) != v for k, v in names.items()):
        known.update(names)
        with open(names_path, "w", encoding="utf-8") as f:
            json.dump(known, f, ensure_ascii=False, indent=1, sort_keys=True)

    day_dir = os.path.join(park_dir, now.strftime("%Y-%m"))
    os.makedirs(day_dir, exist_ok=True)
    path = os.path.join(day_dir, now.strftime("%Y-%m-%d") + ".csv")
    header, rows = ["time"], []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            r = list(csv.reader(f))
        if r:
            header, rows = r[0], r[1:]
    stamp = now.strftime("%H:%M")
    if rows and rows[-1][0] == stamp:
        return False  # already recorded this minute
    new_ids = [k for k in values if k not in header]
    if new_ids:
        header = header + new_ids
        rows = [row + [""] * (len(header) - len(row)) for row in rows]
    rows.append([stamp] + [values.get(k, "") for k in header[1:]])
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([header] + rows)
    return True


def main():
    now = datetime.now(JST)
    wrote = False
    for park, entity_id in PARKS.items():
        try:
            live = get_json(f"https://api.themeparks.wiki/v1/entity/{entity_id}/live")
            wrote |= record_park(park, live, now)
        except Exception as exc:  # one park failing shouldn't stop the other
            print(f"{park}: {exc}", file=sys.stderr)
    print("recorded" if wrote else "nothing to record")


if __name__ == "__main__":
    main()
