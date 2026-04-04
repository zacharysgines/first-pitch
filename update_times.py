import json
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

import statsapi


ROOT = Path(__file__).resolve().parent
GAME_SCORES_PATH = ROOT / "game_scores.json"


def load_scores():
    with GAME_SCORES_PATH.open("r", encoding="utf-8") as handle:
        raw_text = handle.read().strip()
    return json.loads(raw_text) if raw_text else []


def save_scores(saved_scores):
    with GAME_SCORES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(saved_scores, handle, indent=2)


def schedule_lookup_for_date(gamedate):
    schedule_games = statsapi.schedule(date=gamedate)
    lookup = defaultdict(list)

    for game in schedule_games:
        if game.get("game_type") != "R":
            continue
        key = (game.get("away_name"), game.get("home_name"))
        game_datetime = game.get("game_datetime")
        if key[0] and key[1] and game_datetime:
            lookup[key].append(game_datetime)

    return lookup


def update_entry(entry):
    gamedate = entry.get("gamedate")
    if not gamedate:
        return 0, 0

    lookup = schedule_lookup_for_date(gamedate)
    updated_games = 0
    missing_games = 0

    for game in entry.get("games", []):
        key = (game.get("away_team_name"), game.get("home_team_name"))
        matching_datetimes = lookup.get(key)
        if matching_datetimes:
            game["game_datetime"] = matching_datetimes.pop(0)
            game.pop("status", None)
            updated_games += 1
        else:
            missing_games += 1

    return updated_games, missing_games


def should_update_entry(entry, today):
    gamedate = entry.get("gamedate")
    if not gamedate:
        return False

    try:
        game_date = datetime.strptime(gamedate, "%m/%d/%Y").date()
    except ValueError:
        return False

    if game_date.year not in {today.year, today.year - 1}:
        return False

    return game_date <= today


def main():
    today = date.today()
    saved_scores = load_scores()

    updated_entries = 0
    updated_games = 0
    missing_games = 0

    for entry in saved_scores:
        if not should_update_entry(entry, today):
            continue

        entry_updated_games, entry_missing_games = update_entry(entry)
        if entry_updated_games or entry_missing_games:
            updated_entries += 1
            updated_games += entry_updated_games
            missing_games += entry_missing_games

    save_scores(saved_scores)
    print(
        f"Updated {updated_games} games across {updated_entries} dates. "
        f"Missing matches: {missing_games}."
    )


if __name__ == "__main__":
    main()

