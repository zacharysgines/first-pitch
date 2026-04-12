from datetime import date
import sys
from pathlib import Path
import statsapi

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from scores.get_scores import UpdateScores
from scores.lineups import LineupsChanged

def check_lineups():
    #Get todays date as an object
    today = date.today()
    today_str = today.strftime("%m/%d/%Y")

    #Get all the games for today
    games = statsapi.schedule(date=today_str)

    #If there are no games, don't do anything
    if not games:
        return []
    
    #If none of the games today are regular season games, don't do anything
    rs_games = False
    for game in games:
        if game['game_type'] == 'R':
            rs_games = True
            break
    if rs_games == False:
        return []

    #If there are games today, run LineupsChanged() to see if any of the lineups have changed. If they have, run UpdateScores with the list of games that have changed.
    games_to_update = LineupsChanged(games, today_str)
    if games_to_update:
        print("Lineups have changed. Updating current days games.")
        UpdateScores(today_str, games, games_to_update)
    else:
        print("Lineups have not changed.")

check_lineups()