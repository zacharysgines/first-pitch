import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import statsapi

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from save_load import load_pitcher_war_lookup, load_sp_projections
from starting_pitchers import find_pitcher, get_sp_stats


def get_starting_pitcher_war_scores(start_date=None, days=5):
    if start_date is None:
        start_date = date.today()

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%m/%d/%Y").date()

    sp_projections = load_sp_projections()
    war_lookup = load_pitcher_war_lookup(start_date.strftime("%m/%d/%Y"))
    pitcher_scores = []

    for day_offset in range(days):
        gamedate = start_date + timedelta(days=day_offset)
        gamedate_str = gamedate.strftime("%m/%d/%Y")

        games = statsapi.schedule(date=gamedate_str)
        regular_season_games = [
            game for game in games
            if game.get("game_type") == "R"
        ]
        if not regular_season_games:
            continue

        for game in regular_season_games:
            add_pitcher_score(
                pitcher_scores,
                gamedate_str,
                game,
                side="away",
                sp_projections=sp_projections,
                war_lookup=war_lookup,
            )

            add_pitcher_score(
                pitcher_scores,
                gamedate_str,
                game,
                side="home",
                sp_projections=sp_projections,
                war_lookup=war_lookup,
            )

    return pitcher_scores


def add_pitcher_score(
    pitcher_scores,
    gamedate_str,
    game,
    side,
    sp_projections,
    war_lookup,
):
    team_name = game[f"{side}_name"]
    opponent_side = "home" if side == "away" else "away"
    opponent_name = game[f"{opponent_side}_name"]
    probable_pitcher = game.get(f"{side}_probable_pitcher")
    if not probable_pitcher:
        return

    pitchers = statsapi.lookup_player(probable_pitcher)
    if len(pitchers) > 1:
        pitchers = find_pitcher(pitchers, game[f"{side}_id"])
    if not pitchers:
        return

    team_info = {}
    get_sp_stats(pitchers[0], team_info, sp_projections, war_lookup, team_name)

    pitcher_name = team_info.get("pitcher_name")
    if not pitcher_name:
        return

    pitcher_scores.append({
        "gamedate": gamedate_str,
        "game_id": game.get("game_id"),
        "game_datetime": game.get("game_datetime"),
        "side": side,
        "team": team_name,
        "opponent": opponent_name,
        "pitcher_name": pitcher_name,
        "pitcher_current_war": team_info.get("pitcher_current_war"),
        "pitcher_projected_war": team_info.get("pitcher_projected_war"),
        "pitcher_blended_war": team_info.get("pitcher_blended_war"),
        "war_source": team_info.get("war_source"),
        "war_score": team_info.get("war_score"),
    })


def parse_args():
    parser = argparse.ArgumentParser(
        description="Return starting pitcher WAR scores for upcoming games."
    )
    parser.add_argument(
        "--start-date",
        default=date.today().strftime("%m/%d/%Y"),
        help="Start date in MM/DD/YYYY format. Defaults to today.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Number of days to include. Defaults to 5.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pitcher_scores = get_starting_pitcher_war_scores(args.start_date, args.days)
    print(json.dumps(pitcher_scores, indent=2))


if __name__ == "__main__":
    main()
