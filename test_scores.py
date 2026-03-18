import json
import pandas as pd

with open("game_scores.json", "r") as f:
    raw_text = f.read().strip()
    saved_scores = json.loads(raw_text) if raw_text else []

rows = []

for date_entry in saved_scores:
    gamedate = date_entry["gamedate"]
    for game in date_entry["games"]:
        rows.append({
            "gamedate": gamedate,
            "away_team_name": game["away_team_name"],
            "home_team_name": game["home_team_name"],
            "playoff_imp_score": game["playoff_imp_score"],
            "win_streak_score": game["win_streak_score"],
            "wp_score": game["wp_score"],
            "team_diff": game["team_diff"],
            "era_score": game["era_score"],
            "division_score": game["division_score"],
            "milestone_score": game["milestone_score"],
            "prospect_score": game["prospect_score"],
            "unadjusted_score": game["unadjusted_score"],
            "score": game["score"],
        })

pd.DataFrame(rows).to_csv("test_scores.csv", index=False)