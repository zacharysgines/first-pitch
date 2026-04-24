"""
SAVE MILESTONES
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
"On Pace" milestones
Modern (and other) era records
WAR data/better stats
"""

import statsapi
import pandas as pd
from datetime import datetime, timedelta
import json
import math
import hashlib
from pathlib import Path
import pybaseball


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

# def GetProspects():
#     PROSPECTS_CSV = 'scores\prospects.csv'

#     try:
#         df = pd.read_csv(PROSPECTS_CSV, encoding="utf-8")
#     except UnicodeDecodeError:
#         df = pd.read_csv(PROSPECTS_CSV, encoding="cp1252")
#     prospects = df.to_dict(orient='records')

#     return prospects

#fv = 40
# original_prospect_score = 0
# unadjusted_score = 0.24395779497136927
# new_prospect_score = .0094 * math.exp(.0576 * fv)
# new_unadjusted_score = unadjusted_score - original_prospect_score + new_prospect_score
# score = min(100, 100*((math.log(1+new_unadjusted_score))/(math.log(3))))
# print('Prospect Score:', new_prospect_score)
# print('Unadjusted Score:', new_unadjusted_score)
# print('Score:', score)

gamedate = '07/11/2025'
date_obj = datetime.strptime(gamedate, "%m/%d/%Y")

# games = statsapi.schedule(gamedate)
# standings = statsapi.standings_data(date=gamedate)
# teams = GetTeams(standings)

url = "https://www.baseball-reference.com/data/war_daily_pitch.txt"

war_raw = pd.read_csv(url)
war_tab = war_raw[war_raw["year_ID"] == 2026].copy()
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
war_lookup = dict(zip(war_agg["mlb_ID"], war_agg["WAR"]))
print(war_lookup)