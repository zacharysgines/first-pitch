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
import pandas as pd
from datetime import datetime
import unicodedata
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from teams_info.teams_info import get_teams_info
from records.records import records


gamedate_str = '09/10/2026'
standings = statsapi.standings_data(date=gamedate_str)

teams_info = get_teams_info(standings)               #Initialize the teams_info dictionary to hold all scoring info
records(teams_info, standings)                       #Get each team's current or projected record 

print(teams_info)

current_standings = {}
for team, team_info in teams_info.items():
    current_standings[team] = {
        'wins': team_info['wins'],
        'losses': team_info['losses'],
        'win_perc': team_info['adjusted_win_perc'],
        'sim_wins': 0
    }
    print(team)
    print(team_info)


    {"wins": 87, "losses": 58, "winning_percentage": 0.600, "sim_wins": 0},


#Define current structure of MLB
mlb = {
    'american_leauge': {
        'east': ['Tampa Bay Rays', 'New York Yankees', 'Boston Red Sox', 'Toronto Blue Jays', 'Baltimore Orioles'],
        'central': ['Chicago White Sox', 'Cleveland Guardians', 'Minnesota Twins', 'Detroit Tigers', 'Kansas City Royals'],
        'west': ['Houston Astros', 'Texas Rangers', 'Seattle Mariners', 'Athletics', 'Los Angeles Angels'],
    },
    'national_league': {
        'east': ['Atlanta Braves', 'Philadelphia Phillies', 'Miami Marlins', 'New York Mets', 'Washington Nationals'],
        'central': ['Milwaukee Brewers', 'Chicago Cubs', 'Pittsburgh Pirates', 'St. Louis Cardinals', 'Cincinnati Reds'],
        'west': ['Los Angeles Dodgers', 'San Diego Padres', 'Arizona Diamondbacks', 'San Francisco Giants', 'Colorado Rockies'],
    }
}

#List to track which teams made the playoffs in this simulation
playoff_teams = []
for league in mlb.values():
    #Track division winners
    division_winners = []
    for division in league.values():
        #Take the top team in each division based on wins, breaking ties randomly
        division_winner = max(division, key=lambda team: (
            sim_standings[team]['wins'] + sim_standings[team]['sim_wins'], random.random()
        ))