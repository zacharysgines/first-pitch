"""
SAVE MILESTONES
UPDATE LINEUP CHANGES
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

milestone_score = .0094 * math.exp(.0576 * 50)
print('Milestone Score:', milestone_score)

unadjusted_score = .1581134488995094 - .05 + milestone_score
print("Unadjusted Score:",  unadjusted_score)

overall_score = min(100, 100*((math.log(1+unadjusted_score))/(math.log(3))))
print("Overall Score:", overall_score)