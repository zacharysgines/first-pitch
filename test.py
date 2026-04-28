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
# Weighted team score and SP WAR based on projections and this year's stats
# """

#fv = 40
# original_prospect_score = 0
# unadjusted_score = 0.24395779497136927
# new_prospect_score = .0094 * math.exp(.0576 * fv)
# new_unadjusted_score = unadjusted_score - original_prospect_score + new_prospect_score
# score = min(100, 100*((math.log(1+new_unadjusted_score))/(math.log(3))))
# print('Prospect Score:', new_prospect_score)
# print('Unadjusted Score:', new_unadjusted_score)
# print('Score:', score)

import statsapi
from datetime import datetime
import json
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_saved_lineups, load_projections

def get_teams_info(standings):
    #Initialize the teams_info dictionary
    teams_info = {}

    #If there's no standings (i.e., first day of the season), use projections instead
    if standings:
        for division in standings.values():
            for team in division['teams']:                
                #Initialize the dictionary for each team within the teams_info dictionary
                team_info = teams_info.setdefault(team['name'], {})
                #Save each team's Id
                team_obj = statsapi.lookup_team(team['name'], activeStatus="Y")
                team_info['id'] = team_obj[0]['id']
                #Save each team's divison
                team_info['division'] = division['div_name']
    
    else:
        #Load Projections
        projections = load_projections()
        for team in projections:
            #Initialize the dictionary for each team within the teams_info dictionary
            team_info = teams_info.setdefault(team['Name'], {})
            #Save each team's id
            team_obj = statsapi.lookup_team(team['Name'], activeStatus="Y")
            team_info['id'] = team_obj[0]['id']
            #Save each team's divison
            team_info['division'] = team['Division']
    
    return teams_info

gamedate = '04/27/2026'
date_obj = datetime.strptime(gamedate, "%m/%d/%Y")

games = statsapi.schedule(gamedate)
standings = statsapi.standings_data(date=gamedate)
teams_info = get_teams_info(standings)

def get_opening_day(year):
    season = statsapi.get("season", {
        "seasonId": year,
        "sportId": 1
    })

    return season["seasons"][0]["regularSeasonStartDate"]

opening_day = get_opening_day(2026)
print(opening_day)