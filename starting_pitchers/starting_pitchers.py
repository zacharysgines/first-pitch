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

from save_load import load_sp_projections, load_pitcher_war_lookup


def starting_pitchers(games, teams_info, gamedate_str):
    #Load projections for starting pitchers
    sp_projections = load_sp_projections()
    war_lookup = load_pitcher_war_lookup(gamedate_str)

    #For each game, get each teams id
    for game in games:
        #Get team details
        home_team_id = game['home_id']
        away_team_id = game['away_id']
        home_team_name = game['home_name']
        away_team_name = game['away_name']
        home_team_info = teams_info[home_team_name]
        away_team_info = teams_info[away_team_name]
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
            get_sp_stats(home_pitcher[0], home_team_info, sp_projections, war_lookup, home_team_name)
        else:
            set_pitcher_info(home_team_info, None, None, None, None, None, None)
        if away_pitcher:
            get_sp_stats(away_pitcher[0], away_team_info, sp_projections, war_lookup, away_team_name)
        else:
            set_pitcher_info(away_team_info, None, None, None, None, None, None)
    return None


def get_sp_stats(pitcher, team_info, sp_projections, war_lookup, team_name):
    #Track if we find this player in the WAR dictionary
    current_found = False    
    #Look through every player who has a WAR this year in the WAR dictionary and see if any ID matches the starting pitcher's ID
    for id, stats in war_lookup.items():
        if id == str(pitcher['id']):
            #If you find a match, set war_found = True, and get the pitcher's name, WAR and IP
            current_found = True           
            current_WAR = stats['WAR']
            current_ip = stats['IP']
            if current_ip > 0: 
                current_war_per_180 = current_WAR / current_ip * 180
            else:
                current_war_per_180 = 0
                
            saved_war = current_WAR
            source = 'real'
            break

    #If we didn't find this player in the WAR dictionary, just use their projected stats
    if not current_found:
        current_WAR = 0
        current_ip = 0
        current_war_per_180 = 0

    #Get this players projected stats
    proj_ip, proj_war_per_180, proj_war = get_projected_sp_stats(sp_projections, pitcher['fullName'], team_name)

    #If we don't find projected stats or current stats, set pitcher info to None
    if current_ip == 0 and proj_ip == 0:
        set_pitcher_info(team_info, None, None, None, None, None, None)
        return None

    #Find the weighted WAR based on current and projected IP
    current_weight = min(1, current_ip / max(75, proj_ip * 0.75))
    proj_weight = 1 - current_weight

    #If the current ip is less than half of the projected ip, save the projected ip to display on the app
    if current_ip < .5 * proj_ip :
        saved_war = proj_war
        source = 'projected'
    
    #Use weights to find weighted war per 180 IP
    weighted_war_per_180 = current_weight * current_war_per_180 + proj_weight * proj_war_per_180
    
    #If we have either this players projected WAR or current WAR, calculate the score for this player and save it to the team_info dictionary
    set_pitcher_info(team_info, pitcher['fullName'], weighted_war_per_180, saved_war, source, current_WAR, proj_war)

    return None


def get_projected_sp_stats(sp_projections, pitcher_name, team_name):
    #Initialize a list to hold any pitcher who has this name
    possible_pitchers = []

    for pitcher_proj in sp_projections:
        #For each pitcher in the projections csv, if their name and team matches the current pitcher we're looking at, add them to the list of possible pitchers. 
        if normalize_name(pitcher_proj['Name']) == normalize_name(pitcher_name) and pitcher_proj['Team'] == team_name:
            possible_pitchers.append(pitcher_proj)
    
    #If we ended up with only one matching pitcher, get that pitcher's projected WAR and IP and save all their info to team_info
    if len(possible_pitchers) == 1:
        war = possible_pitchers[0]['WAR']
        ip = possible_pitchers[0]['IP']
        if ip > 0:
            war_per_180 = war / ip * 180
            return ip, war_per_180, war

    #If we didn't find a matching pitcher or found more than one match, don't save any pitcher info
    return 0, 0, 0


def set_pitcher_info(team_info, name, war_per_180, saved_war, source, current_war, projected_war):
    #Calculate the WAR score
    if war_per_180 is not None:
        floor = -1.5
        ceiling = 10
        max_score = .75
        war_score = max(0, min(1, (war_per_180 - floor) / (ceiling - floor))) * max_score
    else:
        war_score = 0
    
    #Save all info to team_info
    team_info['pitcher_name'] = name
    team_info['pitcher_current_war'] = current_war
    team_info['pitcher_projected_war'] = projected_war
    team_info['pitcher_blended_war'] = war_per_180
    team_info['war_source'] = source
    team_info['war_score'] = war_score

    return None


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
