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
Milestone watch
"""

import statsapi
import pandas as pd
from datetime import datetime

gamedate = '09/23/2025'
date_obj = datetime.strptime(gamedate, "%m/%d/%Y")



games = statsapi.schedule(date=gamedate)
standings = statsapi.standings_data(date=gamedate)
teams = {}



Milestones()