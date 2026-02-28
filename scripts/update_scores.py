from datetime import date, datetime, timedelta
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from main import GetAllScores, LoadScores, SaveScores
def update_scores():
    today = date.today()
    end_date = today + timedelta(days=31)
    kept_scores = []
    
    all_scores = LoadScores()

    for entry in all_scores:
        gamedate = entry.get("gamedate")
        gamedate_obj = datetime.strptime(gamedate, "%m/%d/%Y").date()

        if gamedate_obj < today:
            kept_scores.append(entry)

    SaveScores(kept_scores)

    start_str = today.strftime("%m/%d/%Y")
    end_str = end_date.strftime("%m/%d/%Y")
    GetAllScores(start_str, end_str)

update_scores()