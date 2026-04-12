import pandas as pd
import statsapi
import unicodedata

def load_sp_projections():
    #Load sp_projections.csv
    with open('scores/sp_projections.csv', 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)
        sp_projections = df.to_dict(orient='records')
    
    return sp_projections

def NormalizeName(name):
    if not isinstance(name, str):
        return ""

    normalized = unicodedata.normalize("NFKD", name.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))

def starting_pitchers(games, teams, date_obj):
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
        home_pitcher = statsapi.lookup_player(home_pitcher_name)
        away_pitcher = statsapi.lookup_player(away_pitcher_name)

        if home_pitcher:
            get_sp_stats(date_obj, home_pitcher, home_team_id, home_team_name, home_pitcher_name, teams, sp_projections)
        else:
            set_pitcher_info(teams, home_team_name, None, None, None)

        if away_pitcher:
            get_sp_stats(date_obj, away_pitcher, away_team_id, away_team_name, away_pitcher_name, teams, sp_projections)
        else:
            set_pitcher_info(teams, away_team_name, None, None, None)

    return None

def get_sp_stats(date_obj, pitchers, team_id, pitcher_team, pitcher_name, teams, sp_projections):
    #Get the current year to pull pitcher stats
    season = date_obj.strftime("%Y")

    #If there are duplicate names, loop through the names and find the right one
    for pitcher in pitchers:
        if pitcher['currentTeam']['id'] == team_id:
            #If it's March or April, we don't need to call the API, just get the projected stats
            if date_obj.month in (3, 4):
                get_projected_sp_stats(sp_projections, pitcher_name, pitcher_team, teams)
                return None
            
            #Get this pitchers stats for this sesason
            pitcher_stats = statsapi.player_stat_data(pitcher['id'], group="pitching", type="season", season=season)
                    
            #Make sure this pitchers current team in the stat list is in teams to avoid DSL or ASG 
            #type things. If it's not, get their projected stats instead of current stats
            current_team = pitcher_stats.get('current_team')
            if current_team not in teams:
                get_projected_sp_stats(sp_projections, pitcher_name, pitcher_team, teams)
                return None
            
            #If this player has pitched this year, get his innings pitched. Otherwise, set IP to 0
            if pitcher_stats['stats']:
                ip = pitcher_stats['stats'][0]['stats']['inningsPitched']
            else:
                ip = 0

            #If this pitcher has pitched at least than 100 innings this year, get their ERA
            if float(ip) >= 100:
                era = float(pitcher_stats['stats'][0]['stats']['era'])
                set_pitcher_info(teams, current_team, pitcher_name, era, 'real')
                return None
            #If this pitcher has pitched less than 100 innings this year, use their projected ERA
            else:                    
                get_projected_sp_stats(sp_projections, pitcher_name, current_team, teams)
                return None
        
    set_pitcher_info(teams, pitcher_team, None, None, None)
            
    return None

def get_projected_sp_stats(sp_projections, pitcher_name, current_team, teams):
    possible_pitchers = []
    normalized_pitcher_name = NormalizeName(pitcher_name)

    for pitcher in sp_projections:
        if NormalizeName(pitcher['Name']) == normalized_pitcher_name:
            possible_pitchers.append(pitcher)
    
    if possible_pitchers:
        for pitcher in possible_pitchers:
            if pitcher['Team'] == current_team:
                era = pitcher['ERA']
                set_pitcher_info(teams, current_team, pitcher_name, era, 'projected')
                return None

    set_pitcher_info(teams, current_team, None, None, None)

    return None

def set_pitcher_info(teams, team, name, era, source):
    if era is not None:
        era_score = max(0,  -.012 * era**3 + 0.1904 * era**2 - 1.008 * era + 1.8161)
    else: 
        era_score = 0
    teams[team]['pitcher_name'] = name
    teams[team]['pitcher_era'] = era
    teams[team]['era_source'] = source
    teams[team]['era_score'] = era_score