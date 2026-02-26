import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCORES_FILE = ROOT_DIR / "game_scores.json"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import GetAllScores


def _parse_gamedate(gamedate):
    return datetime.strptime(gamedate, "%m/%d/%Y").date()


def remove_today_or_later(scores_file, today):
    if not scores_file.exists():
        return 0, 0

    with scores_file.open("r", encoding="utf-8") as f:
        all_scores = json.load(f)

    kept_scores = []
    removed_count = 0

    for entry in all_scores:
        gamedate_str = entry.get("gamedate")
        try:
            gamedate = _parse_gamedate(gamedate_str)
        except (TypeError, ValueError):
            kept_scores.append(entry)
            continue

        if gamedate < today:
            kept_scores.append(entry)
        else:
            removed_count += 1

    with scores_file.open("w", encoding="utf-8") as f:
        json.dump(kept_scores, f, indent=2)

    return removed_count, len(kept_scores)


def main():
    today = date.today()
    end_of_year = date(today.year, 12, 31)

    removed_count, remaining_count = remove_today_or_later(SCORES_FILE, today)
    print(
        f"Removed {removed_count} date entries from {today.strftime('%m/%d/%Y')} onward. "
        f"{remaining_count} date entries remain."
    )

    start_str = today.strftime("%m/%d/%Y")
    end_str = end_of_year.strftime("%m/%d/%Y")
    print(f"Rebuilding scores from {start_str} through {end_str}...")
    GetAllScores(start_str, end_str)
    print("Update complete.")


if __name__ == "__main__":
    main()
