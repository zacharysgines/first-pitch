import math
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_projections
def records(teams, standings):
    projections = load_projections()

    #Make sure there's standings. If not, it's the first day of the season, use projections.
    if standings:
        for division in standings.values():
            for team in division['teams']:  
                #Save each teams wins, losses and games played
                team_name = team['name']
                team_info = teams[team_name]
                current_wins = team['w']
                current_losses = team['l']
                games_left = 162 - (current_wins + current_losses)

                #Get each teams projected records
                for proj_team in projections:
                    if proj_team['Name'] == team_name:
                        proj_wins = proj_team['Wins']
                        proj_wp = round(proj_wins / 162, 3)

                #Calculate the weighted wp based on the current number of games played
                #Once there have been 60 games, it will be 50-50 projections and current standings
                #By 120 games played, it's 100% current standings
                weighted_wp = (current_wins + (proj_wp * games_left)) / 162

                #Pass current record and weighted wp into calc_score to get the scores and save
                #them to team_info
                calc_score(weighted_wp, team_info, current_wins, current_losses, 162 - games_left)
                
    #If it's the first day of the season, just use the projected wp instead of the weighted one
    else:
        for proj_team in projections:
            team_info = teams[proj_team['Name']]
            proj_wins = proj_team['Wins']
            proj_wp = round(proj_wins / 162, 3)

            #Pass projected wp to calc_score to get wp score and 0 for team wins and losses for the 
            #first day of the season
            calc_score(proj_wp, team_info, 0, 0, 162)

    #Get the adjusted division leader for each division so we can calculate games back
    division_leaders = {}
    for team in teams:
        team_info = teams[team]
        division = team_info['division']
        division_info = division_leaders.setdefault(division, {})
        games_over_500 = team_info['adjusted_wins'] - team_info['adjusted_losses']

        if not division_info or games_over_500 > division_info['games_over_500']:
            division_info['team'] = team
            division_info['wins'] = team_info['adjusted_wins']
            division_info['losses'] = team_info['adjusted_losses']
            division_info['games_over_500'] = games_over_500

    #Use adjusted wins and losses to calculate each team's games back in the division
    for team in teams:
        team_info = teams[team]
        division = team_info['division']
        division_info = division_leaders[division]
        games_back = ((division_info['wins'] - team_info['adjusted_wins']) + (team_info['adjusted_losses'] - division_info['losses'])) / 2

        if games_back <= 0:
            team_info['games_back'] = 0
        else:
            team_info['games_back'] = games_back

    return None

def calc_score(wp, team_info, current_wins, current_losses, games_played):
    #After getting the winning percentage either through the weighted team record or through 
    #projections, calculate the wp score with a piecewise function
    if wp >= 0.685:
        wp_score = 0.3
    elif wp >= 0.600:
        wp_score = -14.166 * wp**2 + 19.456 * wp - 6.3762
    elif wp >= 0.400:
        wp_score = 0.5193 * wp - 0.1113
    elif wp >= 0.309:
        wp_score = 7.8024 * wp**2 - 4.5431 * wp + 0.6597
    else:
        wp_score = 0

    #Save the current wins, losses and wp_score to the team_info
    team_info['wins'] = current_wins
    team_info['losses'] = current_losses
    team_info['adjusted_wins'] = round(games_played * wp)
    team_info['adjusted_losses'] = games_played - round(games_played * wp)
    team_info['win_perc'] = wp
    team_info['wp_score'] = wp_score

    return None

