from datetime import date, datetime, timedelta
import sys
from pathlib import Path
import json

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from scores.get_scores import score_all_games
from save_load import load_scores, save_scores

def update_scores():
    #Get today's date
    today = date.today()
    start_str = today.strftime("%m/%d/%Y")
    #Specify how many days we're going to update
    end_date = today + timedelta(days=14)
    end_str = end_date.strftime("%m/%d/%Y")
    #Get a list to keep any scores that are before today so they don't get updated
    kept_scores = []
    #Load current scores from game_scores.json
    all_scores = load_scores()

    #For each date in the .json file, if the game date is before today, then add it to kept scores.
    for entry in all_scores:
        #Get gamedate for this date in game_scores.json, then get it as a string
        gamedate = entry.get("gamedate")
        gamedate_str = datetime.strptime(gamedate, "%m/%d/%Y").date()

        #If this gamedate is before today, add this date to kept_scores
        if gamedate_str < today or gamedate_str > end_date:
            kept_scores.append(entry)

    #Save the scores we're keeping back to the .json file. All scores between today and end date
    #get removed
    save_scores(kept_scores)

    #Reset lineups.json to a blank file to clear out the lineups for yesterday's games
    with open("scores/lineups.json", "w", encoding="utf-8") as f:
        json.dump({"date": None, "games": {}}, f, indent=4)

    #Run get all scores for the specified date range
    score_all_games(start_str, end_str)

update_scores()
