import json
from datetime import datetime
from pathlib import Path
import statsapi
import math
import pandas as pd

#Load milestone_records.json
with open("scores/milestone_records.json", "r") as f:
    milestone_records = json.load(f)

# Load prospects.csv with an encoding fallback because the source file currently
# contains Windows-1252 characters such as accented player names.
PROSPECTS_CSV = Path(__file__).with_name("prospects.csv")

try:
    df = pd.read_csv(PROSPECTS_CSV, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(PROSPECTS_CSV, encoding="cp1252")
prospects = df.to_dict(orient='records')

batter_milestone_stat_list = {
    "runs":         {"margin": 6, 'box_name': 'runs'},
    "doubles":      {"margin": 5, 'box_name': 'doubles'},
    "triples":      {"margin": 4, 'box_name': 'triples'},
    "home_runs":    {"margin": 5, 'box_name': 'homeRuns'},
    "hits":         {"margin": 7, 'box_name': 'hits'}, 
    "steals":       {"margin": 7, 'box_name': 'stolenBases'},
    "rbi":          {"margin": 10, 'box_name': 'rbi'}
}

pitcher_milestone_stat_list = {
    "strikeouts":      {"margin": 21, 'box_name': 'strikeOuts'},
}

def CleanProspectValue(value):
    if pd.isna(value):
        return None
    return value

def LoadLineups():
    with open("scores/lineups.json", "r") as f:
        saved_lineups = json.load(f)

    if isinstance(saved_lineups, dict) and "games" in saved_lineups:
        return saved_lineups["games"]

    return saved_lineups

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

    saved_lineups = LoadLineups()
    
    for game in games:
        away_team = teams[game['away_name']]
        home_team = teams[game['home_name']]
        game_key = f"game_{game['game_id']}"
        game_lineup = saved_lineups.get(game_key)

        if not game_lineup:
            continue

        #Add all the milestones that need to be scored into the teams dictionary
        for player in game_lineup.get('away_lineup', []):
            GetMilestones(player['id'], away_team, player['name'], teams, 'hitting', batter_milestone_stat_list, player)

        for player in game_lineup.get('home_lineup', []):
            GetMilestones(player['id'], home_team, player['name'], teams, 'hitting', batter_milestone_stat_list, player)

        away_pitcher = game_lineup.get('away_pitcher')
        if away_pitcher:
            GetMilestones(away_pitcher['id'], away_team, away_pitcher['name'], teams, 'pitching', pitcher_milestone_stat_list, away_pitcher)

        home_pitcher = game_lineup.get('home_pitcher')
        if home_pitcher:
            GetMilestones(home_pitcher['id'], home_team, home_pitcher['name'], teams, 'pitching', pitcher_milestone_stat_list, home_pitcher)

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

    season_stat_block = player.get('stats', {})
    #For each stat we want to track, find that player's value and save it to their dictionary
    for stat, info in milestone_stat_list.items():        
        season_stats[stat] = season_stat_block.get(info['box_name'], 0)
        career_stats[stat] = career_stat_block.get(info['box_name'], 0)

        #Pass this stat into UpdateMilestone to get the current record, and update the current record if necessary
        season_record = UpdateMilestone(season_stats[stat], stat, 'season')
        #Pass this stat into AddMilestone, which will add it into the teams dictionary if necessary
        AddMilestone(season_record, info['margin'], season_stats[stat], teamname, 'season', stat, player_name)

        #Same thing as above, but with career milestones
        career_record = UpdateMilestone(career_stats[stat], stat, 'career')
        AddMilestone(career_record, info['margin'], career_stats[stat], teamname, 'career', stat, player_name)
    
    if career_stat_block.get('gamesPlayed', 0) == 0:
        if player_type == 'pitching':
            player_position = 'SP'
        else:
            player_position = player.get('position')

        player = {
            'name': player_name,
            'org': None,
            'pos': player_position,
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
                fv = prospect['FV']

                player['org'] = prospect['Org']
                player['pos'] = prospect['Pos']

                if pd.notna(rank):
                    player['mlb_rank'] = rank
                if pd.notna(org_rank):
                    player['org_rank'] = org_rank
                if pd.notna(pos_rank):
                    player['pos_rank'] = pos_rank                
                                
                player['score'] = .0094 * math.exp(.0576 * fv)
        
        teamname['debuts'].append(player)                        
                    
    return None

def AddMilestone(record, margin, player_stat, team, scope, stat, player_name):
    #Initialize "diff" as the difference between the record and this players value
    diff = record - player_stat
    score = 0

    #Get milestone score for runs
    if stat == 'runs':
        if 0 <= diff <= margin:
            score = .0241 * diff**3 - .2581 * diff**2 + .6035 * diff + .6333
            target = record
            milestone_type = 'Record'

    #Get milestone score for doubles
    if stat == 'doubles':
        if 0 <= diff <= margin:
            score = -.245 * diff + 1.245
            target = record
            milestone_type = "Record"
    
    #Get milestone score for triples
    if stat == 'triples':
        if 0 <= diff <= margin:
            score = .1125 * diff**2 - .8675 * diff + .17625
            target = record
            milestone_type = "Record"

    #Get milestone score for home runs
    if stat == 'home_runs':
        if 0 <= diff <= margin:
            score = (0.0414 * diff**2 - 0.4846 * diff + 1.488) * 2
            target = record
            milestone_type = 'Record'
        else:
            target = math.ceil((player_stat + 1) / 100) * 100
            diff = target - player_stat
            if 0 <= diff <= margin:
                score = (0.0414 * diff**2 - 0.4846 * diff + 1.488) * (0.0263 * math.exp(0.006 * target))
                milestone_type = 'Milestone'

    #Get milestone score for hits
    if stat == 'hits':
        if 0 <= diff <= margin:
            score = (.0103 * diff**3 - .1202 * diff**2 + 0.2245 * diff + .9029) * 2
            target = record
            milestone_type = 'Record'
        else:
            target = math.ceil((player_stat + 1) / 1000) * 1000
            diff = target - player_stat
            if 0 <= diff <= margin:
                score = (.0103 * diff**3 - .1202 * diff**2 + 0.2245 * diff + .9029) * (.0000002 * target**2 - .0005 * target + .4)
                milestone_type = 'Milestone'

    #Get milestone score for steals
    if stat == 'steals':
        if 0 <= diff <= margin:
            score = .0125 * diff**3 - .1423 * diff**2 + .2667 * diff + .8857
            target = record
            milestone_type = 'Record'

    #Get milestone score for rbi
    if stat == 'rbi':
        if 0 <= diff <= margin:
            score = .0037 * diff**3 - .057 * diff**2 + .1181 * diff + .9503
            target = record
            milestone_type = 'Record'

    #Get milestone score for strikeouts
    if stat == 'strikeouts':
        if 0 <= diff <= margin:
            score = (.0004 * diff**3 - .0149 * diff**2 + 0.0837 * diff + .9017) * 2
            target = record
            milestone_type = 'Record'
        else:
            target = math.ceil((player_stat + 1) / 1000) * 1000
            diff = target - player_stat
            if 0 <= diff <= margin:
                score = (.0004 * diff**3 - .0149 * diff**2 + 0.0837 * diff + .9017) * (.0000002 * target**2 - .0003 * target + .18)
                milestone_type = 'Milestone'

    if score >= .05:
        team['milestones'].setdefault(scope, []).append(
            {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": milestone_type, "milestone_score": score}
        )     

    return None

def UpdateMilestone(player_stat, stat, scope):
    if player_stat > milestone_records[scope][stat]:
        milestone_records[scope][stat] = player_stat
        
        with open('scores/milestone_records.json', "w") as f:
            json.dump(milestone_records, f, indent=2)

    return milestone_records[scope][stat]