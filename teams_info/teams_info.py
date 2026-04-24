import statsapi
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_projections

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