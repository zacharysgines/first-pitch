"""
TIER 1:
Playoff implications
player making mlb debut
Good starting pitchers
Winning streak
Team difference
Good teams playing
In-division game
"""

#In a close race
#Playing other contender (especially in the same divison and league)

import statsapi
import pandas as pd
gamedate = '09/23/2025'

games = statsapi.schedule(date=gamedate)
#Load projections.csv
with open('projected_records.csv', 'r') as f:
    df = pd.read_csv(f)
    projections = df.to_dict(orient='records')


for game in games:
    home_team_id = game['home_id']
    away_team_id = game['away_id']
    #Get bio details for each teams starting pitcher
    home_pitcher = statsapi.lookup_player(game['home_probable_pitcher'])
    away_pitcher = statsapi.lookup_player(game['away_probable_pitcher'])

    print(home_pitcher)