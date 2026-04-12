from save_load import load_projections
import math

def records(teams, standings):
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
                    win_perc = round(wins / games_played, 3)
                    team_name['win_perc'] = win_perc
                else:
                    projections = load_projections()
                    for proj_team in projections:
                        if proj_team['Name'] == team['name']:   #Find this team in projected_records.csv
                            win_perc = round(proj_team['Wins'] / 162, 3)
                            team_name['win_perc'] = win_perc
                            break

                if win_perc < .45:
                    wp_score = 0
                else:   
                    wp_score = .000007 * math.exp(15.091 * win_perc)
                team_name['wp_score'] = wp_score

    else:
        projections = load_projections()
        for team in projections:
            team_name = teams[team['Name']]
            team_name['wins'] = 0
            team_name['losses'] = 0
            win_perc = round(team['Wins'] / 162, 3)
            team_name['win_perc'] = win_perc

            if win_perc < .45:
                wp_score = 0
            else:   
                wp_score = .000007 * math.exp(15.091 * win_perc)
            team_name['wp_score'] = wp_score
    return None