import streamlit as st
from main import GetScores
from datetime import date
import html

# ---- Include Font Awesome ----
st.markdown(
    '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/css2?family=Playball&display=swap" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">',
    unsafe_allow_html=True
)

# ---- Custom CSS ----
st.markdown(
    """
    <style>
        html, body {
            overflow-x: hidden;
        }

        div[data-testid="stMainBlockContainer"],
        .main .block-container {
            max-width: 100% !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        /* Page background */
        .reportview-container, .stApp {
            background-color: #F4F1E8;
            font-family: "Nunito", sans-serif;
        }

        .stApp, .stApp * {
            font-family: "Nunito", sans-serif !important;
        }

        /* Top banner */
        .top-banner {
            background-color: #1F2A44;
            padding: 1.5rem 2rem 2rem 2rem;
            width: auto;
            margin: -4rem 0 1rem 0;
            text-align: center;
            box-sizing: border-box;
        }

        .top-banner .title-block {
            color: #F4F1E8;
            font-size: 3rem;
            line-height: 1.2;
            font-weight: 700;
            font-family: "Playball", cursive !important;
        }

        .top-banner-title-row {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-family: "Playball", cursive !important;
        }

        .top-banner-title-text {
            font-family: "Playball", cursive !important;
            font-weight: 400 !important;
            line-height: 1;
        }

        .top-banner-title-icon {
            font-family: "Material Symbols Outlined" !important;
            font-size: 2.5rem;
            color: #F4F1E8;
            line-height: 1;
            font-weight: normal;
            font-style: normal;
            display: inline-block;
            margin-right: 5px;
        }

        .top-banner .subtitle {
            display: block;
            color: #F4F1E8;
            font-size: 1.2rem;
            font-weight: 400;
            margin-top: 0.25rem;
        }

        .top-banner-divider {
            width: min(520px, 82%);
            height: 1px;
            margin: 0.25rem auto 0.6rem auto;
            background-color: #D9A441;
        }

        /* Date section */
        div.st-key-date_toolbar {
            max-width: 430px;
            margin: 0.75rem auto 0.35rem auto;
            padding: 0;
            --date-input-width: 190px;
        }

        .date-filter-heading {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            width: auto;
            max-width: none;
            margin: 0.8rem auto 0.2rem auto;
            padding: 0 1.15rem;
            color: #1F2A44;
            font-size: 0.8rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
            box-sizing: border-box;
        }

        .date-filter-heading::before,
        .date-filter-heading::after {
            content: "";
            flex: 1;
            height: 1px;
            background-color: #d4d7dd;
        }

        div.st-key-loading_block {
            padding-left: 0.85rem;
        }

        .no-games-msg {
            margin-left: 0.85rem;
            color: #1F2A44;
        }

        div.st-key-date_toolbar div[data-baseweb="input"] {
            padding-right: 0 !important;
            padding-left: 0 !important;
        }

        div[data-testid="stDateInput"] {
            max-width: var(--date-input-width);
            width: 100%;
            margin: 0 auto;
            position: relative;
        }

        div[data-testid="stDateInput"] input {
            background-color: #F4F1E8;
            border: 1px solid #ccc;
            border-radius: 7px;
            padding: 8px 40px 8px 14px;
            width: 100%;
            font-size: 16px;
            color: #1F2A44;
            -webkit-text-fill-color: #1F2A44;
        }

        div[data-testid="stDateInput"] label {
            display: none;
        }

        div[data-testid="stDateInput"]::after {
            content: "\\f133";
            font-family: "Font Awesome 6 Free";
            font-weight: 400;
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 16px;
            color: #1F2A44;
            pointer-events: none;
        }

        /* Game card styling */
        .game-card {
            background-color: white;
            margin: 0.7rem auto;
            border-radius: 0.5rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            max-width: 600px;
            overflow: hidden;
            position: relative;
        }

        .game-main-row {
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .team-wrapper {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 0.35rem;
            padding-left: .5rem;
            padding-right: 6.2rem;
        }

        .team-column {
            width: auto;
        }

        .team-line {
            display: flex;
            align-items: baseline;
            gap: 0.45rem;
        }

        .team-name {
            font-size: 1.2rem;
            font-weight: 700;
        }

        .team-record {
            font-size: 1rem;
            font-weight: 400;
            color: #555;
        }

        .score-bubble {
            color: white;
            font-weight: 700;
            padding: 0.3rem 1.5rem;
            border-radius: 1.5rem;
            font-size: 1.1rem;
            min-width: 2.5rem;
            height: 2.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            position: absolute;
            top: 1rem;
            right: 1rem;
            margin-left: 0;
        }

        .game-details {
            position: relative;
            background-color: #ebebeb;
            border: 1px solid #d6d6d6;
            border-radius: 0;
            margin: 0 0 1.1rem 0;
            padding: 0.55rem 0.9rem 0.65rem 2rem;
        }

        .game-details::before {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            width: 20px;
            background-color: #1F2A44;
        }

        .game-note-item {
            font-size: 0.9rem;
            color: #333;
            line-height: 1.35;
        }

        .game-note-item + .game-note-item {
            margin-top: 0.25rem;
        }

        .game-pill-row {
            margin: 0 0.9rem 0.9rem 0.9rem;
        }

        .game-pill {
            display: inline-block;
            background-color: #ffffff;
            color: #1F2A44;
            border: 1.5px solid #1F2A44;
            border-radius: 999px;
            padding: 0.28rem 0.72rem;
            font-size: 0.8rem;
            font-weight: 600;
            line-height: 1;
            text-transform: capitalize;
        }

        .game-pill + .game-pill {
            margin-left: 0.45rem;
        }

        .game-pill-division {
            background-color: #ffffff;
            color: #1F2A44;
            border: 1.5px solid #1F2A44;
        }

        /* Responsive layout for phones */
        @media (max-width: 700px) {
            .top-banner {
                width: 100%;
                margin: -4rem 0 1rem 0;
                padding: 1.1rem 1rem 1.35rem 1rem;
            }

            .top-banner .title-block {
                font-size: 2rem;
            }

            .top-banner .subtitle {
                font-size: 1rem;
            }

            div.st-key-date_toolbar {
                width: 100%;
                max-width: 96vw;
                padding: 0;
                box-sizing: border-box;
                --date-input-width: 150px;
            }

            .date-filter-heading {
                margin: 0.8rem auto 0.2rem auto;
                width: 100%;
                padding: 0 0.85rem;
            }

            .game-card {
                width: 100%;
                max-width: 92vw;
                margin: 0.7rem auto;
                box-sizing: border-box;
            }

            .game-main-row {
                padding: 0.8rem 0.9rem;
                align-items: flex-start;
            }

            .team-wrapper {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.35rem;
                padding-left: 0;
                padding-right: 4.8rem;
            }

            .team-column {
                width: auto;
            }

            .team-line {
                gap: 0.4rem;
            }

            .team-name {
                font-size: 1.02rem;
                line-height: 1.2;
            }

            .team-record {
                font-size: 0.88rem;
            }

            .score-bubble {
                margin-left: 0;
                padding: 0.25rem 1rem;
                min-width: 2.15rem;
                height: 2.15rem;
                font-size: 0.98rem;
                top: 0.8rem;
                right: 0.8rem;
            }

            .game-details {
                margin: 0 0 0.9rem 0;
                padding: 0.5rem 0.7rem 0.55rem 1.85rem;
            }

            .game-pill-row {
                margin: 0 0.65rem 0.7rem 0.65rem;
            }
        }

        /* Score color ranges */
        .score-red    { background-color: #C23B22; }
        .score-orange { background-color: #C47A2C; }
        .score-yellow { background-color: #D9A441; }
        .score-green  { background-color: #2E6F3E; }
        .score-blue   { background-color: #1F2A44; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- Header ----
st.markdown(
    """
    <div class="top-banner">
        <div class="title-block">
            <span class="top-banner-title-row">
                <span class="top-banner-title-icon">sports_baseball</span>
                <span class="top-banner-title-text">First Pitch</span>
            </span>
            <div class="top-banner-divider"></div>
            <span class="subtitle">Discover the most exciting games of the day</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Date selector ----
st.markdown('<div class="date-filter-heading">PICK A DATE</div>', unsafe_allow_html=True)

with st.container(key="date_toolbar"):
    if "selected_date" not in st.session_state:
        # value=date.today(),  # original default
        st.session_state.selected_date = date(2025, 7, 11)  # testing default (07/11/2025)

    picked_date = st.date_input(
        "Game Date",
        value=st.session_state.selected_date,
        format="MM/DD/YYYY",
        label_visibility="collapsed"
    )

    if picked_date != st.session_state.selected_date:
        st.session_state.selected_date = picked_date

    selected_date = st.session_state.selected_date

# Convert to MM/DD/YYYY for GetScores
date_str = selected_date.strftime("%m/%d/%Y")

# ---- Get games for selected date ----
if "last_loaded_date" not in st.session_state:
    st.session_state.last_loaded_date = None

if st.session_state.last_loaded_date != date_str:
    with st.container(key="loading_block"):
        with st.spinner("Loading scores..."):
            games = GetScores(date_str)
else:
    games = GetScores(date_str)

st.session_state.last_loaded_date = date_str

# ---- Score color logic ----
def score_class(score):
    if score <= 15:
        return "score-red"
    elif score <= 35:
        return "score-orange"
    elif score <= 60:
        return "score-yellow"
    elif score <= 80:
        return "score-green"
    else:
        return "score-blue"

def build_game_notes(game):
    notes = []
    
    def format_era(era_value):
        return f"{float(era_value):.2f}"

    if game['away_era'] is not None and game['away_era'] <= 3.50:
        away_era_text = html.escape(format_era(game['away_era']))
        if game['away_era_source'] == 'this_year':
            notes.append(
                f"<strong>{html.escape(str(game['away_starter']))}</strong>"
                f": {away_era_text} ERA"
            )
        else: 
            notes.append(
                f"<strong>{html.escape(str(game['away_starter']))}</strong>"
                f": {away_era_text} ERA (last year)"
            )

    if game['home_era'] is not None and game['home_era'] <= 3.50:
        home_era_text = html.escape(format_era(game['home_era']))
        if game['home_era_source'] == 'this_year':
            notes.append(
                f"<strong>{html.escape(str(game['home_starter']))}</strong>"
                f": {home_era_text} ERA"
            )
        else:
            notes.append(
                f"<strong>{html.escape(str(game['home_starter']))}</strong>"
                f": {home_era_text} ERA (last year)"
            )

    if game['away_win_streak'] >= 5:
        notes.append(
            f"<strong>{html.escape(str(game['away_team_name']))}</strong>"
            f": {html.escape(str(game['away_win_streak']))} game winning streak"
        )

    if game['home_win_streak'] >= 5:
        notes.append(
            f"<strong>{html.escape(str(game['home_team_name']))}</strong>"
            f": {html.escape(str(game['home_win_streak']))} game winning streak"
        )

    return notes

# ---- Page content ----
if games:
    for game in games:
        score = game['score']
        color_class = score_class(score)
        notes = build_game_notes(game)
        notes_html = "".join(
            f"<div class='game-note-item'>{note}</div>"
            for note in notes
        )
        has_playoff_implications = game['away_playoff_imp'] >= 0.25 or game['home_playoff_imp'] >= 0.25
        has_division_rivals = game['max_games_back'] is not None and game['max_games_back'] <= 5
        details_html = f'<div class="game-details">{notes_html}</div>' if notes else ""
        pill_items = []
        if has_playoff_implications:
            pill_items.append('<span class="game-pill">Playoff Implications</span>')
        if has_division_rivals:
            pill_items.append('<span class="game-pill game-pill-division">Division Rivals</span>')
        pill_html = f'<div class="game-pill-row">{"".join(pill_items)}</div>' if pill_items else ""

        card_html = (
            '<div class="game-card">'
            '<div class="game-main-row">'
            '<div class="team-wrapper">'
            '<div class="team-column">'
            '<div class="team-line">'
            f'<span class="team-name">{html.escape(str(game["away_team_name"]))}</span>'
            f'<span class="team-record">({game["away_wins"]} - {game["away_losses"]})</span>'
            '</div>'
            '</div>'
            '<div class="team-column">'
            '<div class="team-line">'
            f'<span class="team-name">{html.escape(str(game["home_team_name"]))}</span>'
            f'<span class="team-record">({game["home_wins"]} - {game["home_losses"]})</span>'
            '</div>'
            '</div>'
            '</div>'
            f'<div class="score-bubble {color_class}">{score:.0f}</div>'
            '</div>'
            f'{details_html}'
            f'{pill_html}'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.markdown('<div class="no-games-msg">No games scheduled.</div>', unsafe_allow_html=True)
