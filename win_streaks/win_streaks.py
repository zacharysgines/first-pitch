from datetime import datetime, timedelta
import statsapi
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_win_streaks, save_win_streaks

def win_streak(standings, teams_info, gamedate_str):
    #Get gamedate as an object
    gamedate_obj = datetime.strptime(gamedate_str, "%m/%d/%Y").date()
    #If the current date we're getting scores for is later than today, or if it's the first day of the season, then don't get a score for winning streaks
    if (not standings) or (gamedate_obj > datetime.today().date()):
        for team in teams_info:
            team_info = teams_info[team]
            team_info['win_streak'] = 0
            team_info['win_streak_score'] = 0
        return None

    wins_log = load_win_streaks()   #Get each teams wins/loss log for the year
    streak_year = gamedate_obj.year     #Get the current year so we don't track streaks going back to last year

    for team in teams_info:
        team_info = teams_info[team]

        #Intially define their winning streak to be true and 0 games. Set the start of the streak date to today
        win_streak = True
        streak_count = 0
        streak_date_obj = gamedate_obj

        #While the winning streak is still true, keep going back one day at a time and see if the team won and add 1 to "streak_count"
        while win_streak:
            #Decrease the date by one
            streak_date_obj -= timedelta(days=1)
            streak_date_str = streak_date_obj.strftime("%m/%d/%Y")

            #If the date we're looking at is last year, stop counting their winning streak
            if streak_date_obj.year < streak_year:
                break

            #Track if we found this date in the .json file. If we didn't, we need to add the results for that date into the .json file
            found_entry = False

            #Look at every entry in the .json file for this date
            for entry in wins_log:
                #If you found the date, mark "found_entry" as true and run "find_team_result" to figure out how many wins they had on this date (to account for double headers)
                if entry['gamedate'] == streak_date_str:
                    found_entry = True
                    results = entry['results']
                    win_streak, won_games = find_team_result(results, team)
                    streak_count += won_games
                    break
                    
            #If you didn't find this date in the .json file, we need to add that date in there and return back this team's result for that date
            if found_entry == False:
                wins_log, results = add_win_streak_entry(streak_date_str, wins_log)
                win_streak, won_games = find_team_result(results, team)
                streak_count += won_games

        #After the while loop ends, calculate the streak score
        win_streak_score = max(0, min(1, -0.0008 * streak_count**2 + 0.0616 * streak_count - 0.0043))

        team_info['win_streak'] = streak_count
        team_info['win_streak_score'] = win_streak_score

    #Save any dates that were added back into the .json file
    save_win_streaks(wins_log)

    return None

def find_team_result(results, team):
    #Track how many games this team has won today
    won_games_today = 0
    #Initalize win_streak to be true and set to false if they lost a game on this date
    win_streak = True

    #Find this team's results for this day
    for result_team, result in results.items():
        if result_team == team:
            #Check if they played a double header on this day. If they lost the second game of the day, don't check the first game. If they won, add one to "won_games_today" 
            #and then check the next game.  
            if 'game_2' in result: 
                if result['game_2'] == 'w':
                    won_games_today += 1
                else:
                    win_streak = False
                    break
            #If the team won their second game of the double header or if they didn't play a double header, check the first game of that day to see if they won and add 
            #one to "won_games_today"
            if result['game_1'] == 'w':
                won_games_today += 1
            #If this team lost, end the winning streak
            else:
                win_streak = False
            break

    return win_streak, won_games_today
            
def add_win_streak_entry(streak_date_str, wins_log):
    #Track team results for this day and the result for the team that prompted getting this date 
    results = {}
    #Find this teams game for the current streak_date
    prior_games = statsapi.schedule(date=streak_date_str)

    #Look through every game this day.
    if prior_games:
        for game in prior_games:
            #Don't consider this game if it wasn't a regular season game
            if game.get('game_type') != 'R':
                continue
            #If there's no winning team listed, then that game got postponed, so skip it.
            if 'winning_team' not in game or 'losing_team' not in game:
                continue
            winning_team = game['winning_team']
            losing_team = game['losing_team']

            #If the team is already in results, then this game is the second game of a double header, so save it as game_2. Otherwise, treat it as game_1 
            if winning_team in results:
                results[winning_team]['game_2'] = 'w'                
            else:
                results[winning_team] = {'game_1': 'w'}
            
            if losing_team in results:
                results[losing_team]['game_2'] = 'l'
            else:                
                results[losing_team] = {'game_1': 'l'}

    #Insert the date and results into the win_streaks dictionary 
    wins_log.append({
        'gamedate': streak_date_str,
        'results': results
    })
            
    return wins_log, results
