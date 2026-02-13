import statsapi
from datetime import datetime, timedelta
import pandas as pd
import time
import json
import os
import math

#Save path for game_scores.json
scores_file = "game_scores.json"

#Load projections.csv
with open('projected_records.csv', 'r') as f:
    df = pd.read_csv(f)
    projections = df.to_dict(orient='records')

#Load game_scores.json
def LoadScores():
    if not os.path.exists(scores_file):
        return []
    with open(scores_file, "r") as f:
        return json.load(f)
    
#Save a set of scores to game_scores.json
def SaveScores(scores):
    with open(scores_file, "w") as f:
        json.dump(scores, f, indent=2)

def Teams(standings):
    #Initialize the teams dictionary
    teams = {}
    #If there's no standings (i.e., first day of the season), use projections instead
    if standings:
        for division in standings.values():
            for team in division['teams']:                
                #Initialize the dictionary for each team within the teams dictionary
                teams[team['name']] = {}
                team_name = teams[team['name']]

                #Save each team's divison
                team_name['division'] = division['div_name']
                            
                #Save each teams wins, losses and games played
                wins = team['w']
                losses = team['l']
                team_name['wins'] = wins
                team_name['losses'] = losses
                games_played = wins + losses
                
                #If a team has played 50+ games, use their current winning percentage. Otherwise, use their projected winning percentage
                if games_played >= 50:
                    team_name['win_perc'] = round(wins / games_played, 3)
                    team_name['wp_source'] = 'actual'
                else:
                    for proj_team in projections:
                        if proj_team['Name'] == team['name']:   #Find this team in projected_records.csv
                            team_name['win_perc'] = round(proj_team['Wins'] / 162, 3)
                            team_name['wp_source'] = 'projected'
                            break
    else:
        for team in projections:
            teams[team['Name']] = {}
            team_name = teams[team['Name']]
            
            team_name['division'] = team['Division']
            team_name['wins'] = 0
            team_name['losses'] = 0
            team_name['win_perc'] = round(team['Wins'] / 162, 3)
            team_name['wp_source'] = 'projected'

    return teams

#Only run if there have been <50 games this year
def Playoff_Imp_Proj(teams):
    #Initialize dictionary to hold lowest loss total for each division
    min_losses = {}

    #First pass: find top team by losses in each division
    for team in projections:
        division = team['Division']
        losses = 162 - team['Wins']

        if division not in min_losses or losses < min_losses[division]:
            min_losses[division] = losses
    
    #Second pass, calculate games back for each team and set playoff implications = 0 if it's the first game of the season
    for team in projections:
        division = team['Division']
        team_name = teams[team['Name']]

        #If we haven't already calculated this teams playoff implications, set it to 0 (first game of the season). Otherwise, leave it alone.
        team_name.setdefault('playoff_imp', 0)
        
        #Get first place teams wp, current teams wp, and calculate the current teams wp back
        first_l = min_losses[division]
        losses = 162 - team['Wins']
        team_name['games_back'] =  losses - first_l

    return None

def Playoff_Imp(standings, teams):
    #Initialize dictionary to hold first and second place teams in each division and 4th place team in wild card
    gb_ref = {}
    gb_ref['divisions'] = {}
    gb_ref['leagues'] = {}
    
    #If there haven't been any games this year, use Playoff_Imp_Proj function instead
    if standings:
        #First pass: get first place and second place teams for each division, and 4th place wild card team for each league 
        for division in standings.values():
            #Initialize dictionary for each division
            gb_ref['divisions'][division['div_name']] = {}
            div_name = gb_ref['divisions'][division['div_name']]
            if division['div_name'] in ('American League East', 'American League Central', 'American League West'):
                league = 'American League'
            else:
                league = 'National League'

            for team in division['teams']:
                losses = team['l']
                div_rank = team['div_rank']
                wc_rank = team['wc_rank']

                #If you're the first team in the division, save your wins and losses to gb_ref for this division
                if div_rank == '1':
                    div_name['first_l'] = losses
                #If you're the second team in the division, save your losses to gb_ref for this division
                elif div_rank == '2':                
                    div_name['second_l'] = losses

                #If you're the 4th team in the wild card, save your losses to gb_ref for your league
                if wc_rank == '4':
                    gb_ref['leagues'][league] = losses

        #Second pass: 
        for division in standings.values():
            div_name = gb_ref['divisions'][division['div_name']]
            if division['div_name'] in ('American League East', 'American League Central', 'American League West'):
                league = 'American League'
            else:
                league = 'National League'
            
            for team in division['teams']:
                wins = team['w']
                losses = team['l']
                gp = wins + losses
                gl = 162 - (gp)  #Games left

            #Playoff Urgency
                #If you are the first place team, calculate how many games ahead of the second place team you are. Otherwise, calculate games back from first place
                if team['div_rank'] == '1':
                    gb = abs(losses - div_name['second_l'])
                else:
                    gb = abs(losses - div_name['first_l'])

                #Wild Card Games Back
                wcgb = abs(losses - gb_ref['leagues'][league])

                #Calculate division urgency and wild card urgency, then use those two to get overall urgency
                div_urgency = max(0, 1/(gb + gl) * (1 - gb/gl))
                wc_urgency = max(0, 1/(wcgb + gl) * (1 - wcgb/gl))
                urgency = (div_urgency + wc_urgency*3) / 4

                teams[team['name']]['playoff_imp'] = urgency

            #Divisional Score
                first_l = div_name['first_l']
                
                #If there have been more than 50 games, use the current records, otherwise use projections
                if gp >= 50:
                    teams[team['name']]['games_back'] =  losses - first_l
                else:
                    Playoff_Imp_Proj(teams)
    else:
        Playoff_Imp_Proj(teams)

    return None

def Winning_Streak(standings, teams, gamedate):
    #If it's the first day of the season, everyone's winning streaks should be 0
    if standings:
        for team in teams:
            #Get the ID for this team
            team_obj = statsapi.lookup_team(team, activeStatus="Y")
            team_id = team_obj[0]['id']

            #Intially define their winning streak to be true and 0 games. Set the start of the streak date to today
            winning_streak = True
            streak_count = 0
            streak_date = datetime.strptime(gamedate, "%m/%d/%Y").date()

            #While the winning streak is still true, keep going back one day at a time and see if the team won and add 1 to "streak_count"
            while winning_streak:
                #Decrease the date by one
                streak_date -= timedelta(days=1)
                streak_date_str = streak_date.strftime("%m/%d/%Y")

                #Find this teams game for the current streak_date
                prior_games = statsapi.schedule(date=streak_date_str, team=team_id)

                #If they didn't play a game that day, then just go to the next day
                if not prior_games:
                    continue

                #Look at each game that day in backwards order (for double headers)
                for game in reversed(prior_games):
                    #If the game was rained out then skip this game
                    if 'winning_team' not in game:
                        continue
                    #If this team won, add one to the winning streak
                    if game['winning_team'] == team:
                        streak_count += 1        
                    #If this team lost, end the streak
                    else:
                        winning_streak = False
                        break
            
            #After the while loop ends, save the streak count
            teams[team]['winning_streak'] = streak_count
    else:
        for team in projections:
            teams[team['Name']]['winning_streak'] = 0

    return None

def Get_SP_Stats(pitchers, team_id, season, last_season, teams):
    #If there are duplicate names, loop through the names and find the right one
    for pitcher in pitchers:
        if pitcher['currentTeam']['id'] == team_id:
            #Get this pitchers stats for this sesason
            pitcher_stats = statsapi.player_stat_data(pitcher['id'], group="pitching", type="season", season=season)
            
            #Make sure this pitchers current team is in teams to avoid DSL or ASG type things. If it's not, don't do anything else with this pitcher
            current_team = pitcher_stats.get('current_team')
            if current_team in teams:
                teams[current_team]['pitcher_name'] = pitcher['nameFirstLast']

                #If this player has pitched this year, get his innings pitched. Otherwise, set IP to 0
                if pitcher_stats['stats']:
                    ip = pitcher_stats['stats'][0]['stats']['inningsPitched']
                else:
                    ip = 0

                #If this pitcher has pitched less than 70 innings this year, use the previous years stats
                if float(ip) < 70:
                    #Get this pitchers stats for last season
                    last_year_pitcher_stats = statsapi.player_stat_data(pitcher['id'], group="pitching", type="season", season=last_season)

                    #If this player pitched last year, get his innings pitched, otherwise, set last year IP to 0
                    if last_year_pitcher_stats['stats']:
                        last_year_ip = last_year_pitcher_stats['stats'][0]['stats']['inningsPitched']
                    else:
                        last_year_ip = 0

                    #If this pitcher pitched under 70 innings last year too, then don't save any of their information
                    if float(last_year_ip) < 70:
                        teams[current_team]['pitcher_name'] = None
                        teams[current_team]['pitcher_era'] = None
                        teams[current_team]['era_source'] = None
                    #If this pitcher pitched less than 70 innings this year but more than 70 innings last year, get their ERA from last year
                    else:
                        teams[current_team]['pitcher_era'] = float(last_year_pitcher_stats['stats'][0]['stats']['era'])
                        teams[current_team]['era_source'] = 'last_year'
                #If this pitcher has pitched 70 innings this year, get their ERA from this year
                else:
                    teams[current_team]['pitcher_era'] = float(pitcher_stats['stats'][0]['stats']['era'])
                    teams[current_team]['era_source'] = 'this_year'

def Starting_Pitchers(games, teams, gamedate):
    #Get the current year and the previous year to pull pitcher stats
    date_obj = datetime.strptime(gamedate, "%m/%d/%Y")
    season = date_obj.strftime("%Y")
    last_season = str(date_obj.year - 1)

    for game in games:
        home_team_id = game['home_id']
        away_team_id = game['away_id']
        #Get bio details for each teams starting pitcher
        home_pitcher = statsapi.lookup_player(game['home_probable_pitcher'])
        away_pitcher = statsapi.lookup_player(game['away_probable_pitcher'])

        if home_pitcher:
            Get_SP_Stats(home_pitcher, home_team_id, season, last_season, teams)

        if away_pitcher:
            Get_SP_Stats(away_pitcher, away_team_id, season, last_season, teams)

    return None

def GetScores(gamedate):
    #Pull games and standings from API
    games = statsapi.schedule(date=gamedate)
    standings = statsapi.standings_data(date=gamedate)
    
    #If there are no games today, don't get the scores
    if not games:
        return False
    #If it's the all star game, don't get the scores
    for game in games:
        if game['away_name'] == 'American League All-Stars' or game['home_name'] == 'American League All-Stars':
            return False
    #Load our saved scores from the .json file and check if this date already has an entry. If so, get the scores from there instead of calculating them
    all_scores = LoadScores() 
    for entry in all_scores:
        if entry["gamedate"] == gamedate:
            return entry["games"]
    
    #Run each function to get individual score components
    teams = Teams(standings)
    Playoff_Imp(standings, teams)
    Winning_Streak(standings, teams, gamedate)
    Starting_Pitchers(games, teams, gamedate)
    
    #Get a list to put each game's scores into
    game_scores = []

    for game in games:
        #Team Definitions
        away_team_name = game['away_name']
        home_team_name = game['home_name']
        away_team = teams[away_team_name]
        home_team = teams[home_team_name]
        away_wins = away_team['wins']
        away_losses = away_team['losses']
        home_wins = home_team['wins']
        home_losses = home_team['losses']
        #Playoff Implications
        away_playoff_imp_score = away_team['playoff_imp']
        home_playoff_imp_score = home_team['playoff_imp'] 
        playoff_imp_score = ((away_playoff_imp_score+home_playoff_imp_score) / 2) ** 2.5
        #Win Streak
        away_win_streak = away_team['winning_streak']
        home_win_streak = home_team['winning_streak']
        away_win_streak_score = away_win_streak / 22
        home_win_streak_score = home_win_streak / 22
        win_streak_score = max(away_win_streak_score, home_win_streak_score) ** 3
        #Winning Percentage
        away_wp = away_team['win_perc']
        home_wp = home_team['win_perc']
        away_wp_source = away_team['wp_source']
        home_wp_source = home_team['wp_source']        
        wp_score = (max(0, (min(away_wp, home_wp) - 0.3) / 0.4)) ** 3
        #Winning Percentage Difference
        team_diff_score = (.5 - abs(away_wp - home_wp)) / 100
        #Starting Pitcher ERA
        if away_team.get('pitcher_name'):
            away_starter = away_team['pitcher_name']
            away_era = away_team['pitcher_era']
            away_era_source = away_team['era_source']
            away_era_score = max(0, ((5 - away_era) / 3))**2.5
        else:
            away_starter = None
            away_era = None
            away_era_source = None
            away_era_score = 0
        if home_team.get('pitcher_name'):
            home_starter = home_team['pitcher_name']
            home_era = home_team['pitcher_era']
            home_era_source = home_team['era_source']
            home_era_score = max(0, ((5 - home_era) / 3))**2.5
        else:
            home_starter = None
            home_era = None
            home_era_source = None
            home_era_score = 0
        era_score = 1 - (1 - away_era_score) * (1 - home_era_score)
        #Pitcher ERA Difference Score
        if away_era is not None and home_era is not None:
            era_diff = abs(away_era - home_era)
            if era_diff <= 0.5:
                era_diff_score = 1 - 1.5 * era_diff
            elif era_diff <= 1.5:
                era_diff_score = 0.25 - 0.25 * (era_diff - 0.5)
            else:
                era_diff_score = 0
        else:
            era_diff = None
            era_diff_score = 0
        era_diff_score /= 15
        #Divisional Score
        if away_team['division'] == home_team['division']:
            away_games_back = away_team['games_back']
            home_games_back = home_team['games_back']
            max_games_back = max(away_games_back, home_games_back)
            division_score = (.25**(max_games_back/5)) ** 12
        else:
            max_games_back = None
            division_score = 0

        #SCORING
        unadjusted_score = playoff_imp_score + win_streak_score + wp_score + team_diff_score + era_score + era_diff_score + division_score
        score = min(100, 100*((math.log(1+unadjusted_score))/(math.log(3))))              #Final Adjustment (in denominatior, ln(x), x = 1 + 99th percentile score. 
                                                                                    #Adjust higher to get less 100s, lower to get more 100s) 
        #Add the scores for this game to the game_scores list                                                                            
        game_scores.append({
            'away_team_name': away_team_name,
            'home_team_name': home_team_name,
            'away_wins': away_wins,
            'home_wins': home_wins,
            'away_losses': away_losses,
            'home_losses': home_losses,            
            'away_wp': away_wp,
            'home_wp': home_wp,            
            'away_wp_source': away_wp_source,
            'home_wp_source': home_wp_source,
            'away_starter': away_starter,
            'home_starter': home_starter,
            'away_era': away_era,
            'home_era': home_era,
            'away_era_source': away_era_source,
            'home_era_source': home_era_source,
            'era_diff': era_diff,
            'away_playoff_imp': away_playoff_imp_score,
            'home_playoff_imp': home_playoff_imp_score,
            'away_win_streak': away_win_streak,
            'home_win_streak': home_win_streak,
            'max_games_back': max_games_back,
            'playoff_imp_score': playoff_imp_score,
            'win_streak_score': win_streak_score,                        
            'wp_score': wp_score,
            'team_diff': team_diff_score,
            'era_score': era_score,
            'era_diff_score': era_diff_score,
            'division_score': division_score,
            'unadjusted_score': unadjusted_score,
            'score': score,
        })

    #Sort game scores by highest to lowest scores
    game_scores.sort(key=lambda x: x['score'], reverse=True)

    #Insert all the sorted scores for this day and the date into all_scores and save those scores to the .json file
    all_scores.insert(0, {
        'gamedate': gamedate,
        'games': game_scores
    })
    SaveScores(all_scores)

    return game_scores

def GetAllScores():
    #List to hold all scores
    all_scores = [] 
    #Date to start
    starting_date = '03/27/2025'
    #Number of days to run
    number_of_days = 185
    #Inital date object
    rolling_date_obj = datetime.strptime(starting_date, "%m/%d/%Y").date() - timedelta(days=1)
    
    #Start tracking how long it's been running
    start_time = time.time()
    print('Beginning score calculation')

    #Get the scores for each day
    for i in range(1, number_of_days + 1):
        #Add one to the date
        rolling_date_obj += timedelta(days=1)
        gamedate = rolling_date_obj.strftime("%m/%d/%Y")
        
        #Get the scores for the current date
        scores = GetScores(gamedate)

        #If there were games on this date, add the scores to the all_scores list
        if scores:
            for score in scores:
                all_scores.append(score['score'])
                    
        #After getting the scores, print the current time running, how many scores we've gotten, and how many there are total to get        
        current_time = time.time()
        print(i, 'out of', number_of_days, 'sets of scores calculated')
        print('Time elapsed:', current_time - start_time)

    return all_scores
    
def PrintGames(gamedate):
    #Get the scores for this date
    scores = GetScores(gamedate)

    #If there were scores on this date, print them, otherwise, say there weren't any games today
    if scores:
        print()
        for game in scores:
            #Game print
            print(game['away_team_name'], '@', game['home_team_name'], ':', round(game['score'], 0))
            print()
            #Playoff Importance
            if game['away_playoff_imp'] >= .25:
                print("Playoff implications for", game['away_team_name']) 
            if game['home_playoff_imp'] >= .25:
                print("Playoff implications for", game['home_team_name'])
            #Starting Pitcher ERA
                if game['away_era'] is not None and game['away_era'] <= 3.50:
                    if game['away_era_source'] == 'this_year':
                        print(game['away_starter'], 'has an ERA of', game['away_era'])
                    else:
                        print(game['away_starter'], 'had an ERA of', game['away_era'], 'last year')
                if game['home_era'] is not None and game['home_era'] <= 3.50:
                    if game['home_era_source'] == 'this_year':
                        print(game['home_starter'], 'has an ERA of', game['home_era'])         
                    else:
                        print(game['home_starter'], 'had an ERA of', game['home_era'], 'last year')
            #Divisional
                if game['max_wp_back'] is not None and game['max_wp_back'] <= 0.05:
                    print("Divison rivals")
            #Winning Percentage Difference
            if game['team_diff'] >= .45:
                print("Evenly matched teams")        
            #Starter ERA Difference:
                if game['era_diff'] is not None and game['era_diff'] <= 0.5:
                    print("Evenly matched starting pitchers")
            #Winning Percentage
            if game['away_wp'] > .617:
                if game['away_wp_source'] == 'actual':
                    print(game['away_team_name'], "winning percentage of", game['away_wp'])
                else:
                    print(game['away_team_name'], "projected winning percentage of", game['away_wp'])
            if game['home_wp'] > .617:
                if game['home_wp_source'] == 'actual':
                    print(game['home_team_name'], "winning percentage of", game['home_wp'])
                else:
                    print(game['home_team_name'], "projected winning percentage of", game['home_wp'])
            #Win Streak
            if game['away_win_streak'] >= 5:
                print(game['away_team_name'], "winning streak of", game['away_win_streak'], 'games')
            if game['home_win_streak'] >= 5:
                print(game['home_team_name'], "winning streak of", game['home_win_streak'], 'games')
            print()
            print("Away Team:", game['away_team_name'], 'Divisional Score:', game['division_score'], 'Playoff Imp:', game['away_playoff_imp'], 'Win Streak:', game['away_win_streak'], 'Winning Percentage:', game['away_wp'], "Starting Pitcher:", game['away_starter'], "Starter ERA:", game['away_era'], "Source:", game['away_era_source'], "Team Difference:", game['team_diff'], 'Starter Difference:', game['era_diff'])
            print("Home Team:", game['home_team_name'], 'Divisional Score:', game['division_score'], 'Playoff Imp:', game['home_playoff_imp'], 'Win Streak:', game['home_win_streak'], 'Winning Percentage:', game['home_wp'], "Starting Pitcher:", game['home_starter'], "Starter ERA:", game['home_era'], "Source:", game['home_era_source'], "Team Difference:", game['team_diff'], 'Starter Difference:', game['era_diff'])
            print()
    else:
        print("No games scheduled today")

# all_scores = GetAllScores()
# print(all_scores)