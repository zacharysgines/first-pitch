from save_load import load_projections
import math

def records(teams, standings):
    #Make sure there's standings. If not, it's the first day of the season, use projections.
    if standings:
        for division in standings.values():
            for team in division['teams']:  
                #Save each teams wins, losses and games played
                team_name = team['name']
                team_info = teams[team_name]
                wins = team['w']
                losses = team['l']
                team_info['wins'] = wins
                team_info['losses'] = losses
                games_played = wins + losses
                
                #If a team has played more than 1/4 of their games, use their current winning percentage. 
                if games_played >= 41:
                    win_perc = round(wins / games_played, 3)
                    team_info['win_perc'] = win_perc
                #Otherwise, use their projected winning percentage.
                else:
                    projections = load_projections()
                    for proj_team in projections:
                        if proj_team['Name'] == team_name:   #Find this team in projected_records.csv
                            win_perc = round(proj_team['Wins'] / 162, 3)
                            team_info['win_perc'] = win_perc
                            break
    #If it's the first day of the season, use projected records
    else:
        projections = load_projections()
        for team in projections:
            team_info = teams[team['Name']]
            team_info['wins'] = 0
            team_info['losses'] = 0
            win_perc = round(team['Wins'] / 162, 3)
            team_info['win_perc'] = win_perc

    #After getting the winning percentage either through the team record or through projections, calculate the wp score
    if win_perc < .45:
        wp_score = 0
    else:   
        wp_score = .000007 * math.exp(15.091 * win_perc)
    team_info['wp_score'] = wp_score

    return None