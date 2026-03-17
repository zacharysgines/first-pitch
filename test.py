"""
player making mlb debut
MVP player
Cy Young Player
RotY Player
Hot Streak Player
    - Consecutive games with home run
    - Hitting streak
    - On base streak
    - OPS over last x games
    - Consecutive scoreless innnings
    - ERA over last x games
ERA milestone
Modern (and other) era records
"""

import statsapi
import pandas as pd
from datetime import datetime, timedelta
import json
import math

# def LoadProjections():
#     #Load projections.csv
#     with open('projected_records.csv', 'r', encoding='utf-8') as f:
#         df = pd.read_csv(f)
#         projections = df.to_dict(orient='records')
    
#     return projections

# def GetTeams(standings):
#     #Initialize the teams dictionary
#     teams = {}

#     #If there's no standings (i.e., first day of the season), use projections instead
#     if standings:
#         for division in standings.values():
#             for team in division['teams']:                
#                 #Initialize the dictionary for each team within the teams dictionary
#                 team_name = teams.setdefault(team['name'], {})
#                 #Save each team's Id
#                 team_obj = statsapi.lookup_team(team['name'], activeStatus="Y")
#                 team_name['id'] = team_obj[0]['id']
#                 #Save each team's divison
#                 team_name['division'] = division['div_name']
    
#     else:
#         #Load Projections
#         projections = LoadProjections()
#         for team in projections:
#             #Initialize the dictionary for each team within the teams dictionary
#             team_name = teams.setdefault(team['Name'], {})
#             #Save each team's id
#             team_obj = statsapi.lookup_team(team['Name'], activeStatus="Y")
#             teams[team['Name']]['id'] = team_obj[0]['id']
#             #Save each team's divison
#             team_name['division'] = team['Division']
    
#     return teams

# gamedate = '07/11/2025'
# date_obj = datetime.strptime(gamedate, "%m/%d/%Y")

# games = statsapi.schedule(gamedate)
# standings = statsapi.standings_data(date=gamedate)
# teams = GetTeams(standings)

# for game in games:
#     box = statsapi.boxscore_data(game['game_id'])
#     print(box['gameId'])
#     for batter in box['away']['players'].values():
#         print(batter['person'])
#     break

# #print(statsapi.lookup_player(671106))


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
            "era_diff_score": game["era_diff_score"],
            "division_score": game["division_score"],
            "milestone_score": game["milestone_score"],
            "prospect_score": game["prospect_score"],
            "unadjusted_score": game["unadjusted_score"],
            "score": game["score"],
        })

pd.DataFrame(rows).to_csv("test_scores.csv", index=False)
