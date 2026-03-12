import json
from datetime import datetime
import statsapi
import math

#Load milestone_records.json
with open("scores\milestone_records.json", "r") as f:
    milestone_records = json.load(f)

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
        teams[team]['milestone_score'] = 0

    #If date is later than today, don't get the milestones
    if date_obj.date() > datetime.today().date():
        return None
    
    timecode = date_obj.strftime("%Y%m%d") + "_150000"

    for game in games:
        GetMilestones(timecode, game['game_id'], 'away', teams)
        GetMilestones(timecode, game['game_id'], 'home', teams)

        away_team = teams[game['away_name']]
        home_team = teams[game['home_name']]

        for team in (away_team, home_team):
            milestone_score = 0
            milestones = team['milestones']
            for scope in ('career', 'season'):
                for record in milestones[scope]:
                    milestone_score += MilestoneScore(record['stat'], record['value'], record['diff'], record['milestone_type'])
            team['milestone_score'] = milestone_score

    
    return None

def GetMilestones(timecode, gameid, team_status, teams): 
    box = statsapi.boxscore_data(gameid, timecode=timecode)

    for team in teams:
        if teams[team]['id'] == box[team_status]['team']['id']:
            teamname = team

    for batter in box[team_status]['players'].values():
        if batter.get('battingOrder'):
            id = batter['person']['id']
            player_name = batter['person']['fullName']
            player_career = statsapi.player_stat_data(id, group="hitting", type="career")
            season_stats = {}
            career_stats = {}
            for stat, info in milestone_stat_list.items():
                season_stats[stat] = batter['seasonStats']['batting'][info['box_name']]
                career_stats[stat] = player_career['stats'][0]['stats'][info['box_name']]

                season_record = UpdateMilestone(season_stats[stat], stat, 'season')
                AddMilestone(season_record, info['margin'], season_stats[stat], teamname, 'season', stat, player_name, teams)

                career_record = UpdateMilestone(career_stats[stat], stat, 'career')
                AddMilestone(career_record, info['margin'], career_stats[stat], teamname, 'career', stat, player_name, teams)

    return None

def AddMilestone(record, margin, player_stat, team_key, scope, stat, player_name, teams):
    diff = record - player_stat
    if 0 <= diff <= margin:
        teams[team_key]['milestones'].setdefault(scope, []).append(
            {"stat": stat, "player": player_name, "value": player_stat, "target": record, "diff": diff, "milestone_type": 'Record'}
        )
    elif stat == 'home_runs':
        target = math.ceil((player_stat + 1) / 100) * 100
        diff = target - player_stat
        if 0 < diff <= margin:
            teams[team_key]['milestones'].setdefault(scope, []).append(
                {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": 'Milestone'}
            )
    elif stat == 'hits':
        target = math.ceil((player_stat + 1) / 1000) * 1000
        diff = target - player_stat
        if 0 < diff <= margin:
            teams[team_key]['milestones'].setdefault(scope, []).append(
                {"stat": stat, "player": player_name, "value": player_stat, "target": target, "diff": diff, "milestone_type": 'Milestone'}
            )

    return None

def UpdateMilestone(player_stat, stat, scope):
    if player_stat > milestone_records[scope][stat]:
        milestone_records[scope][stat] = player_stat
        
        with open('milestone_records.json', "w") as f:
            json.dump(milestone_records, f, indent=2)

    return milestone_records[scope][stat]

def MilestoneScore(stat, stat_value, diff, milestone_type):
    stat_info = milestone_stat_list[stat]
    weight = 1
    if stat == 'home_runs' and milestone_type == 'Milestone':
        weight = 0.05*(math.ceil(stat_value / 100) * 100)**0.0053
    elif stat == 'hits' and milestone_type == 'Milestone':
        weight = 0.04*(math.ceil(stat_value / 1000) * 1000)**0.0008
    score = (1-(diff / (stat_info['margin'] + 0.5))**stat_info['score_exp']) * weight

    return score
