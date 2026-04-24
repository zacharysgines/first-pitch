import pandas as pd
import statsapi
import unicodedata
import sys
from pathlib import Path
from datetime import datetime

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_sp_projections

def find_pitcher(player_list, team_id):
    potential_players = []

    for player in player_list:
        current_team = player.get('current_team') or {}
        primary_position = player.get('primaryPosition') or {}
        player_position = primary_position.get('code')

        if current_team.get('id') == team_id and player_position in ('1', 'Y'):
            potential_players.append(player)

    if len(potential_players) > 1:
        return []
    return potential_players



def normalize_name(name):
    #If the name given isn't a string, return an empty string
    if not isinstance(name, str):
        return ""

    #Convert all special characters so we can match names
    normalized = unicodedata.normalize("NFKD", name.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def starting_pitchers(games, teams_info, gamedate_str):
    #Load projections for starting pitchers
    sp_projections = load_sp_projections()

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

        #If we found more than one player with this name, run this function to determine which player we're looking for.
        if home_pitcher != None and len(home_pitcher) > 1:
            home_pitcher = find_pitcher(home_pitcher, home_team_id)
        if away_pitcher != None and len(away_pitcher) > 1:
            away_pitcher = find_pitcher(away_pitcher, away_team_id)
        
        #If we identified the pitcher, get that pitcher's stats. Otherwise, set all team_info to None
        if home_pitcher:
            get_sp_stats(gamedate_str, home_pitcher[0], home_team_name, home_pitcher_name, teams_info, sp_projections)
        else:
            set_pitcher_info(teams_info, home_team_name, None, None, None)
        if away_pitcher:
            get_sp_stats(gamedate_str, away_pitcher[0], away_team_name, away_pitcher_name, teams_info, sp_projections)
        else:
            set_pitcher_info(teams_info, away_team_name, None, None, None)
    return None


def get_sp_stats(gamedate_str, pitcher, team_name, pitcher_name, teams_info, sp_projections):
    #Get date as an object
    gamedate_obj = datetime.strptime(gamedate_str, "%m/%d/%Y").date()
    #If it's March or April, we don't need to call the API, just get the projected stats
    if gamedate_obj.month in (3, 4):
        get_projected_sp_stats(sp_projections, pitcher_name, team_name, teams_info)
        return None
    
    #Get this pitchers stats for this sesason
    game_year_str = gamedate_obj.strftime("%Y")
    pitcher_stats = statsapi.player_stat_data(pitcher['id'], group="pitching", type="season", season=game_year_str)
            
    #Make sure this pitchers current team in the stat list is in teams to avoid DSL or ASG 
    #type things. If it's not, get their projected stats instead of current stats
    if pitcher_stats.get('current_team') not in teams_info:
        get_projected_sp_stats(sp_projections, pitcher_name, team_name, teams_info)
        return None
    
    #If this player has pitched this year, get his innings pitched. Otherwise, set IP to 0
    if pitcher_stats['stats']:
        ip = pitcher_stats['stats'][0]['stats']['inningsPitched']
    else:
        ip = 0

    #If this pitcher has pitched at least 100 innings this year, get their ERA
    if float(ip) >= 100:
        era = float(pitcher_stats['stats'][0]['stats']['era'])
        set_pitcher_info(teams_info, team_name, pitcher_name, era, 'real')
        return None
    #If this pitcher has pitched less than 100 innings this year, use their projected ERA
    else:                    
        get_projected_sp_stats(sp_projections, pitcher_name, team_name, teams_info)
        return None


def get_projected_sp_stats(sp_projections, pitcher_name, team_name, teams_info):
    #Initialize a list to hold any pitcher who has this name
    possible_pitchers = []
    #Remove any special characters from the pitcher's name to match names
    pitcher_name = normalize_name(pitcher_name)

    for pitcher_proj in sp_projections:
        #For each pitcher in the projections csv, if their name and team matches the current pitcher we're looking at, add them to the list of possible pitchers. 
        if normalize_name(pitcher_proj['Name']) == pitcher_name and pitcher_proj['Team'] == team_name:
            possible_pitchers.append(pitcher_proj)
    
    #If we ended up with only one matching pitcher, get that pitcher's projected ERA and save all their info to team_info
    if len(possible_pitchers) == 1:
        era = possible_pitchers[0]['ERA']
        set_pitcher_info(teams_info, team_name, pitcher_name, era, 'projected')
        return None

    #If we didn't find a matching pitcher or found more than one match, don't save any pitcher info
    set_pitcher_info(teams_info, team_name, None, None, None)
    return None


def set_pitcher_info(teams_info, team_name, name, era, source):
    #Calculate the ERA score
    if era is not None:
        era_score = max(0,  -.012 * era**3 + 0.1904 * era**2 - 1.008 * era + 1.8161)
    else: 
        era_score = 0
    
    #Save all info to team_info
    team_info = teams_info[team_name]
    team_info['pitcher_name'] = name
    team_info['pitcher_era'] = era
    team_info['era_source'] = source
    team_info['era_score'] = era_score
