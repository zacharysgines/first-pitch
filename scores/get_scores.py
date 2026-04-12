import statsapi
from datetime import datetime, timedelta
import time
import math
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_scores, save_scores
from teams_info.teams_info import get_teams_info
from records.records import records
from playoffs.playoffs import playoff_imp
from win_streaks.win_streaks import winning_streak
from starting_pitchers.starting_pitchers import starting_pitchers
from milestones.milestones import milestones
from lineups.lineups import get_all_lineups


def score_all_games(starting_date, ending_date):
    #Get all scores from game_scores.json 
    saved_scores = load_scores()

    #Convert date strings to date objects
    start_date_obj = datetime.strptime(starting_date, "%m/%d/%Y").date()
    end_date_obj = datetime.strptime(ending_date, "%m/%d/%Y").date()
    #Calculate how many days are being run
    number_of_days = (end_date_obj - start_date_obj).days + 1
    #Inital date object
    rolling_date_obj = start_date_obj - timedelta(days=1)
    
    #Start tracking how long it's been running
    start_time = time.time()
    print('Beginning score calculation')

    #Run score_games for each date between the start and end date (inclusive)
    for i in range(1, number_of_days + 1):
        #Add one to the date
        rolling_date_obj += timedelta(days=1)
        gamedate = rolling_date_obj.strftime("%m/%d/%Y")
        
        #Get the scores for the current date
        score_games(gamedate, saved_scores)
                     
        #After getting the scores, print the current time running, how many scores we've gotten, and how many there are total to get        
        current_time = time.time()
        elapsed_seconds = int(current_time - start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print()
        print('Date:', gamedate)
        print(i, 'out of', number_of_days, 'sets of scores calculated')
        print(f"Time elapsed: {hours:02}:{minutes:02}:{seconds:02}")

    return None


def score_games(gamedate, saved_scores = None, use_json = True):
    #Get gamedate as an object
    gamedate_obj = datetime.strptime(gamedate, "%m/%d/%Y")
    current_year = datetime.now().year
    #If the month of the current gamedate is between November and February, we don't need to call the API
    if gamedate_obj.month in (11, 12, 1, 2) or gamedate_obj.year not in (current_year, current_year - 1):
        return []
    
    #Load scores from get_scores.json unless we already got them from get_all_score()
    if saved_scores is None:
        saved_scores = load_scores()

    #Check if this date already has an entry in the .json file. If so, get the scores from there instead of calculating them
    #If 'use_json = false', don't check the .json file for this date
    if use_json:
        for entry in saved_scores:
            if entry["gamedate"] == gamedate:
                cached_games = entry["games"]
                if all(game.get("game_datetime") for game in cached_games):
                    return cached_games
                break
        
    #Pull list of this date's games from the API
    games = statsapi.schedule(date=gamedate)
    if not games:
        return []
    
    #Go through each game for this date. If none of them are regular season games, don't get the scores for this date.
    rs_games = False
    for game in games:
        if game['game_type'] == 'R':
            rs_games = True
            break
    if rs_games == False:
        return []
    
    #If there are games on this day, get the standings for this day
    standings = statsapi.standings_data(date=gamedate)

    #Run get_scores() to get the scoring for each game this day
    game_scores = get_scores(standings, games, gamedate_obj)

    #Go through all the scores in game_scores.json and remove the date we just recomputed
    saved_scores[:] = [entry for entry in saved_scores if entry["gamedate"] != gamedate]

    #Insert the sorted scores for this day into saved_scores and save those scores to the .json file
    saved_scores.insert(0, {
        'gamedate': gamedate,
        'games': game_scores
    })
    save_scores(saved_scores)

    return game_scores

def get_scores(standings, games, gamedate_obj):
    #Run each function to get individual score components
    teams_info = get_teams_info(standings)                    #Initialize the teams_info dictionary to hold all scoring info
    get_all_lineups(games)                          #Get lineups for today
    records(teams_info, standings)                       #Get each team's current or projected record 
    playoff_imp(standings, teams_info)                   #Calculate playoff implications for each team
    winning_streak(standings, teams_info, gamedate_obj)  #Find winning streaks for each team
    starting_pitchers(games, teams_info, gamedate_obj)   #Get the starters for today's games
    milestones(games, gamedate_obj, teams_info)          #Find any milestones, record chases or prospect debuts

    #Get a list to put each game's scoring info into
    game_scores = []

    #Go through each game, get all the scores, and save all info in a dictionary
    for game in games:
        #If this game is not a regular season game, don't score it
        if game['game_type'] != 'R':
            continue

        #Game Info
        gameid = game['game_id']
        gamedatetime = game['game_datetime']
        #Team Definitions
        away_team_name = game['away_name']
        home_team_name = game['home_name']
        away_team_info = teams_info[away_team_name]
        home_team_info = teams_info[home_team_name]
        #Record
        away_wins = away_team_info['wins']
        away_losses = away_team_info['losses']
        home_wins = home_team_info['wins']
        home_losses = home_team_info['losses']
        #Playoff Implications
        away_playoff_imp_score = away_team_info['playoff_imp']
        home_playoff_imp_score = home_team_info['playoff_imp'] 
        playoff_imp_score = away_playoff_imp_score + home_playoff_imp_score
        #Win Streak
        away_win_streak = away_team_info['winning_streak']
        away_win_streak_score = away_team_info['win_streak_score']
        home_win_streak = home_team_info['winning_streak']
        home_win_streak_score = home_team_info['win_streak_score']
        win_streak_score = away_win_streak_score + home_win_streak_score
        #Winning Percentage
        away_wp = away_team_info['win_perc']
        home_wp = home_team_info['win_perc']
        away_wp_score = away_team_info['wp_score']
        home_wp_score = home_team_info['wp_score']
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
        #Divisional Score
        if away_team_info['division'] == home_team_info['division']:
            division_score = min_wp_score
        else:
            division_score = 0
        #Starting Pitcher ERA
        away_starter = away_team_info['pitcher_name']
        away_era = away_team_info['pitcher_era']
        away_era_source = away_team_info['era_source']
        away_era_score = away_team_info['era_score']
        home_starter = home_team_info['pitcher_name']
        home_era = home_team_info['pitcher_era']
        home_era_source = home_team_info['era_source']
        home_era_score = home_team_info['era_score']
        era_score = away_era_score + home_era_score
        #Milestones
        away_milestone_score = away_team_info['milestone_score']
        home_milestone_score = home_team_info['milestone_score']
        milestone_score = away_milestone_score + home_milestone_score
        #Prospects
        away_prospect_score = away_team_info['debut_score']
        home_prospect_score = home_team_info['debut_score']
        prospect_score = away_prospect_score + home_prospect_score
        #SCORING
        unadjusted_score = playoff_imp_score + win_streak_score + wp_score + team_diff_score + era_score + division_score + milestone_score + prospect_score + min_wp_score
        score = min(100, 100*((math.log(1+unadjusted_score))/(math.log(3))))    #Final Adjustment (in denominatior, math.log(x), x = 1 + 99th percentile score. 
                                                                                #Adjust higher to get less 100s, lower to get more 100s) 
        #Add the scores for this game to the game_scores list
        game_scores.append({
            'game_id': gameid,
            'game_datetime': gamedatetime,
            'away_team_name': away_team_name,
            'home_team_name': home_team_name,
            'away_wins': away_wins,
            'home_wins': home_wins,
            'away_losses': away_losses,
            'home_losses': home_losses,            
            'away_wp': away_wp,
            'home_wp': home_wp,
            'away_wp_score': away_wp_score,  
            'home_wp_score': home_wp_score,          
            'away_starter': away_starter,
            'home_starter': home_starter,
            'away_era': away_era,
            'home_era': home_era,
            'away_era_source': away_era_source,
            'home_era_source': home_era_source,
            'home_era_score': home_era_score,
            'away_era_score': away_era_score,
            'away_playoff_imp': away_playoff_imp_score,
            'home_playoff_imp': home_playoff_imp_score,
            'away_win_streak': away_win_streak,
            'home_win_streak': home_win_streak,
            'away_win_streak_score': away_win_streak_score,
            'home_win_streak_score': home_win_streak_score,
            'away_career_milestones': away_team_info['milestones']['career'],
            'away_season_milestones': away_team_info['milestones']['season'],
            'home_career_milestones': home_team_info['milestones']['career'],
            'home_season_milestones': home_team_info['milestones']['season'],
            'away_milestone_score': away_milestone_score,
            'home_milestone_score': home_milestone_score,
            'away_debuts': away_team_info['debuts'],
            'home_debuts': home_team_info['debuts'],
            'away_prospect_score': away_prospect_score,
            'home_prospect_score': home_prospect_score,
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

def update_scores(gamedate, games, games_to_update): 
    #Get game date as a string
    gamedate_obj = datetime.strptime(gamedate, "%m/%d/%Y")

    #Get scores from game_scores.json
    saved_scores = load_scores()

    #Get a reference to todays entry in game_scores. If we don't find this date in saved_scores, there's nothing to
    #update so just end the function.
    saved_games = None
    for entry in saved_scores:
        if entry["gamedate"] == gamedate:
            saved_games = entry["games"]
            break
    if saved_games is None:
        return None

    #Run each function needed to update scores to get individual score components 
    standings = statsapi.standings_data(date=gamedate)
    teams_info = get_teams_info(standings)
    starting_pitchers(games, teams_info, gamedate_obj)
    milestones(games, gamedate_obj, teams_info)

    #Create a dictionary to hold all the current game information
    current_games = {}

    for game in games:
        #If this game is not a regular season game, skip the update for that game
        if game['game_type'] != 'R':
            continue
        
        #Create a key in current_games that is this game's ID, and have that key value be a dictionary holding this game's info from games.
        current_games[game['game_id']] = game

    for saved_game in saved_games:
        game_updated = False    #Track whether this game gets updated so we can recalculate the scores only if needed
        game_id = saved_game.get('game_id')   #Get id for this game in game_scores.json
        current_game = current_games.get(game_id)   #Find the current game that shares this game_id   
        game_to_update = games_to_update.get(game_id, {})     #Find the game in games_to_update that shares this game_id

        #Get the away team and home team name for this game
        away_team_name = saved_game['away_team_name']
        home_team_name = saved_game['home_team_name']

        #If the away team needs to be updated for this game
        if game_to_update.get("away"):
            #Get the updated info for this team from teams
            away_team_info = teams_info[away_team_name]

            #Update this game with the new information
            saved_game['away_starter'] = away_team_info['pitcher_name']
            saved_game['away_era'] = away_team_info['pitcher_era']
            saved_game['away_era_source'] = away_team_info['era_source']
            saved_game['away_era_score'] = away_team_info['era_score']
            saved_game['away_career_milestones'] = away_team_info['milestones']['career']
            saved_game['away_season_milestones'] = away_team_info['milestones']['season']
            saved_game['away_milestone_score'] = away_team_info['milestone_score']
            saved_game['away_debuts'] = away_team_info['debuts']
            saved_game['away_prospect_score'] = away_team_info['debut_score']
            game_updated = True

        #If the home team needs to be updated for this game
        if game_to_update.get("home"):
            #Get the updated info for this team from teams_info
            home_team_info = teams_info[home_team_name]

            #Update this game with the new information
            saved_game['home_starter'] = home_team_info['pitcher_name']
            saved_game['home_era'] = home_team_info['pitcher_era']
            saved_game['home_era_source'] = home_team_info['era_source']
            saved_game['home_era_score'] = home_team_info['era_score']
            saved_game['home_career_milestones'] = home_team_info['milestones']['career']
            saved_game['home_season_milestones'] = home_team_info['milestones']['season']
            saved_game['home_milestone_score'] = home_team_info['milestone_score']
            saved_game['home_debuts'] = home_team_info['debuts']
            saved_game['home_prospect_score'] = home_team_info['debut_score']
            game_updated = True

        #If this game didn't get updated, don't recalculate the scoring, just move to the next game.
        if not game_updated:
            continue

        #Get the new overall scores for this game after each team has been recalculated
        saved_game['era_score'] = saved_game['away_era_score'] + saved_game['home_era_score']
        saved_game['milestone_score'] = saved_game['away_milestone_score'] + saved_game['home_milestone_score']
        saved_game['prospect_score'] = saved_game['away_prospect_score'] + saved_game['home_prospect_score']
        saved_game['unadjusted_score'] = (
            saved_game['playoff_imp_score']
            + saved_game['win_streak_score']
            + saved_game['wp_score']
            + saved_game['team_diff']
            + saved_game['era_score']
            + saved_game['division_score']
            + saved_game['milestone_score']
            + saved_game['prospect_score']
            + saved_game['min_wp_score']
        )
        saved_game['score'] = min(100, 100*((math.log(1 + saved_game['unadjusted_score'])) / (math.log(3))))

    #Re-sort all the games and resave them to the .json file
    saved_games.sort(key=lambda x: x['score'], reverse=True)
    save_scores(saved_scores)

    return saved_games

#get_all_scores('08/21/2026', '12/31/2026')
#score_games('04/08/2026', use_json=False)