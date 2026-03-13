import json
from datetime import datetime
import statsapi
import math
import pandas as pd

#Load milestone_records.json
with open("scores\milestone_records.json", "r") as f:
    milestone_records = json.load(f)

#Load prospects.csv
with open('prospects.csv', 'r') as f:
    df = pd.read_csv(f)
    prospects = df.to_dict(orient='records')

milestone_stat_list = {
    "runs":         {"margin": 6, 'box_name': 'runs', 'score_exp': 4.5},
    "doubles":      {"margin": 5, 'box_name': 'doubles', 'score_exp': 3.5},
    "triples":      {"margin": 4, 'box_name': 'triples', 'score_exp': 2.5},
    "home_runs":    {"margin": 5, 'box_name': 'homeRuns', 'score_exp': 3.5},
    "hits":         {"margin": 7, 'box_name': 'hits', 'score_exp': 4.5}, 
    "steals":       {"margin": 7, 'box_name': 'stolenBases', 'score_exp': 4.5},
    "rbi":          {"margin": 10, 'box_name': 'rbi', 'score_exp': 6}
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

        #Add all the milestones that need to be scored into the teams dictionary
        GetMilestones(game['game_id'], teams, away_team, home_team)

    return None

def GetMilestones(gameid, teams, away_team, home_team): 
    #Get boxscores to find lineups
    box = statsapi.boxscore_data(gameid)

    #Do the following for the home and away team to use only one API call for each
    for team_status in ('away', 'home'):
        if team_status == 'away':
            teamname = away_team
        else:
            teamname = home_team

        #Look through each batter
        for batter in box[team_status]['players'].values():
            #Check if they're in the batting order to see if they're playing in this game
            if batter.get('battingOrder'):
                #Get the id, name and career stats for this player
                id = batter['person']['id']
                player_name = batter['person']['fullName']                
                player_career = statsapi.player_stat_data(id, group="hitting", type="career")
                
                #Create a dictionary to hold all of their season and career stats for this iteration of the loop
                season_stats = {}
                career_stats = {}

                #For each stat we want to track, find that player's value and save it to their dictionary
                for stat, info in milestone_stat_list.items():
                    season_stats[stat] = batter['seasonStats']['batting'][info['box_name']]
                    career_stats[stat] = player_career['stats'][0]['stats'][info['box_name']]

                    #Pass this stat into UpdateMilestone to get the current record, and update the current record if necessary
                    season_record = UpdateMilestone(season_stats[stat], stat, 'season')
                    #Pass this stat into AddMilestone, which will add it into the teams dictionary if necessary
                    AddMilestone(season_record, info['margin'], season_stats[stat], teamname, 'season', stat, player_name, teams)

                    #Same thing as above, but with career milestones
                    career_record = UpdateMilestone(career_stats[stat], stat, 'career')
                    AddMilestone(career_record, info['margin'], career_stats[stat], teamname, 'career', stat, player_name, teams)
                
                if player_career['stats'][0]['stats']['gamesPlayed'] == 0:
                    player = {
                        'name': player_name,
                        'org': None,
                        'pos': batter['position']['abbreviation'],
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

def AddMilestone(record, margin, player_stat, team, scope, stat, player_name, teams):
    #Initialize "diff" as the difference between the record and this players value
    diff = record - player_stat
    score_exp = milestone_stat_list[stat]['score_exp']

    #If the difference is within the margin for this stat, they're approaching the record
    if 0 <= diff <= margin:
        score = (1-(diff / (margin + 0.5))**score_exp)

        team['milestones'].setdefault(scope, []).append(
            {"stat": stat, "player": player_name, "value": player_stat, "target": record, "diff": diff, "milestone_type": 'Record', "milestone_score": score}
        )

    #If the difference is not within the margin, then check if we're looking for home runs or hits. If we are, check if they're nearing a milestone,
    #and use that difference instead
    elif stat == 'home_runs':
        target = math.ceil((player_stat + 1) / 100) * 100
        diff = target - player_stat
        if 0 < diff <= margin:
            weight = 0.05*(math.ceil(player_stat / 100) * 100)**0.0053
            score = (1-(diff / (margin + 0.5))**score_exp) * weight

            team['milestones'].setdefault(scope, []).append(
                {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": 'Milestone', "milestone_score": score}
            )
    elif stat == 'hits':
        target = math.ceil((player_stat + 1) / 1000) * 1000
        diff = target - player_stat
        if 0 < diff <= margin:            
            weight = 0.04*(math.ceil(player_stat / 1000) * 1000)**0.0008
            score = (1-(diff / (margin + 0.5))**score_exp) * weight

            team['milestones'].setdefault(scope, []).append(
                {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": 'Milestone', "milestone_score": score}
            )

    return None

def UpdateMilestone(player_stat, stat, scope):
    if player_stat > milestone_records[scope][stat]:
        milestone_records[scope][stat] = player_stat
        
        with open('milestone_records.json', "w") as f:
            json.dump(milestone_records, f, indent=2)

    return milestone_records[scope][stat]