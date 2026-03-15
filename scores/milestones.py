import json
from datetime import datetime
import statsapi
import math
import pandas as pd

#Load milestone_records.json
with open("scores/milestone_records.json", "r") as f:
    milestone_records = json.load(f)

# Load prospects.csv as UTF-8 so local and cloud environments decode it the same way.
df = pd.read_csv('scores/prospects.csv', encoding='utf-8')
prospects = df.to_dict(orient='records')

batter_milestone_stat_list = {
    "runs":         {"margin": 6, 'box_name': 'runs', 'score_exp': 4.5},
    "doubles":      {"margin": 5, 'box_name': 'doubles', 'score_exp': 3.5},
    "triples":      {"margin": 4, 'box_name': 'triples', 'score_exp': 2.5},
    "home_runs":    {"margin": 5, 'box_name': 'homeRuns', 'score_exp': 3.5},
    "hits":         {"margin": 7, 'box_name': 'hits', 'score_exp': 4.5}, 
    "steals":       {"margin": 7, 'box_name': 'stolenBases', 'score_exp': 4.5},
    "rbi":          {"margin": 10, 'box_name': 'rbi', 'score_exp': 6}
}

pitcher_milestone_stat_list = {
    "strikeouts":      {"margin": 21, 'box_name': 'strikeOuts', 'score_exp': 1},
    "wins":             {"margin": 1, 'box_name': 'wins', 'score_exp': 1},
}

def Milestones(games, date_obj, teams):
    #Initialize milestones dictionary
    for team in teams:
        teams[team]['milestones'] = {
            'career': [],
            'season': []
        }
        teams[team]['debuts'] = []

    #If date is later than today, don't get the milestones
    if date_obj.date() > datetime.today().date():
        return None
    
    for game in games:
        away_team = teams[game['away_name']]
        home_team = teams[game['home_name']]
        home_pitcher = game['home_probable_pitcher']
        away_pitcher = game['away_probable_pitcher']

        #Add all the milestones that need to be scored into the teams dictionary
        GetMilestonePlayers(game['game_id'], away_team, home_team, away_pitcher, home_pitcher, teams)

    return None

def GetMilestonePlayers(gameid, away_team, home_team, away_pitcher, home_pitcher, teams):
    #Get boxscores to find lineups
    box = statsapi.boxscore_data(gameid)

    #Do the following for the home and away team to use only one API call for each
    for team_status in ('away', 'home'):
        if team_status == 'away':
            teamname = away_team
            starting_pitcher = away_pitcher
        else:
            teamname = home_team
            starting_pitcher = home_pitcher

        #Look through each batter
        for player in box[team_status]['players'].values():
            #Get the id and name for this player
            player_name = player['person']['fullName']                           
            player_id = player['person']['id']

            #Check if they're in the batting order or the starting pitcher to see if they're playing in this game
            if player.get('battingOrder'):
                 GetMilestones(player_id, teamname, player_name, teams, 'hitting', batter_milestone_stat_list, player)
            if player_name == starting_pitcher:
                GetMilestones(player_id, teamname, player_name, teams, 'pitching', pitcher_milestone_stat_list, player)

    return None

def GetMilestones(player_id, teamname, player_name, teams, player_type, milestone_stat_list, player): 
    #Create a dictionary to hold all of their season and career stats for this iteration of the loop
    season_stats = {}
    career_stats = {}
    
    #Get the career stats for this player
    player_career = statsapi.player_stat_data(player_id, group=player_type, type="career")            
    career_stat_block = {}
    if player_career.get('stats'):
        career_stat_block = player_career['stats'][0].get('stats', {})

    #Change 'hitting' to 'batting' for the next dictionary read
    if player_type == 'hitting':
        new_player_type = 'batting' 
    else:
        new_player_type = 'pitching'

    season_stat_block = player.get('seasonStats', {}).get(new_player_type, {})
    #For each stat we want to track, find that player's value and save it to their dictionary
    for stat, info in milestone_stat_list.items():        
        season_stats[stat] = season_stat_block.get(info['box_name'], 0)
        career_stats[stat] = career_stat_block.get(info['box_name'], 0)

        #Pass this stat into UpdateMilestone to get the current record, and update the current record if necessary
        season_record = UpdateMilestone(season_stats[stat], stat, 'season')
        #Pass this stat into AddMilestone, which will add it into the teams dictionary if necessary
        AddMilestone(season_record, info['margin'], season_stats[stat], teamname, 'season', stat, player_name, milestone_stat_list)

        #Same thing as above, but with career milestones
        career_record = UpdateMilestone(career_stats[stat], stat, 'career')
        AddMilestone(career_record, info['margin'], career_stats[stat], teamname, 'career', stat, player_name, milestone_stat_list)
    
    if career_stat_block.get('gamesPlayed', 0) == 0:
        player = {
            'name': player_name,
            'org': None,
            'pos': player['position']['abbreviation'],
            'mlb_rank': None,
            'org_rank': None,
            'pos_rank': None,
            'score': 0.05
        }
        for prospect in prospects:
            if prospect['Name'] == player_name:
                rank = prospect['Rank']
                org_rank = prospect['OrgRank']
                pos_rank = prospect['PosRank']

                player['org'] = prospect['Org']
                player['pos'] = prospect['Pos']
                player['org_rank'] = org_rank
                
                if math.isnan(rank) == False:
                    player['mlb_rank'] = rank
                    player['score'] = rank * -0.0078 + 1.0078
                else:
                    player['score'] = org_rank * -0.0009 + 0.1026

                if math.isnan(pos_rank) == False:
                    player['pos_rank'] = pos_rank
        
        teamname['debuts'].append(player)                        
                    
    return None

def AddMilestone(record, margin, player_stat, team, scope, stat, player_name, milestone_stat_list):
    #Initialize "diff" as the difference between the record and this players value
    diff = record - player_stat
    score_exp = milestone_stat_list[stat]['score_exp']

    #If the difference is within the margin for this stat, they're approaching the record
    if 0 <= diff <= margin:
        if stat == 'strikeouts':
            score = .00005 * diff**4 - 0.0017 * diff**3 + 0.0114 * diff**2 - 0.0173 * diff + 0.9976 
        else:
            score = (1-(diff / (margin + 0.5))**score_exp)

        team['milestones'].setdefault(scope, []).append(
            {"stat": stat, "player": player_name, "value": player_stat, "target": record, "diff": diff, "milestone_type": 'Record', "milestone_score": score}
        )

    #If the difference is not within the margin, then check if we're looking for home runs, hits, wins or strikeouts. If we are, check if they're nearing a milestone,
    #and use that difference instead
    elif stat == 'home_runs' or stat == 'wins':
        target = math.ceil((player_stat + 1) / 100) * 100
        diff = target - player_stat
        if 0 < diff <= margin:
            weight = 0.000006 * target**2 - 0.0013 * target + 0.1571
            score = (1-(diff / (margin + 0.5))**score_exp) * weight

            team['milestones'].setdefault(scope, []).append(
                {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": 'Milestone', "milestone_score": score}
            )

    elif stat == 'hits' or stat == 'strikeouts':
        target = math.ceil((player_stat + 1) / 1000) * 1000
        diff = target - player_stat
        if 0 < diff <= margin:
            weight = 0.0000002 * target**2 - 0.0005 * target + 0.4
            if stat == 'strikeouts':
                score = (.00005 * diff**4 - 0.0017 * diff**3 + 0.0114 * diff**2 - 0.0173 * diff + 0.9976) * weight
            else:
                score = (1-(diff / (margin + 0.5))**score_exp) * weight

            team['milestones'].setdefault(scope, []).append(
                {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": 'Milestone', "milestone_score": score}
            )

    return None

def UpdateMilestone(player_stat, stat, scope):
    if player_stat > milestone_records[scope][stat]:
        milestone_records[scope][stat] = player_stat
        
        with open('scores/milestone_records.json', "w") as f:
            json.dump(milestone_records, f, indent=2)

    return milestone_records[scope][stat]
