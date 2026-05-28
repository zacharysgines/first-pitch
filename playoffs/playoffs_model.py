from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


DATA_PATH = Path(__file__).with_name("gl_gb_historical.csv")
TRAIN_MAX_SEASON = 2021
SEASON_LENGTH = 162
MODEL_FEATURES = [
    "games_left",
    "season_progress",
    "games_back",
    "gb_per_game_left",
    "gb_per_sqrt_game_left",
    "urgency",
    "late_gb",
]


def _build_model() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("polynomial", PolynomialFeatures(degree=3, include_bias=False)),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=0.5,
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )


def _load_training_data(data_path: Path = DATA_PATH) -> pd.DataFrame:
    data = pd.read_csv(data_path)
    required_columns = {
        "season",
        "games_left",
        "gb_division",
        "gb_playoff_cutline",
        "won_division",
        "made_playoffs_current_format",
    }
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Historical playoff data is missing columns: {missing}")

    return data


def _make_model_features(data: pd.DataFrame) -> pd.DataFrame:
    games_left = data["games_left"].astype(float).clip(lower=1.0)
    games_back = data["games_back"].astype(float)
    season_progress = ((SEASON_LENGTH - games_left) / (SEASON_LENGTH - 1)).clip(
        lower=0.0,
        upper=1.0,
    )

    features = pd.DataFrame(
        {
            "games_left": games_left,
            "season_progress": season_progress,
            "games_back": games_back,
            "gb_per_game_left": games_back / games_left,
            "gb_per_sqrt_game_left": games_back / np.sqrt(games_left),
            "urgency": 1.0 / games_left,
            "late_gb": games_back * season_progress**2,
        }
    )
    return features[MODEL_FEATURES]


def _late_season_sample_weight(games_left: pd.Series) -> pd.Series:
    games_left = games_left.astype(float).clip(lower=1.0)
    return 1.0 + 200.0 / games_left**1.5


def _fit_single_model(
    data: pd.DataFrame,
    gb_column: str,
    target_column: str,
    train_max_season: int = TRAIN_MAX_SEASON,
) -> Pipeline:
    train_data = data.loc[data["season"] <= train_max_season].copy()
    if train_data.empty:
        train_data = data.copy()

    train_data["games_back"] = train_data[gb_column]
    model = _build_model()
    model.fit(
        _make_model_features(train_data),
        train_data[target_column],
        model__sample_weight=_late_season_sample_weight(train_data["games_left"]),
    )
    return model


@lru_cache(maxsize=1)
def get_playoff_models() -> dict[str, Pipeline]:
    data = _load_training_data()
    playoff_train_data = data.loc[data["made_playoffs_current_format"] == 1].copy()
    return {
        "playoff": _fit_single_model(
            data,
            gb_column="gb_playoff_cutline",
            target_column="made_playoffs_current_format",
        ),
        "division_given_playoff": _fit_single_model(
            playoff_train_data,
            gb_column="gb_division",
            target_column="won_division",
        ),
    }


def _season_progress_weight(games_left: float) -> float:
    progress = (SEASON_LENGTH - max(float(games_left), 1.0)) / (SEASON_LENGTH - 1)
    return float(min(max(progress, 0.0), 1.0) ** 1.5)


def _predict_raw_probability(model: Pipeline, games_left: float, games_back: float) -> float:
    features = _make_model_features(
        pd.DataFrame(
            [
                {
                    "games_left": max(float(games_left), 1.0),
                    "games_back": float(games_back),
                }
            ]
        )
    )
    return float(model.predict_proba(features)[0][1])


def _predict_probability(model: Pipeline, games_left: float, games_back: float) -> float:
    games_left = max(float(games_left), 1.0)
    raw_probability = _predict_raw_probability(model, games_left, games_back)
    neutral_probability = _predict_raw_probability(model, games_left, 0.0)
    progress_weight = _season_progress_weight(games_left)
    return neutral_probability + progress_weight * (
        raw_probability - neutral_probability
    )


def get_next_game_odds_changes(
    games_left: float,
    gb_playoff_cutline: float,
    gb_division: float,
) -> tuple[float, float]:
    """Return next-game playoff and division odds swings.

    A win is modeled as reducing games back by 0.5 and a loss as increasing it
    by 0.5, with both outcomes consuming one remaining game.
    """

    models = get_playoff_models()
    next_games_left = max(float(games_left) - 1.0, 1.0)

    playoff_probability_if_win = _predict_probability(
        models["playoff"],
        games_left=next_games_left,
        games_back=float(gb_playoff_cutline) - 0.5,
    )
    playoff_probability_if_loss = _predict_probability(
        models["playoff"],
        games_left=next_games_left,
        games_back=float(gb_playoff_cutline) + 0.5,
    )
    division_given_playoff_if_win = _predict_probability(
        models["division_given_playoff"],
        games_left=next_games_left,
        games_back=float(gb_division) - 0.5,
    )
    division_given_playoff_if_loss = _predict_probability(
        models["division_given_playoff"],
        games_left=next_games_left,
        games_back=float(gb_division) + 0.5,
    )

    division_probability_if_win = (
        playoff_probability_if_win * division_given_playoff_if_win
    )
    division_probability_if_loss = (
        playoff_probability_if_loss * division_given_playoff_if_loss
    )

    division_prob_change = division_probability_if_win - division_probability_if_loss
    playoff_prob_change = playoff_probability_if_win - playoff_probability_if_loss

    return division_prob_change, playoff_prob_change


def get_next_game_odds_change_dict(
    games_left: float,
    gb_playoff_cutline: float,
    gb_division: float,
) -> dict[str, float]:
    division_prob_change, playoff_prob_change = get_next_game_odds_changes(
        games_left=games_left,
        gb_playoff_cutline=gb_playoff_cutline,
        gb_division=gb_division,
    )
    return {
        "division_prob_change": division_prob_change,
        "playoff_prob_change": playoff_prob_change,
    }


def evaluate_models(
    data_path: Path = DATA_PATH,
    train_max_season: int = TRAIN_MAX_SEASON,
) -> dict[str, dict[str, Any]]:
    """Evaluate the two models using seasons after train_max_season as test data."""

    data = _load_training_data(data_path)
    evaluations: dict[str, dict[str, Any]] = {}
    playoff_model = _fit_single_model(
        data,
        "gb_playoff_cutline",
        "made_playoffs_current_format",
        train_max_season,
    )
    conditional_division_model = _fit_single_model(
        data.loc[data["made_playoffs_current_format"] == 1].copy(),
        "gb_division",
        "won_division",
        train_max_season,
    )

    test_data = data.loc[data["season"] > train_max_season].copy()
    if test_data.empty:
        test_data = data.loc[data["season"] <= train_max_season].copy()

    test_data["games_back"] = test_data["gb_playoff_cutline"]
    playoff_probability = playoff_model.predict_proba(
        _make_model_features(test_data)
    )[:, 1]

    test_data["games_back"] = test_data["gb_division"]
    division_given_playoff_probability = conditional_division_model.predict_proba(
        _make_model_features(test_data)
    )[:, 1]
    division_probability = playoff_probability * division_given_playoff_probability

    model_outputs = {
        "playoff": (
            test_data["made_playoffs_current_format"],
            playoff_probability,
            int((data["season"] <= train_max_season).sum()),
        ),
        "division": (
            test_data["won_division"],
            division_probability,
            int(
                (
                    (data["season"] <= train_max_season)
                    & (data["made_playoffs_current_format"] == 1)
                ).sum()
            ),
        ),
    }

    for model_name, (actual, predicted_probability, train_rows) in model_outputs.items():
        predicted_class = (predicted_probability >= 0.5).astype(int)
        evaluations[model_name] = {
            "train_seasons": f"{int(data['season'].min())}-{train_max_season}",
            "test_seasons": (
                f"{train_max_season + 1}-{int(data['season'].max())}"
                if data["season"].max() > train_max_season
                else f"{int(data['season'].min())}-{train_max_season}"
            ),
            "train_rows": train_rows,
            "test_rows": int(len(test_data)),
            "accuracy": float(accuracy_score(actual, predicted_class)),
            "roc_auc": float(roc_auc_score(actual, predicted_probability)),
            "log_loss": float(log_loss(actual, predicted_probability)),
        }

    return evaluations


if __name__ == "__main__":
    odds = get_next_game_odds_changes(70, 2, 5)
    print(odds[0])
