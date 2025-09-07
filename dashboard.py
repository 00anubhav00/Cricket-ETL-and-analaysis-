import os
import pandas as pd
import streamlit as st
import altair as alt

BASE_PATH = "cricket/analysis"
SUBFOLDERS = {
    "all_json": "All International Matches",
    "ipl_json": "IPL Matches",
    "mdms_json": "Multiday Matches",
    "odis_json": "ODI Matches",
    "t20s_json": "T20 International Matches",
    "tests_json": "Test Matches"
}

# ---------- Helpers ----------
def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def get_teams(folder):
    team_dir = os.path.join(BASE_PATH, folder, "team")
    if os.path.exists(team_dir):
        return [d for d in os.listdir(team_dir) if os.path.isdir(os.path.join(team_dir, d))]
    return []

def get_players(folder, team=None):
    player_dir = os.path.join(BASE_PATH, folder, "player")
    if os.path.exists(player_dir):
        return [d for d in os.listdir(player_dir) if os.path.isdir(os.path.join(player_dir, d))]
    return []

# ---------- Dashboard Renderer ----------
def show_dashboard(folder, title, team=None):
    st.header(f"📊 {title}" + (f" - {team}" if team else ""))

    ball_df = load_csv(os.path.join(BASE_PATH, folder, "ballbyball.csv"))
    info_df = load_csv(os.path.join(BASE_PATH, folder, "info_summary.csv"))
    matches_df = load_csv(os.path.join(BASE_PATH, folder, f"{folder}_matches.csv"))
    player_dir = os.path.join(BASE_PATH, folder, "player")

    # --- Filter by team if selected ---
    if team and not matches_df.empty:
        team_matches = matches_df[matches_df["teams"].str.contains(team, na=False)]
        valid_match_ids = team_matches["match_id"].unique()
        ball_df = ball_df[ball_df["match_id"].isin(valid_match_ids)]
        info_df = info_df[info_df["match_id"].isin(valid_match_ids)]
        matches_df = matches_df[matches_df["match_id"].isin(valid_match_ids)]

    if ball_df.empty:
        st.warning("No ball-by-ball data available for this selection.")
        return

    # Runs Distribution
    st.subheader("📊 Runs Distribution (0,1,2,3,4,6)")
    runs_counts = ball_df["runs_batter"].value_counts().reindex([0,1,2,3,4,6], fill_value=0).reset_index()
    runs_counts.columns = ["runs_batter", "count"]
    st.altair_chart(alt.Chart(runs_counts).mark_arc().encode(theta="count:Q", color="runs_batter:N"))
    st.table(runs_counts)

    # Wicket Types
    st.subheader("📊 Wicket Types")
    wk_counts = ball_df["wicket_type"].value_counts().reset_index()
    wk_counts.columns = ["wicket_type", "count"]
    st.altair_chart(alt.Chart(wk_counts).mark_arc().encode(theta="count:Q", color="wicket_type:N"))
    st.table(wk_counts)

    # Extras Types
    st.subheader("📊 Extras Types")
    ex_counts = ball_df["extras_type"].value_counts().reset_index()
    ex_counts.columns = ["extras_type", "count"]
    st.altair_chart(alt.Chart(ex_counts).mark_arc().encode(theta="count:Q", color="extras_type:N"))
    st.table(ex_counts)

    # Totals
    st.subheader("📋 Totals")
    totals = {
        "Total Runs": ball_df["runs_total"].sum(),
        "Total Wickets": ball_df["wicket_type"].notna().sum(),
        "Total Extras": ball_df["runs_extras"].sum(),
        "Total Balls": len(ball_df)
    }
    st.table(pd.DataFrame(totals.items(), columns=["Metric","Value"]))

    # Top 10 Run Scorers
    st.subheader("🏏 Top 10 Run Scorers")
    run_data = []
    if os.path.exists(player_dir):
        for pname in os.listdir(player_dir):
            batter_csv = os.path.join(player_dir, pname, "batter.csv")
            if os.path.exists(batter_csv):
                df = load_csv(batter_csv)
                if team: df = df[df["match_id"].isin(valid_match_ids)]
                run_data.append((pname, df["runs_batter"].sum()))
    run_df = pd.DataFrame(run_data, columns=["player","runs"]).sort_values("runs", ascending=False).head(10)
    st.bar_chart(run_df.set_index("player")["runs"])

    # Top 10 Wicket Takers
    st.subheader("🎯 Top 10 Wicket Takers")
    wk_data = []
    if os.path.exists(player_dir):
        for pname in os.listdir(player_dir):
            bowler_csv = os.path.join(player_dir, pname, "bowler.csv")
            if os.path.exists(bowler_csv):
                df = load_csv(bowler_csv)
                if team: df = df[df["match_id"].isin(valid_match_ids)]
                wk_data.append((pname, df["wicket_type"].notna().sum()))
    wk_df = pd.DataFrame(wk_data, columns=["player","wickets"]).sort_values("wickets", ascending=False).head(10)
    st.bar_chart(wk_df.set_index("player")["wickets"])

    # Top 10 Fielders
    st.subheader("👐 Top 10 Fielders (Catches + Runouts)")
    fld_data = []
    if os.path.exists(player_dir):
        for pname in os.listdir(player_dir):
            fielder_csv = os.path.join(player_dir, pname, "fielder.csv")
            if os.path.exists(fielder_csv):
                df = load_csv(fielder_csv)
                if team: df = df[df["match_id"].isin(valid_match_ids)]
                catches = (df["wicket_type"]=="caught").sum()
                runouts = (df["wicket_type"]=="run out").sum()
                fld_data.append((pname, catches+runouts, catches, runouts))
    fld_df = pd.DataFrame(fld_data, columns=["player","total","catches","runouts"]).sort_values("total", ascending=False).head(10)
    st.bar_chart(fld_df.set_index("player")["total"])
    st.table(fld_df)

    # Toss Analysis
    if not info_df.empty:
        st.subheader("🪙 Toss Wins by Team")
        toss_counts = info_df["toss_winner"].value_counts().reset_index()
        toss_counts.columns = ["team","count"]
        st.bar_chart(toss_counts.set_index("team")["count"])
        st.table(toss_counts)

        st.subheader("🪙 Toss Decision (Bat/Field) by Team")
        if "toss_winner" in info_df.columns and "toss_decision" in info_df.columns:
            toss_decision_counts = info_df.groupby(["toss_winner","toss_decision"]).size().reset_index(name="count")
            toss_chart = alt.Chart(toss_decision_counts).mark_bar().encode(
                x="toss_winner:N", y="count:Q", color="toss_decision:N"
            ).properties(title="Toss Decision by Team")
            st.altair_chart(toss_chart, use_container_width=True)
            st.table(toss_decision_counts)

    # Player of the Match
    if not matches_df.empty and "player_of_match" in matches_df.columns:
        st.subheader("🌟 Player of the Match Awards")
        pom_counts = matches_df["player_of_match"].value_counts().reset_index()
        pom_counts.columns = ["player","count"]
        st.bar_chart(pom_counts.set_index("player")["count"].head(10))
        st.table(pom_counts)

    # Match Winners
    if not matches_df.empty and "outcome.winner" in matches_df.columns:
        st.subheader("🏆 Match Winners")
        win_counts = matches_df["outcome.winner"].value_counts().reset_index()
        win_counts.columns = ["team","wins"]
        st.bar_chart(win_counts.set_index("team")["wins"])
        st.table(win_counts)

        if "outcome.by.wickets" in matches_df.columns or "outcome.by.runs" in matches_df.columns:
            st.subheader("📋 Win Margins")
            margin_df = matches_df[["outcome.winner","outcome.by.wickets","outcome.by.runs","outcome.result"]].dropna(how="all")
            st.table(margin_df.head(20))  # preview only

# ---------- Streamlit UI ----------
st.set_page_config(page_title="🏏 Cricket Dashboard 2001 to 2025", layout="wide")
st.title("🏏 Cricket Dashboard 2001 to 2025")

match_type = st.selectbox("Select Match Type", [""] + list(SUBFOLDERS.keys()), format_func=lambda x: SUBFOLDERS.get(x, ""))
team = st.selectbox("Select Team", [""] + (get_teams(match_type) if match_type else []))
player = st.selectbox("Select Player", [""] + (get_players(match_type, team) if match_type else []))

# ---------- Default / Competition Views ----------
if not match_type and not team and not player:
    show_dashboard("all_json", "All International Matches")

elif match_type and not team and not player:
    show_dashboard(match_type, SUBFOLDERS[match_type])

elif match_type and team and not player:
    show_dashboard(match_type, SUBFOLDERS[match_type], team=team)

elif match_type and team and player:
    st.header(f"⭐ Player Analysis: {player} ({team}, {SUBFOLDERS[match_type]})")
    st.info("Player-specific charts coming soon!")
