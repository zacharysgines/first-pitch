import statsapi
from datetime import datetime, timedelta
import pandas as pd
import time
import json
import math

#Load milestone_records.json
with open("milestone_records.json", "r") as f:
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

def LoadScores():
    #Load game_scores.json
    with open("game_scores.json", "r") as f:
        saved_scores = json.load(f)
    
    return saved_scores

def SaveScores(saved_scores):
    with open("game_scores.json", "w") as f:
        json.dump(saved_scores, f, indent=2)

def LoadProjections():
    #Load projections.csv
    with open('projected_records.csv', 'r') as f:
        df = pd.read_csv(f)
        projections = df.to_dict(orient='records')
    
    return projections

def LoadWinStreaks():
    #Load win_streaks.json
    with open("win_streaks.json", "r") as f:
        win_streaks = json.load(f)
    
    return win_streaks

def SaveWinStreaks(win_streaks):
    with open("win_streaks.json", "w") as f:
        json.dump(win_streaks, f, indent=2)

def GetTeams(standings):
    #Initialize the teams dictionary
    teams = {}

    #If there's no standings (i.e., first day of the season), use projections instead
    if standings:
        for division in standings.values():
            for team in division['teams']:                
                #Initialize the dictionary for each team within the teams dictionary
                team_name = teams.setdefault(team['name'], {})
                #Save each team's Id
                team_obj = statsapi.lookup_team(team['name'], activeStatus="Y")
                team_name['id'] = team_obj[0]['id']
                #Save each team's divison
                team_name['division'] = division['div_name']
    
    else:
        #Load Projections
        projections = LoadProjections()
        for team in projections:
            #Initialize the dictionary for each team within the teams dictionary
            team_name = teams.setdefault(team['Name'], {})
            #Save each team's id
            team_obj = statsapi.lookup_team(team['Name'], activeStatus="Y")
            team_name['id'] = team_obj[0]['id']
            #Save each team's divison
            team_name['division'] = team['Division']
    
    return teams

def Records(teams, standings):
    if standings:
        for division in standings.values():
            for team in division['teams']:  
                #Save each teams wins, losses and games played
                team_name = teams[team['name']]
                wins = team['w']
                losses = team['l']
                games_played = wins + losses
                team_name['wins'] = wins
                team_name['losses'] = losses
                
                #If a team has played 50+ games, use their current winning percentage. Otherwise, use their projected winning percentage
                if games_played >= 50:
                    team_name['win_perc'] = round(wins / games_played, 3)
                else:
                    projections = LoadProjections()
                    for proj_team in projections:
                        if proj_team['Name'] == team['name']:   #Find this team in projected_records.csv
                            team_name['win_perc'] = round(proj_team['Wins'] / 162, 3)
                            break
    else:
        projections = LoadProjections()
        for team in projections:
            team_name = teams[team['Name']]
            team_name['wins'] = 0
            team_name['losses'] = 0
            team_name['win_perc'] = round(team['Wins'] / 162, 3)

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
            div_name = gb_ref['divisions'].setdefault(division['div_name'], {})
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

#Only run if there have been <50 games this year
def Playoff_Imp_Proj(teams):
    #Load Projections
    projections = LoadProjections()

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

def Winning_Streak(standings, teams, date_obj):
    #If the current date we're getting scores for is later than today, or if it's the first day of the season, then don't get a score for winning streaks
    if (not standings) or (date_obj.date() > datetime.today().date()):
        for team in teams:
            teams[team]['winning_streak'] = 0
        return None

    win_streaks = LoadWinStreaks()

    for team in teams:
        #Intially define their winning streak to be true and 0 games. Set the start of the streak date to today
        winning_streak = True
        streak_count = 0
        streak_date = date_obj.date()

        #While the winning streak is still true, keep going back one day at a time and see if the team won and add 1 to "streak_count"
        while winning_streak:
            #Decrease the date by one
            streak_date -= timedelta(days=1)
            streak_date_str = streak_date.strftime("%m/%d/%Y")
            #Track if we found this date in the .json file. If we didn't, we need to add the results for that date into the .json file
            found_entry = False

            #Look at every entry in the .json file for this date
            for entry in win_streaks:
                #If you found the date, mark "found_entry" as true and pass the result set for this day into FindTeamResults
                if entry['gamedate'] == streak_date_str:
                    found_entry = True
                    winning_streak, won_games = FindTeamResult(entry['results'], team)
                    streak_count += won_games
                    break
                    
            #If you didn't find this date in the .json file, we need to add that date in there and return back this team's result for that date
            if found_entry == False:
                win_streaks, results = AddWinStreakEntry(streak_date_str, win_streaks)
                winning_streak, won_games = FindTeamResult(results, team)
                streak_count += won_games

        #After the while loop ends, save the streak count
        teams[team]['winning_streak'] = streak_count    

    #Save any dates that were added back into the .json file
    SaveWinStreaks(win_streaks)

    return None

def FindTeamResult(results, team):
    won_games = 0
    winning_streak = True
    for result_team, result in results.items():
        if result_team == team:
            #If this team won, add one to the streak counter
            if 'game_2' in result:
                if result['game_2'] == 'w':
                    won_games += 1
                else:
                    winning_streak = False
                    break
            if result['game_1'] == 'w':
                won_games += 1
            #If this team lost, end the winning streak
            else:
                winning_streak = False
            break

    return winning_streak, won_games
            
def AddWinStreakEntry(streak_date_str, win_streaks):
    #Track team results for this day and the result for the team that prompted getting this date 
    results = {}
    #Find this teams game for the current streak_date
    prior_games = statsapi.schedule(date=streak_date_str)

    #Look through every game this day.
    if prior_games:
        for game in prior_games:
            #If there's no winning team listed, then that game got postponed, so skip it.
            if 'winning_team' not in game:
                continue
            winning_team = game['winning_team']
            losing_team = game['losing_team']

            #Save the winning and losing teams to the results dictionary
            if winning_team not in results:
                results[winning_team] = {'game_1': 'w'}
            else:
                results[winning_team]['game_2'] = 'w'
            
            if losing_team not in results:
                results[losing_team] = {'game_1': 'l'}
            else:
                results[losing_team]['game_2'] = 'l'

    #Insert the date and results into the win_streaks dictionary 
    win_streaks.append({
        'gamedate': streak_date_str,
        'results': results
    })
            
    return win_streaks, results

def Starting_Pitchers(games, teams, date_obj):
    #Get the current year and the previous year to pull pitcher stats
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

    return None

def Milestones(games, date_obj, teams, milestone_records, milestone_stat_list):
    #Initialize milestones dictionary
    for team in teams:
        teams[team]['milestones'] = {
            'career': [],
            'season': []
        }

    #If date is later than today, don't get the milestones
    if date_obj.date() > datetime.today().date():
        return None
    
    timecode = date_obj.strftime("%Y%m%d") + "_150000"

    for game in games:
        GetMilestones(timecode, game['game_id'], 'away', teams, milestone_stat_list, milestone_records)
        GetMilestones(timecode, game['game_id'], 'home', teams, milestone_stat_list, milestone_records)
    
    return None

def GetMilestones(timecode, gameid, team_status, teams, milestone_stat_list, milestone_records): 
    box = statsapi.boxscore_data(gameid, timecode=timecode)

    teamid = box[team_status]['team']['id']
    teamname = statsapi.lookup_team(teamid)[0]['name']

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

                season_record = UpdateMilestone(season_stats[stat], stat, 'season', milestone_records)
                AddMilestone(season_record, info['margin'], season_stats[stat], teamname, 'season', stat, player_name, teams)

                career_record = UpdateMilestone(career_stats[stat], stat, 'career', milestone_records)
                AddMilestone(career_record, info['margin'], career_stats[stat], teamname, 'career', stat, player_name, teams)

    return None

def AddMilestone(record, margin, player_stat, team_key, scope, stat, player_name, teams):
    if (record - margin <= player_stat <= record) or (stat == 'home_runs' and 100 - margin <= player_stat % 100 < 100) or (stat == 'hits' and 1000 - margin <= player_stat % 1000 < 1000):
        teams[team_key]['milestones'].setdefault(scope, []).append(
            {"stat": stat, "player": player_name, "value": player_stat}
        )

    return None

def UpdateMilestone(player_stat, stat, scope, milestone_records):
    if player_stat > milestone_records[scope][stat]:
        milestone_records[scope][stat] = player_stat
        
        with open('milestone_records.json', "w") as f:
            json.dump(milestone_records, f, indent=2)

    return milestone_records[scope][stat]

def MilestoneScore(milestone_records, scope, stat, stat_value, milestone_stat_list):
    stat_info = milestone_stat_list[stat]
    weight = 1
    if stat == 'home_runs' and scope == 'career':
        record_diff = milestone_records[scope][stat] - stat_value + 1
        milestone_diffs = [abs(m - stat_value) for m in range(100, 701, 100)]
        diff = min(record_diff, *milestone_diffs)
        if diff != record_diff:
            weight = 0.05*(math.ceil(stat_value / 100) * 100)**0.0053
    elif stat == 'hits' and scope == 'career':
        record_diff = milestone_records[scope][stat] - stat_value + 1
        milestone_diffs = [abs(m - stat_value) for m in range(1000, 3001, 1000)]
        diff = min(record_diff, *milestone_diffs)
        if diff != record_diff:
            weight = 0.04*(math.ceil(stat_value / 1000) * 1000)**0.0008
    else:
        diff = milestone_records[scope][stat] - stat_value + 1
    score = (1-(diff / (stat_info['margin'] + 0.5))**stat_info['score_exp']) * weight

    return score     

def GetScores(gamedate, saved_scores = None):
    #Get gamedate as an object
    gamedate_obj = datetime.strptime(gamedate, "%m/%d/%Y")

    #If the month of the current gamedate is between November and February, we don't need to call the API
    if gamedate_obj.month in (11, 12, 1, 2):
        return []
    
    #Pull games and standings from API
    games = statsapi.schedule(date=gamedate)
    if not games:
        return []
    if games[0]['game_type'] != 'R':
        return []
    
    standings = statsapi.standings_data(date=gamedate)

    #Check if this date already has an entry in the .json file. If so, get the scores from there instead of calculating them
    if saved_scores == None:
        saved_scores = LoadScores()

    for entry in saved_scores:
        if entry["gamedate"] == gamedate:
            return entry["games"]

    #Run each function to get individual score components
    teams = GetTeams(standings)
    Records(teams, standings)
    Playoff_Imp(standings, teams)
    Winning_Streak(standings, teams, gamedate_obj)
    Starting_Pitchers(games, teams, gamedate_obj)
    Milestones(games, gamedate_obj, teams, milestone_records, milestone_stat_list)

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
        #Milestones
        milestone_score = 0
        for team in (away_team, home_team):
            milestones = team['milestones']
            for scope in ('career', 'season'):
                for record in milestones[scope]:
                    milestone_score += MilestoneScore(
                        milestone_records, scope, record['stat'], record['value'], milestone_stat_list
                    )

        #SCORING
        unadjusted_score = playoff_imp_score + win_streak_score + wp_score + team_diff_score + era_score + era_diff_score + division_score + milestone_score
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
            'away_career_milestones': away_team['milestones']['career'],
            'away_season_milestones': away_team['milestones']['season'],
            'home_career_milestones': home_team['milestones']['career'],
            'home_season_milestones': home_team['milestones']['season'],
            'playoff_imp_score': playoff_imp_score,
            'win_streak_score': win_streak_score,                        
            'wp_score': wp_score,
            'team_diff': team_diff_score,
            'era_score': era_score,
            'era_diff_score': era_diff_score,
            'division_score': division_score,
            'milestone_score': milestone_score,
            'unadjusted_score': unadjusted_score,
            'score': score,
        })

    #Sort game scores by highest to lowest scores
    game_scores.sort(key=lambda x: x['score'], reverse=True)

    #Insert all the sorted scores for this day and the date into all_scores and save those scores to the .json file
    saved_scores.insert(0, {
        'gamedate': gamedate,
        'games': game_scores
    })

    SaveScores(saved_scores)

    return game_scores

def GetAllScores(starting_date, ending_date):
    saved_scores = LoadScores()

    #Convert date strings to date objects
    start_date_obj = datetime.strptime(starting_date, "%m/%d/%Y").date()
    end_date_obj = datetime.strptime(ending_date, "%m/%d/%Y").date()
    #Number of days to run (inclusive)
    number_of_days = (end_date_obj - start_date_obj).days + 1
    #Inital date object
    rolling_date_obj = start_date_obj - timedelta(days=1)
    
    #Start tracking how long it's been running
    start_time = time.time()
    print('Beginning score calculation')

    #Get the scores for each day
    for i in range(1, number_of_days + 1):
        #Add one to the date
        rolling_date_obj += timedelta(days=1)
        gamedate = rolling_date_obj.strftime("%m/%d/%Y")
        
        #Get the scores for the current date
        GetScores(gamedate, saved_scores)
                    
        #After getting the scores, print the current time running, how many scores we've gotten, and how many there are total to get        
        current_time = time.time()
        elapsed_seconds = int(current_time - start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print()
        print('Date:', gamedate)
        print(i, 'out of', number_of_days, 'sets of scores calculated')
        print(f"Time elapsed: {hours:02}:{minutes:02}:{seconds:02}")