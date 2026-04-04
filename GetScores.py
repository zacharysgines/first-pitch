import statsapi
from datetime import datetime, timedelta
import time
import math
from SaveLoad import LoadScores, SaveScores
from scores.teams import GetTeams
from scores.records import Records
from scores.playoffs import Playoff_Imp
from scores.win_streaks import Winning_Streak
from scores.starting_pitchers import Starting_Pitchers
from scores.milestones import Milestones
from scores.lineups import GetAllLineups

def GetScores(standings, games, gamedate_obj):
    #Run each function to get individual score components
    GetAllLineups(games)
    teams = GetTeams(standings)
    Records(teams, standings)
    Playoff_Imp(standings, teams)
    Winning_Streak(standings, teams, gamedate_obj)
    Starting_Pitchers(games, teams, gamedate_obj)
    Milestones(games, gamedate_obj, teams)

    #Get a list to put each game's scores into
    game_scores = []

    for game in games:
        if game['game_type'] != 'R':
            continue

        # Preserve the scheduled UTC timestamp so the app can format it per-user.
        gamedatetime = game['game_datetime']
        status = "Scheduled"

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
        playoff_imp_score = away_playoff_imp_score + home_playoff_imp_score
        #Win Streak
        away_win_streak = away_team['winning_streak']
        home_win_streak = home_team['winning_streak']
        away_win_streak_score = 0.002 * away_win_streak**2 - 0.0047 * away_win_streak + 0.0083
        home_win_streak_score = 0.002 * home_win_streak**2 - 0.0047 * home_win_streak + 0.0083
        win_streak_score = away_win_streak_score + home_win_streak_score
        #Winning Percentage
        away_wp = away_team['win_perc']
        home_wp = home_team['win_perc']
        if away_wp < .45:
            away_wp_score = 0
        else:   
            away_wp_score = .000007 * math.exp(15.091 * away_wp)
        if home_wp < .45:
            home_wp_score = 0
        else:   
            home_wp_score = .000007 * math.exp(15.091 * home_wp)
        wp_score = (away_wp_score + home_wp_score) / 2
        #Winning Percentage Difference
        team_diff = abs(away_wp - home_wp)
        team_diff_score = max(0, 0.08 * (1 - (team_diff / 0.05)))
        #Min WP
        min_wp = min(away_wp, home_wp)
        if min_wp < .5:
            min_wp_score = 0
        else:
            min_wp_score = 8.9545 * min_wp**2 - 7.0217 * min_wp + 1.3316
        #Starting Pitcher ERA
        if away_team.get('pitcher_name'):
            away_starter = away_team['pitcher_name']
            away_era = away_team['pitcher_era']
            away_era_source = away_team['era_source']
            away_era_score = max(0,  -.012 * away_era**3 + 0.1904 * away_era**2 - 1.008 * away_era + 1.8161)
        else:
            away_starter = None
            away_era = None
            away_era_source = None
            away_era_score = 0
        if home_team.get('pitcher_name'):
            home_starter = home_team['pitcher_name']
            home_era = home_team['pitcher_era']
            home_era_source = home_team['era_source']
            home_era_score = max(0, -.012 * home_era**3 + 0.1904 * home_era**2 - 1.008 * home_era + 1.8161)
        else:
            home_starter = None
            home_era = None
            home_era_source = None
            home_era_score = 0
        era_score = away_era_score + home_era_score
        #Divisional Score
        if away_team['division'] == home_team['division']:
            away_games_back = away_team['games_back']
            home_games_back = home_team['games_back']
            max_games_back = max(away_games_back, home_games_back)
            if max_games_back < 8:
                division_score = max(0, .0004 * max_games_back**3 - 0.0053 * max_games_back**2 - 0.0036 * max_games_back + 0.1517)
            else:
                division_score = 0
        else:
            max_games_back = None
            division_score = 0
        #Milestones
        away_milestone_score = 0
        home_milestone_score = 0
        for scope in ('career', 'season'):
            for milestone in away_team['milestones'][scope]:
                away_milestone_score += milestone['milestone_score']
            for milestone in home_team['milestones'][scope]:
                home_milestone_score += milestone['milestone_score']
        milestone_score = away_milestone_score + home_milestone_score
        #Prospects
        away_prospect_score = 0
        home_prospect_score = 0
        for prospect in away_team['debuts']:
            away_prospect_score += prospect['score']
        for prospect in home_team['debuts']:
            home_prospect_score += prospect['score']
        prospect_score = away_prospect_score + home_prospect_score

        #SCORING
        unadjusted_score = playoff_imp_score + win_streak_score + wp_score + team_diff_score + era_score + division_score + milestone_score + prospect_score + min_wp_score
        score = min(100, 100*((math.log(1+unadjusted_score))/(math.log(3))))              #Final Adjustment (in denominatior, ln(x), x = 1 + 99th percentile score. 
                                                                                    #Adjust higher to get less 100s, lower to get more 100s) 
        #Add the scores for this game to the game_scores list
        game_scores.append({
            'status': status,
            'game_datetime': gamedatetime,
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
            'away_playoff_imp': away_playoff_imp_score,
            'home_playoff_imp': home_playoff_imp_score,
            'away_win_streak': away_win_streak,
            'home_win_streak': home_win_streak,
            'max_games_back': max_games_back,
            'away_career_milestones': away_team['milestones']['career'],
            'away_season_milestones': away_team['milestones']['season'],
            'home_career_milestones': home_team['milestones']['career'],
            'home_season_milestones': home_team['milestones']['season'],
            'away_debuts': away_team['debuts'],
            'home_debuts': home_team['debuts'],
            'playoff_imp_score': playoff_imp_score,
            'win_streak_score': win_streak_score,                        
            'wp_score': wp_score,
            'team_diff': team_diff_score,
            'min_wp_score': min_wp_score,
            'era_score': era_score,
            'division_score': division_score,
            'milestone_score': milestone_score,
            'prospect_score': prospect_score,
            'unadjusted_score': unadjusted_score,
            'score': score,
        })

    #Sort game scores by highest to lowest scores
    game_scores.sort(key=lambda x: x['score'], reverse=True)

    return game_scores

def ScoreGames(gamedate, saved_scores = None, use_json = True):
    #Get gamedate as an object
    gamedate_obj = datetime.strptime(gamedate, "%m/%d/%Y")
    current_year = datetime.now().year

    #If the month of the current gamedate is between November and February, we don't need to call the API
    if gamedate_obj.month in (11, 12, 1, 2) or gamedate_obj.year not in (current_year, current_year - 1):
        return []
    
    #Load existing scores unless the caller already provided them.
    # `use_json=False` should bypass the cached return path, not wipe the file.
    if saved_scores is None:
        saved_scores = LoadScores()

    #Check if this date already has an entry in the .json file. If so, get the scores from there instead of calculating them
    if use_json:
        for entry in saved_scores:
            if entry["gamedate"] == gamedate:
                cached_games = entry["games"]
                if all(game.get("game_datetime") for game in cached_games):
                    return cached_games
                break
        
    #Pull games and standings from API
    games = statsapi.schedule(date=gamedate)
    if not games:
        return []
    
    rs_games = False
    for game in games:
        if game['game_type'] == 'R':
            rs_games = True
            break
    if rs_games == False:
        return []
    
    standings = statsapi.standings_data(date=gamedate)

    game_scores = GetScores(standings, games, gamedate_obj)

    #Replace an existing entry for this date so recomputes do not create duplicates.
    saved_scores[:] = [entry for entry in saved_scores if entry["gamedate"] != gamedate]

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
        ScoreGames(gamedate, saved_scores)
        #saved_scores = LoadScores()
                     
        #After getting the scores, print the current time running, how many scores we've gotten, and how many there are total to get        
        current_time = time.time()
        elapsed_seconds = int(current_time - start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print()
        print('Date:', gamedate)
        print(i, 'out of', number_of_days, 'sets of scores calculated')
        print(f"Time elapsed: {hours:02}:{minutes:02}:{seconds:02}")

#GetAllScores('08/21/2026', '12/31/2026')
#ScoreGames('07/11/2025', use_json=False)
