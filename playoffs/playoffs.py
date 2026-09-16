import statsapi
from datetime import datetime, timedelta
from pathlib import Path
import sys
import random
import copy
import time
from requests.exceptions import HTTPError, ConnectionError, Timeout

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))


def get_schedule(**kwargs):
    #Try the schedule request up to three times if the API has a temporary problem.
    for attempt in range(3):
        try:
            return statsapi.schedule(**kwargs)
        except HTTPError as error:
            #Retry temporary server errors and rate limits, but let other HTTP errors through.
            if error.response is None or error.response.status_code not in (429, 500, 502, 503, 504):
                raise
            #If the third attempt failed, report the error instead of continuing without a schedule.
            if attempt == 2:
                raise
        except (ConnectionError, Timeout):
            #Connection failures and timeouts also get up to three attempts.
            if attempt == 2:
                raise

        #Wait two seconds before the second attempt and four seconds before the third.
        time.sleep(2 ** (attempt + 1))


def playoff_imp(teams_info, start_date_str):
    start_date_obj = datetime.strptime(start_date_str, "%m/%d/%Y").date()
    current_year = start_date_obj.year

    #Get remaining season schedule
    remaining_games = get_schedule(start_date=start_date_str, end_date=f'12/31/{current_year}')
    remaining_schedule = [game for game in remaining_games if game.get('game_type') == 'R']

    #Get todays games
    todays_games = [game for game in remaining_schedule if datetime.strptime(game['game_date'], "%Y-%m-%d").date() == start_date_obj]

    #Get each teams current wins, losses and adjusted winning percentage
    current_standings = {}
    for team, team_info in teams_info.items():
        current_standings[team] = {
            'wins': team_info['wins'],
            'losses': team_info['losses'],
            'win_perc': team_info['adjusted_win_perc'],
            'sim_wins': 0
        }
    
    #For each game today, get the home team, away team, and set their playoff change counter for both wins today and losses today.
    playoff_change_counter = {}

    for game in todays_games:
        away_team = game['away_name']
        home_team = game['home_name']

        playoff_change_counter[game['game_id']] = {
            'away_team': away_team,
            'home_team': home_team,
            'away_win_sims': 0,
            'away_win_playoffs': 0,
            'away_loss_sims': 0,
            'away_loss_playoffs': 0,

            'home_win_sims': 0,
            'home_win_playoffs': 0,
            'home_loss_sims': 0,
            'home_loss_playoffs': 0,
        }

    playoff_probs = simulate_season(current_standings, remaining_schedule, todays_games, playoff_change_counter, start_date_str, teams_info)

    for game in playoff_probs.values():
        for team_status in ('away', 'home'):
            if team_status == 'away':
                team_name = game['away_team']
                playoff_change = game['away_playoff_change']
            else:
                team_name = game['home_team']
                playoff_change = game['home_playoff_change']

            if playoff_change < 0.01:
                playoff_imp_score = 0
            else:
                playoff_imp_score = 0.974*playoff_change**3 - 2.84*playoff_change**2 + 2.94*playoff_change + 0.0347

            teams_info[team_name]['playoff_imp_score'] = playoff_imp_score

    return None


def simulate_season(current_standings, remaining_schedule, todays_games, playoff_change_counter, start_date_str, teams_info):
    #Reuse historical matchup schedules across this run's simulations. Start fresh on the next run.
    matchup_cache = {}
    # #Set number of simulations
    n = 10000
    
    #Simulate rest of season n times
    for i in range(n):
        #Get current standings
        sim_standings = copy.deepcopy(current_standings)

        #Set simulated wins to 0 for each team
        for stats in sim_standings.values():
            stats['sim_wins'] = 0

        #Track the results of each simulated game
        simulated_results = {}

        #Get each remaining game
        for game in remaining_schedule:
            #Get info for each game and calculate win probability for the away team
            away_team = game['away_name']
            home_team = game['home_name']
            away_wp = sim_standings[away_team]['win_perc']
            home_wp = sim_standings[home_team]['win_perc']
            away_win_prob = (away_wp - away_wp * home_wp) / (away_wp + home_wp - 2 * away_wp * home_wp)

            #Simulate winner of the game based on win probability using a random number generator
            if random.random() < away_win_prob:
                sim_standings[away_team]['sim_wins'] += 1
                simulated_results[game['game_id']] = 'away'
            else:
                sim_standings[home_team]['sim_wins'] += 1
                simulated_results[game['game_id']] = 'home'

        #Get the teams that made the playoffs in this simulation
        playoff_teams = made_playoffs(sim_standings, start_date_str, teams_info, simulated_results, remaining_schedule, matchup_cache)

        #See who won each game today in this simulation and update the playoff change counter for each 
        #team based on whether they won or lost today and whether they made the playoffs in this simulation
        for game in todays_games:
            game_id = game['game_id']
            away_team = game['away_name']
            home_team = game['home_name']

            #Get the simulated results for this game
            simulated_result = simulated_results[game_id]
            #Get current counts for this game from the playoff change counter
            counts = playoff_change_counter[game_id]

            #If the away team won todays game, add one to away_wins and one to home_losses
            if simulated_result == 'away':
                counts['away_win_sims'] += 1
                counts['home_loss_sims'] += 1
                #If the away team won and made the playoffs, add one to away_win_playoffs
                if away_team in playoff_teams:
                    counts['away_win_playoffs'] += 1
                #If the away team won and the home team made the playoffs, add one to home_loss_playoffs
                if home_team in playoff_teams:
                    counts['home_loss_playoffs'] += 1
            #If the home team won todays game, add one to home_wins and one to away_losses
            else:
                counts['home_win_sims'] += 1
                counts['away_loss_sims'] += 1
                #If the home team won and made the playoffs, add one to home_win_playoffs
                if home_team in playoff_teams:
                    counts['home_win_playoffs'] += 1                
                #If the home team won and the away team made the playoffs, add one to away_loss_playoffs
                if away_team in playoff_teams:
                    counts['away_loss_playoffs'] += 1

    playoff_probs = calculate_playoff_prob(playoff_change_counter)

    return playoff_probs 


def made_playoffs(sim_standings, start_date_str, teams_info, simulated_results, remaining_schedule, matchup_cache=None):
    #Also allow this function to be called directly without providing a cache.
    if matchup_cache is None:
        matchup_cache = {}
    #Define current structure of MLB
    mlb = {
        'american_leauge': {
            'east': ['Tampa Bay Rays', 'New York Yankees', 'Boston Red Sox', 'Toronto Blue Jays', 'Baltimore Orioles'],
            'central': ['Chicago White Sox', 'Cleveland Guardians', 'Minnesota Twins', 'Detroit Tigers', 'Kansas City Royals'],
            'west': ['Houston Astros', 'Texas Rangers', 'Seattle Mariners', 'Athletics', 'Los Angeles Angels'],
        },
        'national_league': {
            'east': ['Atlanta Braves', 'Philadelphia Phillies', 'Miami Marlins', 'New York Mets', 'Washington Nationals'],
            'central': ['Milwaukee Brewers', 'Chicago Cubs', 'Pittsburgh Pirates', 'St. Louis Cardinals', 'Cincinnati Reds'],
            'west': ['Los Angeles Dodgers', 'San Diego Padres', 'Arizona Diamondbacks', 'San Francisco Giants', 'Colorado Rockies'],
        }
    }
    
    #List to track which teams made the playoffs in this simulation 
    playoff_teams = []
    for league in mlb.values():
        #Track division winners
        for division in league.values():
            top_wins = 0
            top_teams = []

            for team in division:
                sim_team = {
                    'team_name': team,
                    'sim_stats': sim_standings[team]
                }
                sim_season_wins = sim_team['sim_stats']['wins'] + sim_team['sim_stats']['sim_wins']
                if sim_season_wins > top_wins:
                    top_wins = sim_season_wins
                    top_teams.clear()
                    top_teams.append(sim_team)
                elif sim_season_wins == top_wins:
                    top_teams.append(sim_team)

            if len(top_teams) > 1:
                tiebreak_winner = resolve_tiebreak(start_date_str, top_teams, teams_info, simulated_results, remaining_schedule, matchup_cache)
                playoff_teams.append(tiebreak_winner)
            else:
                playoff_teams.append(top_teams[0]['team_name'])

        #List to track wild card winners
        wild_card_teams = []
        for division in league.values():
            for team in division:
                sim_team = {
                    'team_name': team,
                    'sim_stats': sim_standings[team]
                }
                sim_season_wins = sim_team['sim_stats']['wins'] + sim_team['sim_stats']['sim_wins']
                #Go through each team in the league that is not a division winner and add them to the wild card list
                if team not in playoff_teams:
                    wild_card_teams.append(sim_team)

        #Sort the wild card list based on wins
        wild_card_teams.sort(key=lambda sim_team: (
            sim_team['sim_stats']['wins'] + sim_team['sim_stats']['sim_wins']
        ), reverse=True)

        #Select one team for each of the three wild card spots
        for i in range(3):
            #The list is already sorted, so the first team has the most remaining wins
            top_team = wild_card_teams[0]
            top_wins = top_team['sim_stats']['wins'] + top_team['sim_stats']['sim_wins']

            #Collect every remaining team with that same win total
            tied_teams = []
            for team in wild_card_teams:
                team_wins = team['sim_stats']['wins'] + team['sim_stats']['sim_wins']

                if team_wins == top_wins:
                    tied_teams.append(team)

            #Select the sole leader, or resolve the tie for this spot
            if len(tied_teams) == 1:
                winner = tied_teams[0]['team_name']
            else:
                winner = resolve_tiebreak(start_date_str, tied_teams, teams_info, simulated_results, remaining_schedule, matchup_cache)

            #Add the selected team to the playoffs
            playoff_teams.append(winner)

            #Remove that team so it cannot claim another spot
            #The remaining teams stay in their original sorted order
            wild_card_teams = [team for team in wild_card_teams if team['team_name'] != winner]

    return playoff_teams


def resolve_tiebreak(start_date_str, teams, teams_info, simulated_results, remaining_schedule, matchup_cache=None):
    #Only historical API results are cached. Rebuild the records with each simulation's results below.
    if matchup_cache is None:
        matchup_cache = {}
    start_date_obj = datetime.strptime(start_date_str, "%m/%d/%Y").date()
    current_year = start_date_obj.year

    #The schedule's end date is inclusive, so stop at yesterday to exclude today's games.
    previous_date_obj = start_date_obj - timedelta(days=1)
    previous_date_str = previous_date_obj.strftime("%m/%d/%Y")

    #Each entry in teams is a dictionary, so get its team_name before looking up the team's ID.
    team_names = [team['team_name'] for team in teams]
    #Keep a separate record against each other tied team, including matchups with no games played yet.
    head_to_head = {}
    for team in team_names:
        head_to_head[team] = {}
        for opponent in team_names:
            if opponent != team:
                head_to_head[team][opponent] = {
                            'wins': 0,
                            'losses': 0
                        }

    #Get each pair only once. A vs. B also gives us B's record against A.
    for i, team in enumerate(team_names):
        for opponent in team_names[i + 1:]:
            #Both API filters use team IDs. Either team can be home or away in the returned games.
            #Sorting the IDs lets A vs. B reuse the same entry as B vs. A.
            #Include the cutoff date so records from different dates cannot be mixed.
            matchup_key = (start_date_obj, *sorted((teams_info[team]['id'], teams_info[opponent]['id'])))
            if matchup_key not in matchup_cache:
                matchup_cache[matchup_key] = get_schedule(start_date=f'01/01/{current_year}', end_date=previous_date_str, team=teams_info[team]['id'], opponent=teams_info[opponent]['id'])
            completed_games = matchup_cache[matchup_key]
            #Only completed regular-season games contribute to the historical win/loss record.
            completed_schedule = [game for game in completed_games if game.get('game_type') == 'R']

            for game in completed_schedule:                
                if game.get('winning_team'):
                    head_to_head[game['winning_team']][game['losing_team']]['wins'] += 1
                    head_to_head[game['losing_team']][game['winning_team']]['losses'] += 1
                elif game.get('status') == 'Completed Early':
                    #The API may omit the winning team for games completed early, so use the final scores.
                    #Equal scores do not give either team a win or loss.
                    if game['away_score'] == game['home_score']:
                        continue
                    if game['away_score'] > game['home_score']:
                        winner = game['away_name']
                        loser = game['home_name']
                    else:
                        winner = game['home_name']
                        loser = game['away_name']

                    #Update both records, just as we do when the API supplies the winning team.
                    head_to_head[winner][loser]['wins'] += 1
                    head_to_head[loser][winner]['losses'] += 1
                else:
                    continue

    #Go through the games played in this simulation
    for game in remaining_schedule:
        away_team = game['away_name']
        home_team = game['home_name']

        #Only count games where both teams are part of the tie
        if away_team not in team_names or home_team not in team_names:
            continue

        #Look up which side won this game in the current simulation
        simulated_winner = simulated_results[game['game_id']]

        #Get the winning and losing team names
        if simulated_winner == 'away':
            winner = away_team
            loser = home_team
        else:
            winner = home_team
            loser = away_team

        #Add the simulated win and loss to the historical head-to-head records
        head_to_head[winner][loser]['wins'] += 1
        head_to_head[loser][winner]['losses'] += 1

    #First, check whether a team had a winning record against every other tied team
    for team, opponents in head_to_head.items():
        if all(record['wins'] > record['losses'] for record in opponents.values()):
            return team

    #If no team won every season series, compare combined winning percentages
    best_win_perc = -1
    top_teams = []

    for team, opponents in head_to_head.items():
        #Add up this team's wins and losses against all other tied teams
        wins = sum(record['wins'] for record in opponents.values())
        losses = sum(record['losses'] for record in opponents.values())
        games_played = wins + losses
        win_perc = wins / games_played

        #If this team has the best percentage so far, replace the previous leaders
        if win_perc > best_win_perc:
            best_win_perc = win_perc
            top_teams = [team]

        #Keep track of teams that share the best percentage
        elif win_perc == best_win_perc:
            top_teams.append(team)
    
    #Return the winner if only one team has the highest combined percentage
    if len(top_teams) == 1:
        return top_teams[0]

    #If some teams were eliminated, restart the tiebreak with only the remaining leaders
    if len(top_teams) < len(teams):
        #top_teams contains names, but resolve_tiebreak needs the original team dictionaries
        remaining_teams = [
            team for team in teams
            if team['team_name'] in top_teams
        ]

        return resolve_tiebreak(
            start_date_str, remaining_teams, teams_info,
            simulated_results, remaining_schedule, matchup_cache
        )

    #For now, randomly choose among the teams still tied for the best percentage.
    return random.choice(top_teams)
        

def calculate_playoff_prob(playoff_change_counter):
    results = {}
    for game_id, counts in playoff_change_counter.items():
        away_team = counts['away_team']
        home_team = counts['home_team']

        #Calculate the percentage of times each team made the playoffs for each different scenario and store it in the results dictionary
        away_win_prob = counts['away_win_playoffs'] / counts['away_win_sims'] if counts['away_win_sims'] > 0 else 0
        away_loss_prob = counts['away_loss_playoffs'] / counts['away_loss_sims'] if counts['away_loss_sims'] > 0 else 0
        home_win_prob = counts['home_win_playoffs'] / counts['home_win_sims'] if counts['home_win_sims'] > 0 else 0
        home_loss_prob = counts['home_loss_playoffs'] / counts['home_loss_sims'] if counts['home_loss_sims'] > 0 else 0
        results[game_id] = {
            'away_team': away_team,
            'home_team': home_team,
            'away_win_playoffs': away_win_prob,
            'away_loss_playoffs': away_loss_prob,
            'away_playoff_change': away_win_prob - away_loss_prob,
            'home_win_playoffs': home_win_prob,
            'home_loss_playoffs': home_loss_prob,
            'home_playoff_change': home_win_prob - home_loss_prob,
        }
        
    return results
