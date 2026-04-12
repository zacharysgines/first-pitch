from datetime import datetime, timedelta
import json
import statsapi

def LoadWinStreaks():
    #Load win_streaks.json
    with open("scores/win_streaks.json", "r") as f:
        raw_text = f.read().strip()
        if not raw_text:
            return []
        win_streaks = json.loads(raw_text)
    
    return win_streaks

def SaveWinStreaks(win_streaks):
    with open("scores/win_streaks.json", "w") as f:
        json.dump(win_streaks, f, indent=2)

def winning_streak(standings, teams, date_obj):
    #If the current date we're getting scores for is later than today, or if it's the first day of the season, then don't get a score for winning streaks
    if (not standings) or (date_obj.date() > datetime.today().date()):
        for team in teams:
            teams[team]['winning_streak'] = 0
        return None

    win_streaks = LoadWinStreaks()
    streak_year = date_obj.year

    for team in teams:
        #Intially define their winning streak to be true and 0 games. Set the start of the streak date to today
        winning_streak = True
        streak_count = 0
        streak_date = date_obj.date()

        #While the winning streak is still true, keep going back one day at a time and see if the team won and add 1 to "streak_count"
        while winning_streak:
            #Decrease the date by one
            streak_date -= timedelta(days=1)
            if streak_date.year < streak_year:
                break
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

        if streak_count == 0:
            win_streak_score = 0
        else:
            win_streak_score = 0.002 * streak_count**2 - 0.0047 * streak_count + 0.0083

        teams[team]['win_streak_score'] = win_streak_score

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
            if game.get('game_type') != 'R':
                continue
            #If there's no winning team listed, then that game got postponed, so skip it.
            if 'winning_team' not in game or 'losing_team' not in game:
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
