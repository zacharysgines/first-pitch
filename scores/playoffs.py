from SaveLoad import LoadProjections

def Playoff_Imp(standings, teams):
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

            #Playoff Urgency
                #If you are the first place team, calculate how many games ahead of the second place team you are. Otherwise, calculate games back from first place
                if team['div_rank'] == '1':
                    gb = abs(losses - div_name['second_l'])
                else:
                    gb = abs(losses - div_name['first_l'])

                #Wild Card Games Back
                wcgb = abs(losses - gb_ref['leagues'][league])

                #Calculate division urgency and wild card urgency, then use those two to get overall urgency
                div_urgency = max(0, 1/(gb + gl) * (1 - gb/gl))
                wc_urgency = max(0, 1/(wcgb + gl) * (1 - wcgb/gl))
                urgency = (div_urgency + wc_urgency*3) / 4

                teams[team['name']]['playoff_imp'] = urgency

            #Divisional Score
                first_l = div_name['first_l']
                
                #If there have been more than 50 games, use the current records, otherwise use projections
                if gp >= 50:
                    teams[team['name']]['games_back'] =  losses - first_l
                else:
                    Playoff_Imp_Proj(teams)
    else:
        Playoff_Imp_Proj(teams)

    return None

#Only run if there have been <50 games this year
def Playoff_Imp_Proj(teams):
    #Load Projections
    projections = LoadProjections()

    #Initialize dictionary to hold lowest loss total for each division
    min_losses = {}

    #First pass: find top team by losses in each division
    for team in projections:
        division = team['Division']
        losses = 162 - team['Wins']

        if division not in min_losses or losses < min_losses[division]:
            min_losses[division] = losses
    
    #Second pass, calculate games back for each team and set playoff implications = 0 if it's the first game of the season
    for team in projections:
        division = team['Division']
        team_name = teams[team['Name']]

        #If we haven't already calculated this teams playoff implications, set it to 0 (first game of the season). Otherwise, leave it alone.
        team_name.setdefault('playoff_imp', 0)
        
        #Get first place teams wp, current teams wp, and calculate the current teams wp back
        first_l = min_losses[division]
        losses = 162 - team['Wins']
        team_name['games_back'] =  losses - first_l

    return None