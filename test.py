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

"""

import statsapi
import pandas as pd
from datetime import datetime, timedelta
import json
import math

def LoadProjections():
    #Load projections.csv
    with open('projected_records.csv', 'r') as f:
        df = pd.read_csv(f)
        projections = df.to_dict(orient='records')
    
    return projections

def GetTeams(standings):
    #Initialize the teams dictionary
    teams = {}

    #If there's no standings (i.e., first day of the season), use projections instead
    if standings:
        for division in standings.values():
            for team in division['teams']:                
                #Initialize the dictionary for each team within the teams dictionary
                team_name = teams.setdefault(team['name'], {})
                #Save each team's Id
                team_obj = statsapi.lookup_team(team['name'], activeStatus="Y")
                team_name['id'] = team_obj[0]['id']
                #Save each team's divison
                team_name['division'] = division['div_name']
    
    else:
        #Load Projections
        projections = LoadProjections()
        for team in projections:
            #Initialize the dictionary for each team within the teams dictionary
            team_name = teams.setdefault(team['Name'], {})
            #Save each team's id
            team_obj = statsapi.lookup_team(team['Name'], activeStatus="Y")
            teams[team['Name']]['id'] = team_obj[0]['id']
            #Save each team's divison
            team_name['division'] = team['Division']
    
    return teams

gamedate = '07/11/2025'
date_obj = datetime.strptime(gamedate, "%m/%d/%Y")

games = statsapi.schedule()
standings = statsapi.standings_data(date=gamedate)
teams = GetTeams(standings)

#Load projections.csv
with open('prospects.csv', 'r') as f:
    df = pd.read_csv(f)
    prospects = df.to_dict(orient='records')
    
test_player = 'Konnor Griffin'

for player in prospects:
    if math.isnan(player['Rank']) == False:
        name = player['Name']
        rank = player['Rank']
        score = rank * -0.0078 + 1.0078
        print(player)
        print(score)