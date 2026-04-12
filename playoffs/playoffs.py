from save_load import LoadProjections
import math

def playoff_imp(standings, teams):
    #Initialize dictionary to hold first and second place teams in each division and 4th place team in wild card
    gb_ref = {}
    gb_ref['divisions'] = {}
    gb_ref['leagues'] = {}
    
    #If there haven't been any games this year, use Playoff_Imp_Proj function instead
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
                losses = team['l']
                div_rank = team['div_rank']
                wc_rank = team['wc_rank']

                #If you're the first team in the division, save your wins and losses to gb_ref for this division
                if div_rank == '1':
                    div_name['first_l'] = losses
                #If you're the second team in the division, save your losses to gb_ref for this division
                elif div_rank == '2':                
                    div_name['second_l'] = losses

                #If you're the 4th team in the wild card, save your losses to gb_ref for your league
                if wc_rank == '4':
                    gb_ref['leagues'][league] = losses

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
                #If you are the first place team, calculate how many games ahead of the second place team you are. Otherwise, calculate games back from first place
                if team['div_rank'] == '1':
                    gb = abs(losses - div_name['second_l'])
                else:
                    gb = abs(losses - div_name['first_l'])

                #Wild Card Games Back
                wcgb = abs(losses - gb_ref['leagues'][league])

                #Calculate division implications and wild card implications, then use those two to get overall playoff implications
                if gl == 0:
                    gl += 1
                
                if gb > gl:
                    div_imp = 0
                else:                                    
                    div_imp = max(0, 1.107 * math.exp(-1 * (gl/16.77)**.598) * (1 - gb / gl)**2.547)
                
                if wcgb > gl:
                    wc_imp = 0
                else:                                    
                    wc_imp = max(0, 1.107 * math.exp(-1 * (gl/16.77)**.598) * (1 - wcgb / gl)**2.547)
                
                playoff_imp = (div_imp * .4 + wc_imp * .6)

                teams[team['name']]['playoff_imp'] = playoff_imp
    else:
        teams[team['name']]['playoff_imp'] = 0

    return None