import json
from pathlib import Path
from datetime import datetime

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
SCORES_FILE = ROOT_DIR / "scores" / "game_scores.json"
PROJECTIONS_FILE = ROOT_DIR / "records" / "projected_records.csv"
LINEUPS_FILE = ROOT_DIR / "lineups" / "lineups.json"
WIN_STREAKS_FILE = ROOT_DIR / "win_streaks" / "win_streaks.json"
SP_PROJECTIONS_FILE = ROOT_DIR / "starting_pitchers" / "sp_projections_war.csv"
MILESTONE_RECORDS_FILE = ROOT_DIR / "milestones" / "milestone_records.json"
PROSPECTS_FILE = ROOT_DIR / "milestones" / "prospects.csv"
PITCHER_WAR_FILE = ROOT_DIR / "starting_pitchers" / "war_lookup.json"

#Load game_scores.json
def load_scores():
    with open(SCORES_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()
        saved_scores = json.loads(raw_text)
    return saved_scores

#Save scorse to game_scores.json
def save_scores(saved_scores):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_scores, f, indent=2)

#Load projected records from projected_records.csv
def load_projections():
    with open(PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)
        projections = df.to_dict(orient='records')    
    return projections 

def load_saved_lineups():
    try:
        with open(LINEUPS_FILE, "r", encoding="utf-8") as f:
            saved_lineups = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"date": None, "games": {}}

    if isinstance(saved_lineups, dict) and "games" in saved_lineups:
        saved_lineups.setdefault("date", None)
        return saved_lineups

    return {"date": None, "games": saved_lineups}

def save_lineups(lineup_date_str, game_lineups):
    with open(LINEUPS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "date": lineup_date_str,
            "games": game_lineups
        }, f, indent=4)

def load_win_streaks():
    #Load win_streaks.json
    with open(WIN_STREAKS_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()
        if not raw_text:
            return []
        win_streaks = json.loads(raw_text)
    return win_streaks

def save_win_streaks(win_streaks):
    with open(WIN_STREAKS_FILE, "w", encoding="utf-8") as f:
        json.dump(win_streaks, f, indent=2)

def load_sp_projections():
    #Load sp_projections.csv
    with open(SP_PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)
        sp_projections = df.to_dict(orient='records')
    
    return sp_projections

def load_milestone_records():
    #Load milestone_records.json
    with open(MILESTONE_RECORDS_FILE, "r", encoding="utf-8") as f:
        milestone_records = json.load(f)
    
    return milestone_records

def save_milestone_records(milestone_records):
    with open(MILESTONE_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(milestone_records, f, indent=2)
    return None

def load_prospects():
    #Load prospects.csv
    with open(PROSPECTS_FILE, "r", encoding="utf-8") as f:
        df = pd.read_csv(f)
    prospects = df.to_dict(orient='records')
    
    return prospects

def load_milestone_stat_list():
    batter_milestone_stat_list = {
        "runs":         {"margin": 6, 'box_name': 'runs'},
        "doubles":      {"margin": 5, 'box_name': 'doubles'},
        "triples":      {"margin": 4, 'box_name': 'triples'},
        "home_runs":    {"margin": 5, 'box_name': 'homeRuns'},
        "hits":         {"margin": 7, 'box_name': 'hits'}, 
        "steals":       {"margin": 7, 'box_name': 'stolenBases'},
        "rbi":          {"margin": 10, 'box_name': 'rbi'}
    }

    pitcher_milestone_stat_list = {
        "strikeouts":      {"margin": 21, 'box_name': 'strikeOuts'},
    }

    return batter_milestone_stat_list, pitcher_milestone_stat_list


def load_pitcher_war_lookup(gamedate_str):
    # Get date
    gamedate_obj = datetime.strptime(gamedate_str, "%m/%d/%Y").date()

    try:
        #Try to fetch fresh data
        war_raw = pd.read_csv("https://www.baseball-reference.com/data/war_daily_pitch.txt")
        war_tab = war_raw[war_raw["year_ID"] == gamedate_obj.year].copy()
        war_agg = (
            war_tab
            .groupby(["mlb_ID", "year_ID"], as_index=False)
            .agg({
                "name_common": "first",
                "WAR": "sum",
                "IPouts": "sum",
                "team_ID": "last"
            })
        )
        war_agg = war_agg.dropna(subset=["mlb_ID"])
        war_agg["mlb_ID"] = war_agg["mlb_ID"].astype(int)
        war_agg["IP"] = round(war_agg["IPouts"] / 3, 1)
        war_agg["WAR"] = round(war_agg["WAR"], 1)
        war_lookup = {
            str(row["mlb_ID"]): {
                "WAR": row["WAR"],
                "IP": row["IP"]
            }
            for _, row in war_agg.iterrows()
        }

        if not war_lookup:
            raise ValueError("WAR lookup is empty")
        else:
            #Save to JSON (overwrite old cache)
            with open(PITCHER_WAR_FILE, "w") as f:
                json.dump(war_lookup, f)
            return war_lookup

    except Exception as e:
        with open(PITCHER_WAR_FILE, "r") as f:
            return json.load(f)
