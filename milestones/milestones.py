from datetime import datetime, timedelta
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

from save_load import load_milestone_records, load_prospects, load_milestone_stat_list, load_saved_lineups, save_milestone_records, load_player_stats


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

    #Get player_stats list 
    player_stats = load_player_stats()

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
            #get_milestones(player, away_team_info, 'hitting', batter_milestone_stat_list)
            get_streaks(player, player_stats, gamedate_str)
            break

        # for player in game_lineup.get('home_lineup', []):
        #     get_milestones(player, home_team_info, 'hitting', batter_milestone_stat_list)

        # away_pitcher = game_lineup.get('away_pitcher')
        # if away_pitcher:
        #     get_milestones(away_pitcher, away_team_info, 'pitching', pitcher_milestone_stat_list)

        # home_pitcher = game_lineup.get('home_pitcher')
        # if home_pitcher:
        #     get_milestones(home_pitcher, home_team_info, 'pitching', pitcher_milestone_stat_list)

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
            'score': 0.05
        }

        for prospect in prospects:
            #See if you can find this player in prospects.csv. If you can't they're not a top prospect, so we don't have any additional info on them.
            if prospect['Name'] == player_name:
                #Get all info about this prospect from the .csv file
                rank = prospect['Rank']
                org_rank = prospect['OrgRank']
                pos_rank = prospect['PosRank']
                fv = prospect['FV']

                #Update debut_info with any info we found in the .csv file, and save the calculated score for this prosepct
                debut_info['org'] = prospect['Org']
                debut_info['pos'] = prospect['Pos']
                if pd.notna(rank):
                    debut_info['mlb_rank'] = rank
                if pd.notna(org_rank):
                    debut_info['org_rank'] = org_rank
                if pd.notna(pos_rank):
                    debut_info['pos_rank'] = pos_rank                                
                debut_info['score'] = .0094 * math.exp(.0576 * fv)
        
        #Save all debut info for this player into the team_info dictionary
        team_info['debuts'].append(debut_info)       
        team_info['debut_score'] += debut_info['score']
    return None


def add_milestone(record, margin, player_stat_value, team_info, scope, stat_name, player_name):
    #Initialize "diff" as the difference between the record and this players value, and score as 0
    diff = record - player_stat_value
    score = 0

    #Get milestone score for runs
    if stat_name == 'runs':
        if 0 <= diff <= margin:
            score = min(1, .0172 * diff**3 - .1757 * diff**2 + .2787 * diff + .9674)
            target_stat_value = record
            milestone_type = 'Record'

    #Get milestone score for doubles
    if stat_name == 'doubles':
        if 0 <= diff <= margin:
            score = min(1, .0264 * diff**3 - .2167 * diff**2 + .2438 * diff + .9869)
            target_stat_value = record
            milestone_type = "Record"
    
    #Get milestone score for triples
    if stat_name == 'triples':
        if 0 <= diff <= margin:
            score = min(1, .0536 * diff**2 - .4693 * diff + 1.0471)
            target_stat_value = record
            milestone_type = "Record"

    #Get milestone score for home runs
    if stat_name == 'home_runs':
        if 0 <= diff <= margin:
            score = min(1, 0.0273 * diff**3 - 0.2272 * diff**2 + 0.263 * diff + 0.9841)
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 100) * 100
            diff = target_stat_value - player_stat_value
            if 0 <= diff <= margin:
                score = min(1, 0.0414 * diff**2 - 0.4846 * diff + 1.488) * min(1, -.000000006 * target_stat_value**3 + .000008 * target_stat_value**2 - .0018 * target_stat_value + .1593)
                milestone_type = 'Milestone'

    #Get milestone score for hits
    if stat_name == 'hits':
        if 0 <= diff <= margin:
            score = min(1, -.003 * diff**3 - .0052 * diff**2 + 0.052 * diff + .9785)
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 1000) * 1000
            diff = target_stat_value - player_stat_value
            if 0 <= diff <= margin:
                score = min(1, -.003 * diff**3 - .0052 * diff**2 + 0.052 * diff + .9785) * min(1, -.00000000006 * target_stat_value**3 + .0000005 * target_stat_value**2 - .001 * target_stat_value + .54)
                milestone_type = 'Milestone'

    #Get milestone score for steals
    if stat_name == 'steals':
        if 0 <= diff <= margin:
            score = min(1, .0172 * diff**3 - .1757 * diff**2 + .2787 * diff + .9674)
            target_stat_value = record
            milestone_type = 'Record'

    #Get milestone score for rbi
    if stat_name == 'rbi':
        if 0 <= diff <= margin:
            score = min(1, .0041 * diff**3 - .0707 * diff**2 + .2037 * diff + .9308)
            target_stat_value = record
            milestone_type = 'Record'

    #Get milestone score for strikeouts
    if stat_name == 'strikeouts':
        if 0 <= diff <= margin:
            if diff <= 10:
                score = 1
            else:
                score = min(1, -.0004 * diff**3 + .0313 * diff**2 - 0.7902 * diff + 6.3981)
            target_stat_value = record
            milestone_type = 'Record'
        else:
            target_stat_value = math.ceil((player_stat_value + 1) / 1000) * 1000
            diff = target_stat_value - player_stat_value
            if 0 <= diff <= margin:
                if target_stat_value >= 5000:
                    score = 1
                else:
                    score = min(1, -.0004 * diff**3 + .0313 * diff**2 - 0.7902 * diff + 6.3981) * min(1, .00000005 * target_stat_value**2 + .00007 * target_stat_value - .075)
                milestone_type = 'Milestone'

    #If the milestone score for this player was significant enough, add this milestone info to the team_info dictionary
    if score >= .05:
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


def get_streaks(player, player_stats, gamedate_str):
    #Get today's date and the date of opening day so we know how far back we need to calculate streaks
    season_dates = statsapi.get("season", {"seasonId": datetime.now().year,"sportId": 1})
    opening_day_str = season_dates["seasons"][0]["regularSeasonStartDate"]
    opening_day_obj = datetime.strptime(opening_day_str, "%Y-%m-%d")
    gamedate_obj = datetime.strptime(gamedate_str, "%m/%d/%Y")

    #Set each streak as active and 0 for tracking
    hitting_streak_active = True
    hitting_streak = 0

    for saved_player in player_stats:
        #Find the player in player_stats.json that matches the current player we're looking at
        if saved_player['player_id'] == player['id']:
            #Loop through dates until we get back to opening day
            while gamedate_obj >= opening_day_obj:
                #Subtract one from the last day we looked at to get the previous date (gamedate starts as today, so first day we check is yesterday)
                gamedate_obj -= timedelta(days=1)
                check_date = gamedate_obj.strftime("%m/%d/%Y")
                print(check_date)

                #Initialize "found_date" as false and set true if we find this date in player_stats.json
                found_date = False
                #Loop through each date we have saved for this player
                for saved_game in saved_player['games']:
                    #If we find this date saved alraedy, check their streak numbers from the saved stats
                    if saved_game['date'] == check_date:
                        found_date = True                        
                        print(saved_game)

                        #Get this players saved stats for this day
                        at_bats =  saved_game['stats']['at_bats']
                        hits = saved_game['stats']['hits']

                        #Make sure they had at least one at bat on this date. If they didn't, don't consider the hitting streak
                        if at_bats > 0:
                            #If they had a hit, add one to their hitting streak
                            if hits > 0:
                                hitting_streak += 1
                            #If they didn't end the streak
                            else:
                                hitting_streak_active = False
                        
                        break
                    
                    #If we didn't find this date, add their stats for this date into player_stats.json
                    if found_date == False:
                        prior_games = statsapi.schedule(date=check_date)
                        #print(prior_games)





                


    





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

milestones(games, gamedate, teams_info)
