import pandas as pd
import statsapi

def LoadSPProjections():
    #Load sp_projections.csv
    with open('scores/sp_projections.csv', 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)
        sp_projections = df.to_dict(orient='records')
    
    return sp_projections

def Starting_Pitchers(games, teams, date_obj):
    #Load projections for starting pitchers
    sp_projections = LoadSPProjections()

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
        home_pitcher = statsapi.lookup_player(home_pitcher_name)
        away_pitcher = statsapi.lookup_player(away_pitcher_name)

        if home_pitcher:
            Get_SP_Stats(date_obj, home_pitcher, home_team_id, home_team_name, home_pitcher_name, teams, sp_projections)

        if away_pitcher:
            Get_SP_Stats(date_obj, away_pitcher, away_team_id, away_team_name, away_pitcher_name, teams, sp_projections)

    return None

def Get_SP_Stats(date_obj, pitchers, team_id, pitcher_team, pitcher_name, teams, sp_projections):
    #Get the current year to pull pitcher stats
    season = date_obj.strftime("%Y")

    #If there are duplicate names, loop through the names and find the right one
    for pitcher in pitchers:
        if pitcher['currentTeam']['id'] == team_id:
            #If it's between November and April, we don't need to call the API, just get the projected stats
            if date_obj.month in (11, 12, 1, 2, 3, 4):
                GetProjectedSPStats(sp_projections, pitcher_name, pitcher_team, teams) 
                return None
            
            #Get this pitchers stats for this sesason
            pitcher_stats = statsapi.player_stat_data(pitcher['id'], group="pitching", type="season", season=season)
                    
            #Make sure this pitchers current team is in teams to avoid DSL or ASG type things. If it's not, don't do anything else with this pitcher
            current_team = pitcher_stats.get('current_team')
            if current_team not in teams:
                return None
            
            #If this player has pitched this year, get his innings pitched. Otherwise, set IP to 0
            if pitcher_stats['stats']:
                ip = pitcher_stats['stats'][0]['stats']['inningsPitched']
            else:
                ip = 0

            #If this pitcher has pitched at least than 100 innings this year, get their ERA
            if float(ip) >= 100:
                teams[current_team]['pitcher_name'] = pitcher_name
                teams[current_team]['pitcher_era'] = float(pitcher_stats['stats'][0]['stats']['era'])
                teams[current_team]['era_source'] = 'real'
            #If this pitcher has pitched less than 100 innings this year, use their projected ERA
            else:                    
                GetProjectedSPStats(sp_projections, pitcher_name, current_team, teams)

    return None

def GetProjectedSPStats(sp_projections, pitcher_name, current_team, teams):
    possible_pitchers = []
    for pitcher in sp_projections:
        if pitcher['Name'] == pitcher_name:
            possible_pitchers.append(pitcher)
    
    if len(possible_pitchers) > 1:
        for pitcher in possible_pitchers:
            if pitcher['Team'] == current_team:
                teams[current_team]['pitcher_era'] = pitcher['ERA']
                teams[current_team]['pitcher_name'] = pitcher_name
                teams[current_team]['era_source'] = 'projected' 
                break
    elif len(possible_pitchers) == 1:
        teams[current_team]['pitcher_era'] = possible_pitchers[0]['ERA']
        teams[current_team]['pitcher_name'] = pitcher_name
        teams[current_team]['era_source'] = 'projected' 

    return None
