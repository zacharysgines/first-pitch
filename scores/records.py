from SaveLoad import LoadProjections

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