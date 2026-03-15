import streamlit as st
import streamlit.components.v1 as components
from GetScores import ScoreGames
from datetime import date, datetime
import html
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
        
        /* WHOLE PAGE */
        div[data-testid="stMainBlockContainer"],
        .main .block-container {
            max-width: 100% !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            background-color: #F4F1E8;            
        }

        /* MAIN PAGE FONT */
        .stApp, .stApp * {
            font-family: "Nunito", sans-serif !important;
        }

        /* HEADER BAR */
        .top-banner {
            background-color: #1F2A44;
            padding: 1.5rem 2rem 2rem 2rem;
            margin: -4rem 0 1rem 0;
            text-align: center;
        }

        /* HEADER TITLE CONTAINER */
        .top-banner .title-block {
            color: #F4F1E8;
            font-size: 3rem;
            line-height: 1.2;
            background-color: #1F2A44;
        }

        /* HEADER TITLE & LOGO */
        .top-banner-title-row {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
        }

        /* HEADER TITLE */
        .top-banner-title-text {
            font-family: "Playball", cursive !important;
            line-height: 1;
        }

        /* HEADER LOGO */
        .top-banner-title-icon {
            font-family: "Material Symbols Outlined" !important;
            font-size: 2.5rem;
            color: #F4F1E8;
            line-height: 1;
        }

        /* HEADER SUBTITLE */
        .top-banner .subtitle {
            display: block;
            font-size: 1.2rem;
            margin-top: 0.25rem;
        }

        /* HEADER DIVIDER */
        .top-banner-divider {
            width: min(520px, 82%);
            height: 1px;
            margin: 0.25rem auto 0.6rem auto;
            background-color: #D9A441;
        }

        /* DATE CONTAINER */
        div.st-key-date_toolbar {
            margin: 0.75rem auto 0.35rem auto;
            --date-input-width: 190px;
        }

        /* DATE LABEL */
        .date-filter-heading {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.8rem auto 0.2rem auto;
            font-size: 0.8rem;
            letter-spacing: 0.12em;
            font-weight: 700;
        }

        /* DATE DIVIDER */
        .date-filter-heading::before,
        .date-filter-heading::after {
            content: "";
            flex: 1;
            height: 1px;
            background-color: #d4d7dd;
        }

        /* LOADING MESSAGE */
        .loading-msg {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.65rem;
            width: 100%;
            text-align: center;
            color: #1F2A44;
            font-size: 18px;
            margin: 0.4rem 0 0.8rem 0;
        }

        .loading-spinner {
            width: 18px;
            height: 18px;
            border: 3px solid rgba(31, 42, 68, 0.2);
            border-top-color: #1F2A44;
            border-radius: 50%;
            animation: first-pitch-spin 0.8s linear infinite;
            flex: 0 0 auto;
        }

        @keyframes first-pitch-spin {
            to { transform: rotate(360deg); }
        }

        /* NO GAMES MESSAGE */
        .no-games-msg {
            text-align: center;
            font-size: 18px;
        }

        /* CALENDAR ICON */
        div.st-key-date_toolbar div[data-baseweb="input"] {
            padding-right: 0 !important;
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
            align-items: flex-start;
        }

        .team-wrapper {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 0.35rem;
            padding-left: .5rem;
            padding-right: 6.2rem;
        }

        .game-time {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6c7280;
            margin-bottom: 0.2rem;
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

            .game-time {
                font-size: 0.74rem;
                margin-bottom: 0.15rem;
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

components.html(
    """
    <script>
      const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const currentUrl = new URL(window.parent.location.href);
      if (browserTz && currentUrl.searchParams.get("tz") !== browserTz) {
        currentUrl.searchParams.set("tz", browserTz);
        window.parent.location.replace(currentUrl.toString());
      }

      const applyDateInputMobileFix = () => {
        const inputs = window.parent.document.querySelectorAll('div[data-testid="stDateInput"] input');
        inputs.forEach((input) => {
          input.readOnly = true;
          input.setAttribute('inputmode', 'none');
          input.style.caretColor = 'transparent';
        });
      };

      applyDateInputMobileFix();
      new MutationObserver(applyDateInputMobileFix).observe(window.parent.document.body, {
        childList: true,
        subtree: true,
      });
    </script>
    """,
    height=0,
)

# Convert to MM/DD/YYYY for GetScores
date_str = selected_date.strftime("%m/%d/%Y")
browser_timezone = st.query_params.get("tz")

# ---- Get games for selected date ----
if "last_loaded_date" not in st.session_state:
    st.session_state.last_loaded_date = None

if st.session_state.last_loaded_date != date_str:
    loading_placeholder = st.empty()
    loading_placeholder.markdown(
        """
        <div class="loading-msg">
            <span class="loading-spinner" aria-hidden="true"></span>
            <span>Loading scores...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    games = ScoreGames(date_str)
    loading_placeholder.empty()
else:
    games = ScoreGames(date_str)

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

    def format_count(diff_value, singular_label, plural_label):
        if diff_value == 1:
            return singular_label
        return plural_label

    def format_milestone_note(milestone, scope):
        stat_labels = {
            'runs': ('run', 'runs'),
            'doubles': ('double', 'doubles'),
            'triples': ('triple', 'triples'),
            'home_runs': ('home run', 'home runs'),
            'hits': ('hit', 'hits'),
            'steals': ('stolen base', 'stolen bases'),
            'rbi': ('RBI', 'RBI'),
            'strikeouts': ('strikeout', 'strikeouts'),
            'wins': ('win', 'wins'),
        }

        stat = milestone.get('stat')
        player = milestone.get('player')
        diff = milestone.get('diff')
        chase_type = milestone.get('milestone_type', milestone.get('type'))
        target = milestone.get('target')

        if stat not in stat_labels or player is None or diff is None or chase_type is None:
            return None

        singular_label, plural_label = stat_labels[stat]
        diff_label = format_count(diff, singular_label, plural_label)
        player_text = html.escape(str(player))
        diff_text = html.escape(str(diff))

        if chase_type == 'Milestone' and target is not None:
            target_text = html.escape(str(target))
            stat_text = html.escape(plural_label)
            scope_text = html.escape(scope)
            return (
                f"<strong>{player_text}</strong>: "
                f"{diff_text} {diff_label} away from {target_text} {scope_text} {stat_text}"
            )

        if chase_type == 'Record':
            scope_text = "single season" if scope == 'season' else "all time"
            record_label = html.escape(singular_label)
            return (
                f"<strong>{player_text}</strong>: "
                f"{diff_text} {diff_label} away from breaking the {scope_text} {record_label} record"
            )

        return None

    def format_debut_note(player):
        name = player.get('name')
        pos = player.get('pos')

        if name is None or pos is None:
            return None

        name_text = html.escape(str(name))
        pos_text = html.escape(str(pos))
        mlb_rank = player.get('mlb_rank')
        org_rank = player.get('org_rank')
        pos_rank = player.get('pos_rank')
        org = player.get('org')

        rank_bits = []
        if mlb_rank is not None:
            rank_bits.append(f"#{html.escape(str(int(mlb_rank)))} MLB")
        if org_rank is not None and org:
            rank_bits.append(
                f"#{html.escape(str(int(org_rank)))} {html.escape(str(org))}"
            )
        if pos_rank is not None:
            rank_bits.append(f"#{html.escape(str(int(pos_rank)))} {pos_text}")

        rank_text = f" ({', '.join(rank_bits)})" if rank_bits else ""

        return f"<strong>{name_text}{rank_text}</strong>: MLB debut"

    if game['away_era'] is not None and game['away_era'] <= 3.50:
        away_era_text = html.escape(format_era(game['away_era']))
        if game['away_era_source'] == 'real':
            notes.append(
                f"<strong>{html.escape(str(game['away_starter']))}</strong>"
                f": {away_era_text} ERA"
            )
        elif game['away_era_source'] == 'projected':
            notes.append(
                f"<strong>{html.escape(str(game['away_starter']))}</strong>"
                f": {away_era_text} ERA (projected)"
            )

    if game['home_era'] is not None and game['home_era'] <= 3.50:
        home_era_text = html.escape(format_era(game['home_era']))
        if game['home_era_source'] == 'real':
            notes.append(
                f"<strong>{html.escape(str(game['home_starter']))}</strong>"
                f": {home_era_text} ERA"
            )
        elif game['home_era_source'] == 'projected':
            notes.append(
                f"<strong>{html.escape(str(game['home_starter']))}</strong>"
                f": {home_era_text} ERA (projected)"
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

    for milestone in game.get('away_career_milestones', []):
        note = format_milestone_note(milestone, 'career')
        if note:
            notes.append(note)

    for milestone in game.get('home_career_milestones', []):
        note = format_milestone_note(milestone, 'career')
        if note:
            notes.append(note)

    for milestone in game.get('away_season_milestones', []):
        note = format_milestone_note(milestone, 'season')
        if note:
            notes.append(note)

    for milestone in game.get('home_season_milestones', []):
        note = format_milestone_note(milestone, 'season')
        if note:
            notes.append(note)

    for debut in game.get('away_debuts', []):
        note = format_debut_note(debut)
        if note:
            notes.append(note)

    for debut in game.get('home_debuts', []):
        note = format_debut_note(debut)
        if note:
            notes.append(note)

    return notes

def format_game_status(game, browser_timezone_name):
    game_status = game.get("game_status", game.get("status", ""))

    if game_status in {"Final", "Completed Early"}:
        return "Final"
    if game_status == "In Progress":
        return game.get("status", "In Progress")

    game_datetime = game.get("game_datetime")
    if not game_datetime:
        return game.get("status", "")

    try:
        browser_timezone = ZoneInfo(browser_timezone_name) if browser_timezone_name else ZoneInfo("America/Denver")
    except ZoneInfoNotFoundError:
        browser_timezone = ZoneInfo("America/Denver")

    scheduled_dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00")).astimezone(browser_timezone)
    timezone_abbr = scheduled_dt.tzname() or ""
    if " " in timezone_abbr:
        timezone_abbr = "".join(word[0] for word in timezone_abbr.split() if word)
    return f'{scheduled_dt.strftime("%I:%M %p").lstrip("0")} {timezone_abbr}'.strip()

# ---- Page content ----
if games:
    for game in games:
        score = game['score']
        color_class = score_class(score)
        notes = build_game_notes(game)
        game_status = html.escape(str(format_game_status(game, browser_timezone)))
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
            f'<div class="game-time">{game_status}</div>'
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
