from datetime import datetime
from pathlib import Path
import statsapi
import math
import pandas as pd
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_milestone_records, load_prospects, load_milestone_stat_list, load_saved_lineups, save_milestone_records


def parse_future_value(fv):
    if pd.isna(fv):
        return None

    if isinstance(fv, (int, float)):
        return float(fv)

    fv_text = str(fv).strip()
    if not fv_text:
        return None

    if fv_text.endswith("+"):
        fv_value = pd.to_numeric(fv_text[:-1], errors="coerce")
        if pd.isna(fv_value):
            return None
        return float(fv_value) + 2.5

    fv_value = pd.to_numeric(fv_text, errors="coerce")
    if pd.isna(fv_value):
        return None

    return float(fv_value)


def milestones(games, gamedate_str, teams_info):
    #Initialize milestones info in teams_info
    for team in teams_info:
        team_info = teams_info[team]
        team_info['milestones'] = {
            'career': [],
            'season': []
        }
        team_info['debuts'] = []
        team_info['milestone_score'] = 0
        team_info['debut_score'] = 0

    #Get lineup info for today's games
    saved_lineups = load_saved_lineups()
    lineup_date_str = saved_lineups.get("date")
    saved_games = saved_lineups.get("games", {})

    #If the date passed in is not the lineup date, don't get the milestones for this game
    if gamedate_str != lineup_date_str:
        return None
    
    batter_milestone_stat_list, pitcher_milestone_stat_list = load_milestone_stat_list()
    
    for game in games:
        #Get team info
        away_team_info = teams_info[game['away_name']]
        home_team_info = teams_info[game['home_name']]
        #Find this game in the saved lineups. If you can't find it, don't get the milestones for this game.
        game_id = game['game_id']
        game_lineup = saved_games.get(str(game_id))
        if not game_lineup:
            continue

        #Add all the milestones that need to be scored into the teams dictionary
        for player in game_lineup.get('away_lineup', []):
            get_milestones(player, away_team_info, 'hitting', batter_milestone_stat_list)

        for player in game_lineup.get('home_lineup', []):
            get_milestones(player, home_team_info, 'hitting', batter_milestone_stat_list)

        away_pitcher = game_lineup.get('away_pitcher')
        if away_pitcher:
            get_milestones(away_pitcher, away_team_info, 'pitching', pitcher_milestone_stat_list)

        home_pitcher = game_lineup.get('home_pitcher')
        if home_pitcher:
            get_milestones(home_pitcher, home_team_info, 'pitching', pitcher_milestone_stat_list)

    return None

def get_milestones(player, team_info, player_type, milestone_stat_list): 
    #################################################################################################################################################################################
    ######################################################################### MILESTONES ############################################################################################
    #################################################################################################################################################################################
    player_name = player['name']
    #Create a dictionary to hold all of their season and career stats for this iteration of the loop
    season_stats = {}
    career_stats = {}
    
    #Get the career stats for this player
    career_stat_block = {}
    player_career = statsapi.player_stat_data(player['id'], group=player_type, type="career")            
    if player_career.get('stats'):
        career_stat_block = player_career['stats'][0].get('stats', {})

    #Get season stats for this player
    season_stat_block = player.get('stats', {})

    #For each stat we want to track, find that player's value and save it to their dictionary
    for stat_name, milestone_info in milestone_stat_list.items():        
        season_stats[stat_name] = season_stat_block.get(milestone_info['box_name'], 0)
        career_stats[stat_name] = career_stat_block.get(milestone_info['box_name'], 0)
        player_season_stat_value = season_stats[stat_name]
        player_career_stat_value = career_stats[stat_name]

        #Pass this stat into update_milestone to get the current season record, and update it if necessary
        season_record = update_milestone(player_season_stat_value, stat_name, 'season')
        #Pass this season stat into add_milestone, which will add it into the teams dictionary if necessary
        add_milestone(season_record, milestone_info['margin'], player_season_stat_value, team_info, 'season', stat_name, player_name)

        #Pass this stat into update_milestone to get the current career record, and update it if necessary
        career_record = update_milestone(player_career_stat_value, stat_name, 'career')
        #Pass this career stat into add_milestone, which will add it into the teams dictionary if necessary
        add_milestone(career_record, milestone_info['margin'], player_career_stat_value, team_info, 'career', stat_name, player_name)
    
    #################################################################################################################################################################################
    ########################################################################### DEBUTS ##############################################################################################
    #################################################################################################################################################################################
    #Get prospects.csv
    prospects = load_prospects()

    #Check if this player has not played an MLB game yet to see if they're making their debut
    if career_stat_block.get('gamesPlayed', 0) == 0:
        player_position = player.get('position')

        #Define basic debut info, which will be updated if more info is found.
        debut_info = {
            'name': player_name,
            'org': None,
            'pos': player_position,
            'mlb_rank': None,
            'org_rank': None,
            'pos_rank': None,
            'score': 0.1
        }
    
        for prospect in prospects:
            #See if you can find this player in prospects.csv. If you can't they're not a top prospect, so we don't have any additional info on them.
            if prospect['Name'] == player_name:
                #Get all info about this prospect from the .csv file
                rank = prospect['Rank']
                org_rank = prospect['OrgRank']
                pos_rank = prospect['PosRank']
                fv = parse_future_value(prospect['FV'])

                #Update debut_info with any info we found in the .csv file, and save the calculated score for this prosepct
                debut_info['org'] = prospect['Org']
                debut_info['pos'] = prospect['Pos']
                if pd.notna(rank):
                    debut_info['mlb_rank'] = rank
                if pd.notna(org_rank):
                    debut_info['org_rank'] = org_rank
                if pd.notna(pos_rank):
                    debut_info['pos_rank'] = pos_rank                                
                if fv is not None:
                    debut_info['score'] = 0.0001 * fv**2 + 0.0029 * fv - 0.1338
        
        #Save all debut info for this player into the team_info dictionary
        team_info['debuts'].append(debut_info)       
        team_info['debut_score'] += debut_info['score']
    return None


def add_milestone(record, margin, player_stat_value, team_info, scope, stat_name, player_name):
    #Initialize "diff" as the needed number to pass the record, and score as 0
    diff = record - player_stat_value + 1
    score = 0
    milestone_type = None

    #Get milestone score for runs
    if stat_name == 'runs':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 500) * 500
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, .00000005 * target_stat_value**2 + 0.0002 * target_stat_value + 0.1305)) * max(0, min(1, 0.03 * diff**3 - 0.305 * diff**2 + 0.6513 * diff + 0.5993))

    #Get milestone score for doubles
    if stat_name == 'doubles':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 100) * 100
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, .000001 * target_stat_value**2 + 0.0003 * target_stat_value + 0.1698)) * max(0, min(1, 0.1198 * diff**3 - 0.8666 * diff**2 + 1.5026 * diff + 0.1951))
    
    #Get milestone score for triples
    if stat_name == 'triples':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 50) * 50
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, -.000006 * target_stat_value**2 + 0.0042 * target_stat_value + 0.204)) * max(0, min(1, 0.3078 * diff**2 - 1.6001 * diff + 2.0321))

    #Get milestone score for home runs
    if stat_name == 'home_runs':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 100) * 100
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, .0000002 * target_stat_value**2 + 0.0009 * target_stat_value + 0.1928)) * max(0, min(1, 0.0862 * diff**3 - 0.5685 * diff**2 + 0.7238 * diff + 0.6888))

    #Get milestone score for hits
    if stat_name == 'hits':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 500) * 500
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, -.00000001 * target_stat_value**2 + 0.0003 * target_stat_value + 0.0723)) * max(0, min(1, 0.0201 * diff**3 - 0.2455 * diff**2 + 0.6613 * diff + 0.5264))

    #Get milestone score for steals
    if stat_name == 'steals':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 100) * 100
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, -.0000006 * target_stat_value**2 + 0.0015 * target_stat_value + 0.139)) * max(0, min(1,  -0.007 * diff**3 + 0.1348 * diff**2 - 0.8207 * diff + 1.5901))

    #Get milestone score for rbi
    if stat_name == 'rbi':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 500) * 500
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, .0000001 * target_stat_value**2 + 8E-05 * target_stat_value + 0.2145)) * max(0, min(1, -0.0009 * diff**4 + 0.0232 * diff**3 - 0.1981 * diff**2 + 0.4591 * diff + 0.671))

    #Get milestone score for strikeouts
    if stat_name == 'strikeouts':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 500) * 500
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, -.00000003 * target_stat_value**2 + 0.0003 * target_stat_value + 0.0857)) * max(0, min(1, 0.0006 * diff**3 - 0.0189 * diff**2 + 0.0883 * diff + 0.8579))

    #Get milestone score for wins
    if stat_name == 'wins':
        if 1 <= diff <= margin:
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 50) * 50
            diff = target_stat_value - player_stat_value
            if 1 <= diff <= margin:
                milestone_type = 'Milestone'
        if milestone_type:
            score = max(0, min(1, -.00000003 * target_stat_value**2 + 0.0003 * target_stat_value + 0.0857)) * max(0, min(1, 0.0006 * diff**3 - 0.0189 * diff**2 + 0.0883 * diff + 0.8579))

    #If the milestone score for this player was significant enough, add this milestone info to the team_info dictionary
    if score >= .2:
        team_info['milestones'].setdefault(scope, []).append(
            {"stat": stat_name, "player": player_name, "value": player_stat_value, "target": target_stat_value, "diff": diff, "milestone_type": milestone_type, "milestone_score": score}
        )     
        team_info['milestone_score'] += score
    return None


def update_milestone(player_stat_value, stat_name, scope):
    #Load the current records for each stat we're tracking
    milestone_records = load_milestone_records()

    #If this player has exceeded the record, update the record to whatever this player's stat value is
    if player_stat_value > milestone_records[scope][stat_name]:
        milestone_records[scope][stat_name] = player_stat_value
        
        #If we updated the milestone_records, save the new record
        save_milestone_records(milestone_records)

    #Return the current record for this stat
    return milestone_records[scope][stat_name]
