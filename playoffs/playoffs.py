import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_projections
from playoffs.playoffs_model import get_next_game_odds_changes


def games_back(team_wins, team_losses, reference_wins, reference_losses):
    return ((reference_wins - team_wins) + (team_losses - reference_losses)) / 2


def playoff_imp(standings, teams):
    #Initialize dictionary to hold first and second place teams in each division and 4th place team in wild card
    gb_ref = {
        'divisions': {},
        'leagues': {}
    }
    
    #If there haven't been any games this year, use playoff_imp_proj() instead
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
                wins = team['w']
                losses = team['l']
                div_rank = team['div_rank']
                wc_rank = team['wc_rank']

                #If you're the first team in the division, save your wins and losses to gb_ref for this division
                if div_rank == '1':
                    div_name['first_w'] = wins
                    div_name['first_l'] = losses
                #If you're the second team in the division, save your wins and losses to gb_ref for this division
                elif div_rank == '2':                
                    div_name['second_w'] = wins
                    div_name['second_l'] = losses

                #If you're the 4th team in the wild card, save your wins and losses to gb_ref for your league
                if wc_rank == '4':
                    gb_ref['leagues'][league] = {
                        'w': wins,
                        'l': losses,
                    }

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

            #Playoff Implications
                #If you are the first place team, calculate signed games back from second place.
                #Otherwise, calculate signed games back from first place. Negative means ahead of the reference.
                if team['div_rank'] == '1':
                    gb = games_back(wins, losses, div_name['second_w'], div_name['second_l'])
                else:
                    gb = games_back(wins, losses, div_name['first_w'], div_name['first_l'])

                #Signed games back from the playoff cutline. Negative means ahead of the cutline.
                wc_cutline = gb_ref['leagues'][league]
                wcgb = games_back(wins, losses, wc_cutline['w'], wc_cutline['l'])

                #Calculate division implications and wild card implications, then use those two to get overall playoff implications
                if gl == 0:
                    gl += 1
                
                div_change, wc_change = get_next_game_odds_changes(gl, wcgb, gb)

                if gb > gl:
                    div_change = 0
                if wcgb > gl:
                    wc_change = 0

                playoff_imp = min(1, max(0, 2.0 * wc_change + 1.0 * div_change))

                teams[team['name']]['playoff_imp'] = playoff_imp
    else:
        projections = load_projections()
        for team in projections:
            teams[team['Name']]['playoff_imp'] = 0

    return None
