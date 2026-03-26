import statsapi
import json
import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DISPLAY_TIMEZONE = ZoneInfo("America/Denver")


def LoadSavedLineups():
    try:
        with open("scores/lineups.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def GetLineup(game):
    gameid = game['game_id']
    away_team = game['away_name']
    home_team = game['home_name']
    home_pitcher = game['home_probable_pitcher']
    away_pitcher = game['away_probable_pitcher']

    box = statsapi.boxscore_data(gameid)

    game_lineup = {
        "away_team": away_team,
        "home_team": home_team,
        "away_lineup": [],
        "home_lineup": [],
        "away_pitcher": None,
        "home_pitcher": None,
        "lineup_hash": "",
        "lineup_confirmed": False
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
                game_lineup[lineup_key].append(lineup_player)

            if player_name == starting_pitcher:
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
                game_lineup[pitcher_key] = pitcher_data

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

    hash_string = json.dumps(hash_input, sort_keys=True)
    game_lineup["lineup_hash"] = hashlib.md5(hash_string.encode()).hexdigest()

    return game_lineup


def GetAllLineups(games):
    if not games:
        return None

    first_game_datetime = games[0].get("game_datetime")
    if not first_game_datetime:
        return None

    scheduled_date = datetime.fromisoformat(first_game_datetime.replace("Z", "+00:00")).astimezone(DISPLAY_TIMEZONE).date()
    if scheduled_date != datetime.now(DISPLAY_TIMEZONE).date():
        return None

    saved_lineups = LoadSavedLineups()
    game_lineups = {}

    for game in games:
        gameid = game["game_id"]
        game_key = f"game_{gameid}"
        game_datetime = game.get("game_datetime")

        # Preserve the original pregame snapshot once a game has started.
        # Same-day reruns should only refresh lineups for games that have not
        # started yet, otherwise debut flags and pregame milestone baselines can
        # disappear as live stats begin updating.
        if game_datetime:
            scheduled_dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
            if scheduled_dt <= datetime.now(timezone.utc) and game_key in saved_lineups:
                game_lineups[game_key] = saved_lineups[game_key]
                continue

        game_lineups[game_key] = GetLineup(game)

    with open("scores/lineups.json", "w") as f:
        json.dump(game_lineups, f, indent=4)

    return None


def LineupsChanged(games):
    saved_lineups = LoadSavedLineups()

    for game in games:
        game_datetime = game.get("game_datetime")
        if game_datetime:
            scheduled_dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
            if scheduled_dt <= datetime.now(timezone.utc):
                continue

        gameid = game["game_id"]
        game_key = f"game_{gameid}"

        current_game_data = GetLineup(game)
        current_hash = current_game_data["lineup_hash"]

        saved_hash = saved_lineups.get(game_key, {}).get("lineup_hash")

        if current_hash != saved_hash:
            return True

    return False
