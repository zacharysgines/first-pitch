from datetime import date
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from GetScores import ScoreGames
from scores.lineups import LineupsChanged
import statsapi

def check_lineups():
    today = date.today()
    gamedate = today.strftime("%m/%d/%Y")
    games = statsapi.schedule(date=gamedate)

    if not games:
        return []
    
    rs_games = False
    for game in games:
        if game['game_type'] == 'R':
            rs_games = True
            break
    if rs_games == False:
        return []

    if LineupsChanged(games):
        print("Lineups have changed. Rerunning current days games.")
        ScoreGames(gamedate, use_json=False)
    else:
        print("Lineups have not changed.")

check_lineups()
