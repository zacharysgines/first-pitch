from datetime import date, datetime, timedelta
import sys
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from GetScores import GetAllScores
from SaveLoad import LoadScores, SaveScores

def update_scores():
    today = date.today()
    end_date = today + timedelta(days=14)
    kept_scores = []
    
    all_scores = LoadScores()

    for entry in all_scores:
        gamedate = entry.get("gamedate")
        gamedate_obj = datetime.strptime(gamedate, "%m/%d/%Y").date()

        if gamedate_obj < today:
            kept_scores.append(entry)

    SaveScores(kept_scores)

    LINEUPS_PATH = Path("scores/lineups.json")

    LINEUPS_PATH.write_text(
        json.dumps({"date": None, "games": {}}, indent=4),
        encoding="utf-8",
    )

    start_str = today.strftime("%m/%d/%Y")
    end_str = end_date.strftime("%m/%d/%Y")
    GetAllScores(start_str, end_str)

update_scores()