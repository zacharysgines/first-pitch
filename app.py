import streamlit as st
from GetScores import ScoreGames
from datetime import date, datetime, timedelta, timezone
import html
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Streamlit still handles layout/state, but most of the visual presentation in this
# file is custom HTML/CSS injected with st.markdown. Treat this file more like a
# single-page HTML app that happens to use Streamlit for state/query params/data.
st.set_page_config(
    page_title="First Pitch",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Typography Assets ----
# These <link> tags load the fonts/icons used by the custom HTML sections below.
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Playball&display=swap" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">',
    unsafe_allow_html=True
)

# ---- Global CSS ----
# Streamlit generates the outer DOM, but nearly all styling here is applied to
# Streamlit's wrappers and to raw HTML fragments rendered later in this file.
st.markdown(
    """
    <style>
        
        /* WHOLE PAGE */
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: #F4F1E8 !important;
            color-scheme: light !important;
            forced-color-adjust: none !important;
        }

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
            margin: -4.15rem 0 1rem 0;
            text-align: center;
            position: relative;
        }

        .header-menu-link {
            position: absolute;
            top: 0.95rem;
            left: 1rem;
            z-index: 1002;
            width: 46px;
            height: 46px;
            min-height: 46px;
            border: none;
            border-radius: 50%;
            background: rgba(244, 241, 232, 0.96);
            color: #1F2A44;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18);
            padding: 0;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .header-menu-link,
        .header-menu-link:link,
        .header-menu-link:visited,
        .header-menu-link:hover,
        .header-menu-link:active,
        .header-menu-link:focus,
        .header-menu-link:focus-visible {
            color: #1F2A44 !important;
            text-decoration: none !important;
            border-radius: 50% !important;
            outline: none !important;
        }

        .nav-link-form {
            margin: 0;
        }

        button.header-menu-link,
        button.nav-close-button,
        button.nav-link-button {
            appearance: none;
            -webkit-appearance: none;
        }

        .header-menu-link .material-symbols-outlined {
            font-family: "Material Symbols Outlined" !important;
            font-size: 1.65rem;
            line-height: 1;
        }

        .header-menu-link:hover,
        .header-menu-link:active,
        .header-menu-link:focus,
        .header-menu-link:focus-visible {
            width: 46px;
            height: 46px;
            min-height: 46px;
            border-radius: 50%;
            padding: 0;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18);
            transform: none;
        }

        .menu-drawer {
            position: fixed;
            inset: 0;
            z-index: 1000;
            pointer-events: none;
        }

        .menu-overlay {
            position: fixed;
            inset: 0;
            background: rgba(13, 20, 33, 0.28);
            backdrop-filter: blur(3px);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.18s ease;
            display: block;
            text-decoration: none;
            pointer-events: none;
        }

        .nav-panel-shell {
            position: fixed;
            top: 0;
            left: 0;
            bottom: 0;
            width: min(260px, 78vw);
            z-index: 1001;
            padding: 1.15rem 1rem 1.25rem 1rem;
            background: linear-gradient(180deg, #1F2A44 0%, #243553 100%);
            border-right: 1px solid rgba(244, 241, 232, 0.12);
            box-shadow: 14px 0 40px rgba(0, 0, 0, 0.22);
            overflow-y: auto;
            transform: translateX(-102%);
            transition: transform 0.22s ease;
        }

        .menu-drawer:target {
            pointer-events: auto;
        }

        .menu-drawer:target .menu-overlay {
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
        }

        .menu-drawer:target .nav-panel-shell {
            transform: translateX(0);
        }

        .menu-drawer:target + .top-banner .header-menu-link {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }

        .nav-panel-brand {
            padding: 0.25rem 0 1rem 0;
            color: #F4F1E8;
        }

        .nav-panel-title {
            font-family: "Playball", cursive !important;
            font-size: 2rem;
            line-height: 1.1;
            margin-top: 0.35rem;
        }

        .nav-link-button {
            width: 100%;
            border: none;
            background: transparent;
            color: #F4F1E8;
            font-weight: 700;
            padding: 0.4rem 0;
            text-align: left;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            box-sizing: border-box;
            font-size: 1rem;
        }

        .nav-link-form + .nav-link-form {
            margin-top: 0.5rem;
        }

        .nav-menu-item + .nav-menu-item {
            margin-top: 0.5rem;
        }

        .nav-panel-brand + .nav-menu-item {
            margin-top: 1rem;
        }

        .nav-link-button:hover {
            color: #D9A441;
        }

        .nav-link-button.active {
            color: #D9A441;
            text-decoration: none;
        }

        .nav-link-button .material-symbols-outlined {
            font-family: "Material Symbols Outlined" !important;
            font-size: 1.25rem;
            line-height: 1;
        }

        .nav-close-row {
            margin-bottom: 0.8rem;
        }

        .nav-close-button {
            width: 44px;
            height: 44px;
            min-height: 44px;
            border-radius: 999px;
            border: 1px solid rgba(244, 241, 232, 0.24);
            background: rgba(244, 241, 232, 0.08);
            color: #F4F1E8;
            font-size: 1.15rem;
            padding: 0;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
        }

        .page-transition-overlay {
            position: fixed;
            inset: 0;
            z-index: 1200;
            display: flex;
            align-items: center;
            justify-content: center;
            background:
                linear-gradient(180deg, rgba(31, 42, 68, 0.94) 0%, rgba(36, 53, 83, 0.90) 100%);
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
            transition: opacity 0.18s ease, visibility 0.18s ease;
        }

        .page-transition-overlay.is-visible {
            opacity: 1;
            visibility: visible;
        }

        .page-transition-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
            color: #F4F1E8;
        }

        .page-transition-title {
            font-family: "Playball", cursive !important;
            font-size: 2rem;
            line-height: 1;
        }

        .page-transition-subtitle {
            font-size: 0.82rem;
            letter-spacing: 0.16em;
            font-weight: 700;
            opacity: 0.82;
        }

        .page-transition-spinner {
            width: 26px;
            height: 26px;
            border: 3px solid rgba(244, 241, 232, 0.25);
            border-top-color: #F4F1E8;
            border-radius: 50%;
            animation: first-pitch-spin 0.8s linear infinite;
        }

        .info-shell {
            max-width: 860px;
            margin: 0.75rem auto 0 auto;
            padding: 0 1.5rem 2rem 1.5rem;
        }

        .info-title {
            color: #1F2A44;
            font-size: 2rem;
            font-weight: 800;
            margin: 0.35rem 0 0.6rem 0;
        }

        .info-body {
            color: #344055 !important;
            font-size: 1rem;
            line-height: 1.65;
        }

        .info-body p,
        .info-body li,
        .info-body strong,
        .info-list,
        .info-list li {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
        }

        .contact-plain {
            margin-top: 3rem;
            text-align: center;
        }

        .contact-plain a,
        .contact-plain a:link,
        .contact-plain a:visited {
            color: #1F2A44;
            text-decoration: underline;
        }

        .info-list {
            margin: 0;
            padding-left: 1.2rem;
        }

        .info-list li + li {
            margin-top: 0.55rem;
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
            position: relative;
        }

        div.st-key-date_toolbar div[data-testid="stHorizontalBlock"] {
            max-width: var(--date-input-width);
            margin: 0 auto;
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
            color: #1F2A44 !important;
            -webkit-text-fill-color: #1F2A44 !important;
            forced-color-adjust: none !important;
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

        /* CALENDAR INPUT */
        div.st-key-date_toolbar div[data-baseweb="input"] {
            padding-right: 0 !important;
            background-color: #F4F1E8 !important;
            border: 1px solid #ccc !important;
            border-radius: 7px !important;
            box-shadow: none !important;
            forced-color-adjust: none !important;
        }

        div.st-key-date_toolbar div[data-baseweb="input"]:focus-within {
            border: 1px solid #ccc !important;
            box-shadow: none !important;
        }

        div[data-testid="stDateInput"] {
            max-width: var(--date-input-width);
            width: 100%;
            margin: 0 auto;
            position: relative;
        }

        div[data-testid="stDateInput"] input {
            background-color: #F4F1E8 !important;
            border: 1px solid #ccc !important;
            border-radius: 7px;
            padding: 8px 40px 8px 14px;
            width: 100%;
            font-size: 16px;
            color: #1F2A44 !important;
            -webkit-text-fill-color: #1F2A44 !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231F2A44' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='18' rx='2' ry='2'/%3E%3Cline x1='16' y1='2' x2='16' y2='6'/%3E%3Cline x1='8' y1='2' x2='8' y2='6'/%3E%3Cline x1='3' y1='10' x2='21' y2='10'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 18px 18px;
            box-shadow: none !important;
            outline: none !important;
            appearance: none !important;
            -webkit-appearance: none !important;
            forced-color-adjust: none !important;
        }

        div[data-testid="stDateInput"] label {
            display: none;
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
            color: #1F2A44 !important;
            -webkit-text-fill-color: #1F2A44 !important;
            forced-color-adjust: none !important;
        }

        .team-record {
            font-size: 1rem;
            font-weight: 400;
            color: #555 !important;
            -webkit-text-fill-color: #555 !important;
            forced-color-adjust: none !important;
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
                margin: -4.15rem 0 1rem 0;
                padding: 1.1rem 1rem 1.35rem 1rem;
            }

            .header-menu-link {
                top: 0.8rem;
                left: 0.75rem;
                width: 40px;
                height: 40px;
                min-height: 40px;
            }

            .header-menu-link:hover,
            .header-menu-link:active,
            .header-menu-link:focus,
            .header-menu-link:focus-visible {
                width: 40px;
                height: 40px;
                min-height: 40px;
            }

            .nav-panel-shell {
                width: min(240px, 82vw);
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

def get_query_value(key, default=None):
    """Return a single query-param value even when Streamlit stores it as a list."""
    value = st.query_params.get(key, default)
    if isinstance(value, list):
        return value[0] if value else default
    return value


def build_query_params(**updates):
    """Preserve current navigation params while allowing specific overrides/removals."""
    params = {}
    for key in ("page", "date", "tz"):
        value = get_query_value(key)
        if value not in (None, ""):
            params[key] = value

    for key, value in updates.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value

    return params


def build_hidden_inputs(params):
    """Render hidden <input> tags for the small HTML forms used in the nav drawer."""
    return "".join(
        f'<input type="hidden" name="{html.escape(str(key), quote=True)}" value="{html.escape(str(value), quote=True)}">'
        for key, value in params.items()
    )


def sync_selected_date_from_input():
    """Mirror the Streamlit date widget back into query params for shareable URLs."""
    selected = st.session_state.selected_date_input
    st.session_state.selected_date = selected
    st.query_params["date"] = selected.isoformat()


def render_methodology_page():
    """Render the static methodology page as raw HTML inside Streamlit."""
    st.markdown(
        """
        <div class="info-shell">
            <div class="info-title">What is this app?</div>
            <div class="info-body">
                <p>
                    This app started as a way for me to get better at data analytics by working with something I 
                    loved in baseball, and continued growing until it became something I’m proud enough of to share 
                    with others. I’m a huge fan of baseball, but my affiliation to any particular team has wavered 
                    through the years. I’ve always been more interested in watching the league as a whole. The 
                    problem, though, is that I never know what game to watch. Typically I would turn on MLB.tv and 
                    spend 10 minutes looking through team records, starting pitchers, division games, and even 
                    sometimes going to Baseball Reference or FanGraphs to find championship win probabilities for 
                    each game, and then after all of this I would find later that day that I missed a significant 
                    game because I didn’t know that, say, Salvador Perez was one home run away from 300.
                </p>
            </div>
            <div class="info-title">How does it work?</div>
            <div class="info-body">
                <p>
                    This app is an attempt to answer the question “What game should I watch today?” What started 
                    as a list of notable events in each game quickly turned into a full scoring algorithm for 
                    each game, each day, using a number of different factors (explanations of each factor can be 
                    found further down this page):
                </p>
                <ul class="info-list">
                    <li>Playoff implications</li>
                    <li>Starting pitchers</li>
                    <li>Milestones</li>
                    <li>MLB debuts</li>
                    <li>Winning streaks</li>
                    <li>Team strength</li>
                </ul>
                <p></p>
                <p>
                    All these factors get an individual score, and then all are aggregated into a final score from 
                    0 to 100. While these algorithms have been thoroughly evaluated and tested dozens of times, 
                    they are not a perfect representation of what games are most interesting. As you use this app, 
                    use it as a guide to get a feel for the best matchups of the day, find milestones you didn’t 
                    know were about to be hit, and never miss prospects debuting. Magnitude of differences matter 
                    more than ordinal rankings.
                </p>
                <p>
                    One thing to note with the scoring is that they will change up to the game date. As starters 
                    and lineups get announced, the model will begin to take those into account, and the scores will 
                    reflect that. Scoring updates every morning, so if lineups are announced late or players are 
                    scratched, then the score might not accurately reflect that game (hopefully this will be fixed 
                    soon!)
                </p>
                <p>
                    The final point I want to make ties back to the purpose of this app. This is not a way to make 
                    money or to use a computer to tell people what to do. I made this app because I love baseball, 
                    and I want to take part in spreading what makes the game so great. I hope this app is fun, leads 
                    you to learn more interesting things about the sport, and encourages you to embrace the joy that 
                    comes from watching games. 
                </p>
                <p>
                    Now, with that out of the way, let’s get into the details of how this model works.
                </p>
                <div class="info-title">Detailed explanation</div>
                <ul class="info-list">
                    <li><strong>Playoff implications:</strong> a homemade algorithm that determines how much this 
                    game matters to each team in terms of their chances of making the playoffs. This takes into 
                    account how many games are left in the season and how many games back (or ahead) each team is, 
                    both in divisional standings and wild card standings. Wild card standings are weighted more 
                    heavily, as this typically leads to “make the playoffs or go home” situations, whereas divisional 
                    races are often only important in seeding implications.</li>
                    <li><strong>Divisional games:</strong> top teams playing in division get a boost in order to give 
                    significance to early season games where playoffs might not be on the line, but it’s likely that 
                    the games will still matter come September. This also gives a boost when two teams are fighting 
                    for playoff positioning late in the season and they play each other, multiplying the already 
                    strong playoff implications score.</li>
                    <li><strong>Starting pitcher:</strong> the quality of each team's starting pitcher is a large 
                    factor in determining scores for games. Currently, this is based on starting pitcher ERA, 
                    however plans are to change this to FIP or WAR in the near future.</li>
                    <li><strong>Milestones:</strong> players approaching a milestone will give their teams a boost 
                    in score when they are within range of hitting that milestone in the given game. These milestones 
                    include runs scored, doubles, triples, home runs, hits, steals, RBI, and strikeouts for pitchers, 
                    in both a season and career context. Milestones for home runs, hits and strikeouts include both 
                    record chases as well as career milestones (such as 300 home runs or 1000 strikeouts), weighted by 
                    the significance of that milestone. All other stats include only record chases. Milestone scores 
                    trigger when a player gets within a reasonable range to hit that milestone in the given game, so 
                    teams won’t get a boost when a player is 10 home runs away from hitting their 700th home run.</li>
                    <li><strong>Debuts:</strong> Any starting pitcher or position player making their debut in a game 
                    will get a score boost, however top prospects (as defined by FanGraphs) will get more of a boost 
                    than unknown players. This will only include starting pitchers and players in the starting lineup, 
                    as it’s impossible to know whether a reliever or a player on the bench will actually play in the 
                    given game or not with the data available.</li>
                    <li><strong>Winning streaks:</strong> teams on longer winning streaks will get a boost to their 
                    scores.</li>
                    <li><strong>Team strength:</strong> the success of both teams are taken into account, but have 
                    relatively small impacts on the overall game score. Things like overall winning percentage and 
                    difference in winning percentage will have an impact on the overall scoring.</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_contact_page():
    """Render the static contact page."""
    st.markdown(
        """
        <div class="info-shell">
            <div class="info-body contact-plain">
                If you have any suggestions, problems, or comments, please reach out to me at zacharysgines@gmail.com
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_user_display_timezone():
    """Return the best available timezone for the current Streamlit client."""
    user_timezone_name = getattr(st.context, "timezone", None)
    if user_timezone_name:
        try:
            return ZoneInfo(user_timezone_name)
        except ZoneInfoNotFoundError:
            pass

    offset_minutes = getattr(st.context, "timezone_offset", None)
    if offset_minutes is not None:
        return timezone(timedelta(minutes=offset_minutes))

    return ZoneInfo("America/Denver")


def get_default_selected_date():
    """Return today's date using a 2 AM Mountain Time rollover."""
    mountain_now = datetime.now(ZoneInfo("America/Denver"))
    if mountain_now.hour < 2:
        mountain_now -= timedelta(days=1)
    return mountain_now.date()


# ---- Query-State Bootstrap ----
# This app uses query params instead of Streamlit multipage routing so the current
# page/date/timezone can be shared via URL and preserved across header navigation.
current_page = get_query_value("page", "home")
query_date = get_query_value("date")
home_inputs = build_hidden_inputs(build_query_params(page="home"))
methodology_inputs = build_hidden_inputs(build_query_params(page="methodology"))
contact_inputs = build_hidden_inputs(build_query_params(page="contact"))

# Each nav item is raw HTML so the drawer can use standard form submission and CSS
# transitions instead of trying to coordinate multiple Streamlit widgets.
home_menu_item = (
    '<div class="nav-menu-item">'
    '<a class="nav-link-button active" href="#">'
    '<span class="material-symbols-outlined">home</span>'
    '<span>Home</span>'
    '</a>'
    '</div>'
    if current_page == "home"
    else (
        '<div class="nav-menu-item">'
        '<form class="nav-link-form" method="get" onsubmit="return firstPitchStartPageTransition()">'
        f'{home_inputs}'
        '<button class="nav-link-button" type="submit">'
        '<span class="material-symbols-outlined">home</span>'
        '<span>Home</span>'
        '</button>'
        '</form>'
        '</div>'
    )
)

methodology_menu_item = (
    '<div class="nav-menu-item">'
    '<a class="nav-link-button active" href="#">'
    '<span class="material-symbols-outlined">analytics</span>'
    '<span>Methodology</span>'
    '</a>'
    '</div>'
    if current_page == "methodology"
    else (
        '<div class="nav-menu-item">'
        '<form class="nav-link-form" method="get" onsubmit="return firstPitchStartPageTransition()">'
        f'{methodology_inputs}'
        '<button class="nav-link-button" type="submit">'
        '<span class="material-symbols-outlined">analytics</span>'
        '<span>Methodology</span>'
        '</button>'
        '</form>'
        '</div>'
    )
)

contact_menu_item = (
    '<div class="nav-menu-item">'
    '<a class="nav-link-button active" href="#">'
    '<span class="material-symbols-outlined">mail</span>'
    '<span>Contact</span>'
    '</a>'
    '</div>'
    if current_page == "contact"
    else (
        '<div class="nav-menu-item">'
        '<form class="nav-link-form" method="get" onsubmit="return firstPitchStartPageTransition()">'
        f'{contact_inputs}'
        '<button class="nav-link-button" type="submit">'
        '<span class="material-symbols-outlined">mail</span>'
        '<span>Contact</span>'
        '</button>'
        '</form>'
        '</div>'
    )
)

# ---- Shared Header / Nav Drawer Markup ----
# This string contains both:
# 1. A tiny script for the page transition overlay + theme/date-input tweaks.
# 2. The reusable top banner and left slide-out navigation drawer.
header_html = f"""
    <script>
        function firstPitchStartPageTransition() {{
            const overlay = document.getElementById('page-transition-overlay');
            if (overlay) {{
                overlay.classList.add('is-visible');
            }}
            return true;
        }}

        function firstPitchForceLightTheme() {{
            const doc = window.parent.document;
            const root = doc.documentElement;

            root.style.colorScheme = 'light';
            root.style.setProperty('color-scheme', 'light', 'important');
            root.style.setProperty('forced-color-adjust', 'none', 'important');

            const ensureMeta = (name, content) => {{
                let meta = doc.head.querySelector(`meta[name="${{name}}"]`);
                if (!meta) {{
                    meta = doc.createElement('meta');
                    meta.name = name;
                    doc.head.appendChild(meta);
                }}
                meta.content = content;
            }};

            ensureMeta('color-scheme', 'light');
            ensureMeta('supported-color-schemes', 'light');
        }}

        function firstPitchEnableMobileDatePickerRedirect() {{
            const doc = window.parent.document;
            const isTouchDevice = window.matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0;
            if (!isTouchDevice) {{
                return;
            }}

            const dateFields = doc.querySelectorAll('div[data-testid="stDateInput"]');
            dateFields.forEach((field) => {{
                const input = field.querySelector('input');
                if (!input || input.dataset.firstPitchTouchRedirect === 'true') {{
                    return;
                }}

                input.dataset.firstPitchTouchRedirect = 'true';
                input.readOnly = true;
                input.setAttribute('inputmode', 'none');
                input.setAttribute('autocomplete', 'off');
                input.setAttribute('autocapitalize', 'off');
                input.setAttribute('spellcheck', 'false');

                const openPicker = (event) => {{
                    event.preventDefault();
                    input.blur();
                    const pickerButton =
                        field.querySelector('button[aria-label*="Choose"]') ||
                        field.querySelector('button[aria-label*="Open"]') ||
                        field.querySelector('button[aria-label*="calendar"]') ||
                        field.querySelector('button');
                    if (pickerButton) {{
                        pickerButton.click();
                    }}
                }};

                input.addEventListener('touchstart', openPicker, {{ passive: false }});
                input.addEventListener('mousedown', openPicker);
                input.addEventListener('focus', () => input.blur());
            }});
        }}

        firstPitchForceLightTheme();
        new MutationObserver(() => {{
            firstPitchForceLightTheme();
            firstPitchEnableMobileDatePickerRedirect();
        }}).observe(window.parent.document.body, {{
            childList: true,
            subtree: true
        }});
        firstPitchEnableMobileDatePickerRedirect();
    </script>
    <div id="page-transition-overlay" class="page-transition-overlay" aria-hidden="true">
        <div class="page-transition-card">
            <div class="page-transition-spinner" aria-hidden="true"></div>
            <div class="page-transition-title">First Pitch</div>
            <div class="page-transition-subtitle">LOADING PAGE</div>
        </div>
    </div>
    <div id="site-menu" class="menu-drawer">
        <a class="menu-overlay" href="#" aria-label="Close menu"></a>
        <div class="nav-panel-shell">
            <div class="nav-close-row">
                <a class="nav-close-button" href="#">Close</a>
            </div>
            <div class="nav-panel-brand">
                <div class="nav-panel-title">First Pitch</div>
            </div>
            {home_menu_item}
            {methodology_menu_item}
            {contact_menu_item}
        </div>
    </div>
    <div class="top-banner">
        <a class="header-menu-link" href="#site-menu" aria-label="Open menu">
            <span class="material-symbols-outlined">menu</span>
        </a>
        <div class="title-block">
            <span class="top-banner-title-row">
                <span class="top-banner-title-icon">sports_baseball</span>
                <span class="top-banner-title-text">First Pitch</span>
            </span>
            <div class="top-banner-divider"></div>
            <span class="subtitle">Discover the most exciting games of the day</span>
        </div>
    </div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# ---- Home Page: Selected Date + Score Fetch ----
# The home page is the only page that hits the scoring pipeline. The selected date
# is kept in session_state so reruns do not reset the control, but the query param
# remains the source of truth for shareable links.
if current_page == "home":
    st.markdown('<div class="date-filter-heading">PICK A DATE</div>', unsafe_allow_html=True)

    with st.container(key="date_toolbar"):
        if "selected_date" not in st.session_state:
            if query_date:
                try:
                    st.session_state.selected_date = datetime.strptime(query_date, "%Y-%m-%d").date()
                except ValueError:
                    st.session_state.selected_date = get_default_selected_date()
            else:
                st.session_state.selected_date = get_default_selected_date()
        elif query_date:
            try:
                query_date_value = datetime.strptime(query_date, "%Y-%m-%d").date()
                if query_date_value != st.session_state.selected_date:
                    st.session_state.selected_date = query_date_value
            except ValueError:
                pass

        if (
            "selected_date_input" not in st.session_state
            or st.session_state.selected_date_input != st.session_state.selected_date
        ):
            st.session_state.selected_date_input = st.session_state.selected_date

        st.date_input(
            "Game Date",
            key="selected_date_input",
            format="MM/DD/YYYY",
            label_visibility="collapsed",
            on_change=sync_selected_date_from_input,
        )

        selected_date = st.session_state.selected_date

    date_str = selected_date.strftime("%m/%d/%Y")

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
else:
    games = []

# ---- Game Card Helpers ----
def score_class(score):
    """Map a 0-100 game score to the CSS pill color used on each card."""
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
    """Build the detail lines shown beneath each game card."""
    notes = []
    
    # These helpers stay nested because they only exist to turn the score JSON
    # for one game into the short note strings shown on that game's card.
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

    def displayable_rank(value):
        if value is None:
            return None

        try:
            return None if value != value else int(value)
        except (TypeError, ValueError):
            return None

    def format_debut_note(player):
        name = player.get('name')
        pos = player.get('pos')

        if name is None or pos is None:
            return None

        name_text = html.escape(str(name))
        pos_text = html.escape(str(pos))
        mlb_rank = displayable_rank(player.get('mlb_rank'))
        org_rank = displayable_rank(player.get('org_rank'))
        pos_rank = displayable_rank(player.get('pos_rank'))
        org = player.get('org')

        rank_bits = []
        if mlb_rank is not None:
            rank_bits.append(f"#{html.escape(str(mlb_rank))} MLB")
        if org_rank is not None and org:
            rank_bits.append(
                f"#{html.escape(str(org_rank))} {html.escape(str(org))}"
            )
        if pos_rank is not None:
            rank_bits.append(f"#{html.escape(str(pos_rank))} {pos_text}")

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

def format_game_status(game):
    game_datetime = game.get("game_datetime")

    display_timezone = get_user_display_timezone()
    scheduled_dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00")).astimezone(display_timezone)
    timezone_abbr = scheduled_dt.tzname() or ""
    if " " in timezone_abbr:
        timezone_abbr = "".join(word[0] for word in timezone_abbr.split() if word)
    return f'{scheduled_dt.strftime("%I:%M %p").lstrip("0")} {timezone_abbr}'.strip()

# ---- Final Page Render ----
# At this point all shared state/header/date-selection work is done. The remaining
# logic is just "which page should render" plus the home-page game-card loop.
if current_page == "methodology":
    render_methodology_page()
elif current_page == "contact":
    render_contact_page()
elif games:
    for game in games:
        score = game['score']
        color_class = score_class(score)
        notes = build_game_notes(game)
        game_status = html.escape(str(format_game_status(game)))
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

        # Build one self-contained HTML card so the CSS can control layout the
        # same way a handwritten HTML page would.
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
    st.markdown('<div class="no-games-msg">No scores to display.</div>', unsafe_allow_html=True)
