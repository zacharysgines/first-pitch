import statsapi
import json
import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import sys
from pathlib import Path

#Find the project root path and add that path to Python's import path so we can find the files we
#need to import from
ROOT_DIR = Path(__file__).resolve().parents[1]  
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_saved_lineups, save_lineups


def get_all_lineups(games, gamedate_str):
    #Get today's date
    current_date_obj = datetime.now(ZoneInfo("America/Denver")).date()
    current_date_str = current_date_obj.strftime("%m/%d/%Y")

    #If this game is not today, don't get the lineups (lineups are only known day of game)
    if gamedate_str != current_date_str:
        return None

    #Create a dictionary to hold all games and their lineups
    game_lineups = {}

    for game in games:
        #Get the gameid
        gameid = game["game_id"]

        #Create a key in game_lineups dictionary with this game's id and set the value to the lineup returned from get_lineup
        game_lineups[gameid] = get_lineup(game)

    #Save all the lineups for this date to lineups.json
    save_lineups(gamedate_str, game_lineups)

    return None


def get_lineup(game):
    #Get information about the game from the API
    gameid = game['game_id']
    away_team = game['away_name']
    home_team = game['home_name']
    home_pitcher = game['home_probable_pitcher']
    away_pitcher = game['away_probable_pitcher']

    #Find this game in the boxscore API
    box = statsapi.boxscore_data(gameid)

    #Set up the lineup dictionary for this game
    game_lineup = {
        "away_team": away_team,
        "home_team": home_team,
        "away_lineup": [],
        "home_lineup": [],
        "away_pitcher": None,
        "home_pitcher": None,
        "lineup_hash": ""
    }

    for team_status in ('away', 'home'):
        if team_status == 'away':
            starting_pitcher = away_pitcher
            lineup_key = "away_lineup"
            pitcher_key = "away_pitcher"
        else:
            starting_pitcher = home_pitcher
            lineup_key = "home_lineup"
            pitcher_key = "home_pitcher"

        for player in box[team_status]['players'].values():
            player_name = player['person']['fullName']
            player_id = player['person']['id']

            if player.get('battingOrder'):
                #For each player in the batting order for this game, get their season stats from the boxscore API and create a dictionary for this player
                season_stats = player.get('seasonStats', {}).get('batting', {})
                lineup_player = {
                    "id": player_id,
                    "name": player_name,
                    "position": player['position']['abbreviation'],
                    "stats": {
                        "runs": season_stats.get('runs', 0),
                        "doubles": season_stats.get('doubles', 0),
                        "triples": season_stats.get('triples', 0),
                        "home_runs": season_stats.get('homeRuns', 0),
                        "hits": season_stats.get('hits', 0),
                        "steals": season_stats.get('stolenBases', 0),
                        "rbi": season_stats.get('rbi', 0)
                    }
                }
                #Add this player to the lineup dictionary for this game
                game_lineup[lineup_key].append(lineup_player)

            if player_name == starting_pitcher:
                #If this player if the starting pitcher, get their season stats from the boxscore API and create a dictionary for this player
                season_stats = player.get('seasonStats', {}).get('pitching', {})
                pitcher_data = {
                    "id": player_id,
                    "name": player_name,
                    "stats": {
                        "strikeouts": season_stats.get('strikeOuts', 0),
                        "era": season_stats.get('era', 0),
                        "ip": season_stats.get('inningsPitched', 0)
                    }
                }
                #Add this player to the lineup dictionary for this game
                game_lineup[pitcher_key] = pitcher_data

    #Sort all the batter id's and get the pitcher ID to build the lineup hash to uniquely identify this games lineup so we can see if it needs to be changed later
    away_batter_ids = sorted(player["id"] for player in game_lineup["away_lineup"])
    home_batter_ids = sorted(player["id"] for player in game_lineup["home_lineup"])
    away_pitcher_id = game_lineup["away_pitcher"]["id"] if game_lineup["away_pitcher"] else None
    home_pitcher_id = game_lineup["home_pitcher"]["id"] if game_lineup["home_pitcher"] else None
    hash_input = {
        "away_batter_ids": away_batter_ids,
        "home_batter_ids": home_batter_ids,
        "away_pitcher_id": away_pitcher_id,
        "home_pitcher_id": home_pitcher_id
    }

    #Create the lineup hash and add it to the game lineup
    hash_string = json.dumps(hash_input, sort_keys=True)
    game_lineup["lineup_hash"] = hashlib.md5(hash_string.encode()).hexdigest()

    return game_lineup


def lineups_changed(games, gamedate_str):
    #Get what we currently have saved in lineups.json
    saved_lineups = load_saved_lineups()
    saved_games = saved_lineups.get("games", {})
    lineup_date_str = saved_lineups.get("date")
    changed = False
    games_to_update = {}

    #If the date in lineups.json is not today, then don't check the lineups. 
    if lineup_date_str != gamedate_str:
        return {}

    #For each game, get the game's start time. If that start time has passed, don't check if this lineup has changed. Otherwise, check.
    for game in games:
        game_datetime = game.get("game_datetime")
        if game_datetime:
            scheduled_dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
            if scheduled_dt <= datetime.now(timezone.utc):
                continue

        gameid = game["game_id"]

        #Get the updated hash for this game
        current_game_data = get_lineup(game)
        current_hash = current_game_data["lineup_hash"]

        #Get the hash for this game saved in lineups.json
        saved_game_data = saved_games.get(str(gameid), {})
        saved_hash = saved_game_data.get("lineup_hash")

        #If the hash's don't match, update lineups.json with the new game data.
        if current_hash != saved_hash:
            #If the current and saved lineups don't match or the current and saved starting pitchers don't match, this evaluates to "True"
            away_changed = (
                current_game_data.get("away_lineup") != saved_game_data.get("away_lineup")
                or current_game_data.get("away_pitcher") != saved_game_data.get("away_pitcher")
            )
            home_changed = (
                current_game_data.get("home_lineup") != saved_game_data.get("home_lineup")
                or current_game_data.get("home_pitcher") != saved_game_data.get("home_pitcher")
            )

            #save true or false to games_to_update for this specific game for both the home team and away team
            games_to_update[gameid] = {
                "away": away_changed,
                "home": home_changed
            }

            #Update this lineup in lineups.json and set changed = True
            saved_games[gameid] = current_game_data
            changed = True

    #If any of the lineups have changed, save the new lineups in lineups.json
    if changed:
        save_lineups(lineup_date_str, saved_games)

    return games_to_update
