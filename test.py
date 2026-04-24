# """
# Adjust divisional scores to use min wp instead of games back
# SAVE MILESTONES
# UPDATE LINEUP CHANGES
# MVP player
# Cy Young Player
# RotY Player
# Hot Streak Player
#     - Consecutive games with home run
#     - Hitting streak
#     - On base streak
#     - OPS over last x games
#     - Consecutive scoreless innnings
#     - ERA over last x games
# ERA milestone
# "On Pace" milestones
# Modern (and other) era records
# WAR data/better stats
# Automated prospect list
# """

import statsapi
import pandas as pd
from datetime import datetime, timedelta
import json
import math
import hashlib
from pathlib import Path


# # def LoadProjections():
# #     #Load projections.csv
# #     with open('projected_records.csv', 'r', encoding='utf-8') as f:
# #         df = pd.read_csv(f)
# #         projections = df.to_dict(orient='records')
    
# #     return projections

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

# # def GetProspects():
# #     PROSPECTS_CSV = 'scores\prospects.csv'

# #     try:
# #         df = pd.read_csv(PROSPECTS_CSV, encoding="utf-8")
# #     except UnicodeDecodeError:
# #         df = pd.read_csv(PROSPECTS_CSV, encoding="cp1252")
# #     prospects = df.to_dict(orient='records')

# #     return prospects

# # fv = 40
# # original_prospect_score = 0
# # unadjusted_score = 0.24395779497136927
# # new_prospect_score = .0094 * math.exp(.0576 * fv)
# # new_unadjusted_score = unadjusted_score - original_prospect_score + new_prospect_score
# # score = min(100, 100*((math.log(1+new_unadjusted_score))/(math.log(3))))
# # print('Prospect Score:', new_prospect_score)
# # print('Unadjusted Score:', new_unadjusted_score)
# # print('Score:', score)

gamedate = '04/26/2026'
date_obj = datetime.strptime(gamedate, "%m/%d/%Y")

games = statsapi.schedule(gamedate)
# standings = statsapi.standings_data(date=gamedate)
# teams = GetTeams(standings)

# pitchers = statsapi.lookup_player("Diaz")

# for pitcher in pitchers:
#     print(pitcher)


#For each game, get each teams id
for game in games:
    #Get team details
    home_team_id = game['home_id']
    away_team_id = game['away_id']
    home_team_name = game['home_name']
    away_team_name = game['away_name']
    #Get bio details for each teams starting pitcher
    home_pitcher_name = game['home_probable_pitcher']
    away_pitcher_name = game['away_probable_pitcher']
    if home_pitcher_name != '':
        home_pitcher = statsapi.lookup_player(home_pitcher_name)
    else:
        home_pitcher = None
    if away_pitcher_name != '':
        away_pitcher = statsapi.lookup_player(away_pitcher_name)
    else:
        away_pitcher = None
    
    if home_pitcher != None:
        for pitcher in home_pitcher:
            print(pitcher)
    if away_pitcher != None:
        for pitcher in away_pitcher:
            print(pitcher)
