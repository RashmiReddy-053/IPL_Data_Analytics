import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# reading & load the data from csv


def load_data():
    matches = pd.read_csv("matches.csv")
    deliveries = pd.read_csv("deliveries.csv")
    return matches, deliveries


matches, deliveries = load_data()

st.set_page_config(page_title="IPL Dashboard",
                   page_icon="ipl_loago.jpeg", layout="wide")

st.markdown(
    '<style> div.block-container </style>', unsafe_allow_html=True)
image = Image.open('ipl_logo.jpeg')

col1, col2 = st.columns([0.2, 0.8])
with col1:
    st.image(image, width=100)

    html_title = """
        <style>
            .title-test{
            font-weight:bold;
            padding:5px;
            border-radius:6px
            }
        </style>
        <center><h1 class="title-text">🏏 IPL Analytics Dashboard (2008-2024)</h1></center>"""
with col2:
    st.markdown(html_title, unsafe_allow_html=True)

col3, col4, col5 = st.columns([0.20, 0.40, 0.40])
with col3:
    box_date = str(datetime.datetime.now().strftime("%d %B %Y"))
    st.write(f"Last updated by:  \n {box_date}")


# overview metrics
col6, col7, col8 = st.columns(3)
col6.metric("🏆 Total Matches Played", matches.shape[0])
col7.metric("🏏 Total Runs Scored", deliveries["total_runs"].sum())
col8.metric("🎯 Total Wickets Taken",
            deliveries[deliveries["dismissal_kind"].notna()].shape[0])

# matches per season overview
all_seasons = pd.DataFrame({"season": list(range(2008, 2024))})

matches_per_season = (
    matches.groupby("season")["id"]
    .count()
    .reset_index()
    .rename(columns={"id": "matches"})
)
matches_per_season = matches.merge(
    matches_per_season, on="season", how="left")
matches_per_season = matches_per_season[matches_per_season["matches"] > 0]
# 2. Create the figure FIRST
fig_line = px.line(
    matches_per_season,
    x="season",
    y="matches",
    markers=True,
    title="Matches Per Season (Trend)"
)

# 3. Then update layout or scale
fig_line.update_layout(
    xaxis=dict(title="Season"),
    yaxis=dict(title="Number of Matches", range=[0, 80], dtick=10),
    height=500,
    plot_bgcolor='rgba(0,0,0,0)'
)

# 4. Show it in Streamlit
fig_line.update_traces(connectgaps=True)

st.plotly_chart(fig_line, use_container_width=True)

# Most successful teams visualisation

# Total team wins dataframe
team_wins = matches["winner"].value_counts().reset_index()
team_wins.columns = ["Team", "Wins"]


fig_team = px.bar(team_wins, x="Wins", y="Team", orientation="h",
                  title="Most Wins by Team", color="Wins")
st.plotly_chart(fig_team, use_container_width=True)

# Toss Analysis

toss_decisions = matches["toss_decision"].value_counts().reset_index()
fig_toss = px.pie(toss_decisions, names="toss_decision",
                  values="count", title="Toss Decisions (Field vs. Bat)")
st.plotly_chart(fig_toss, use_container_width=True)


# Toss to winning match strategy

# Step 1: Filter only toss winners
matches["toss_win_and_match_win"] = matches["toss_winner"] == matches["winner"]

# Step 2: Group by toss_decision and whether the team also won
toss_analysis = matches.groupby(
    ["toss_decision", "toss_win_and_match_win"]).size().reset_index(name='count')

# Step 3: Pivot to get win/loss count per toss decision
toss_pivot = toss_analysis.pivot(
    index='toss_decision', columns='toss_win_and_match_win', values='count').fillna(0)
toss_pivot.columns = ['Lost Match After Toss', 'Won Match After Toss']
toss_pivot["Total Toss Wins"] = toss_pivot.sum(axis=1)
toss_pivot["Win Percentage"] = round(
    (toss_pivot["Won Match After Toss"] / toss_pivot["Total Toss Wins"]) * 100, 2)

# Reset index for plotting
toss_pivot = toss_pivot.reset_index()

fig = go.Figure()

fig.add_trace(go.Bar(
    x=toss_pivot["toss_decision"],
    y=toss_pivot["Won Match After Toss"],
    name="Won Match After Toss",
    marker_color="green"
))

fig.add_trace(go.Bar(
    x=toss_pivot["toss_decision"],
    y=toss_pivot["Lost Match After Toss"],
    name="Lost Match After Toss",
    marker_color="red"
))

fig.update_layout(
    title="Impact of Toss Decision on Match Outcome",
    barmode="stack",
    xaxis_title="Toss Decision",
    yaxis_title="Number of Matches",
    plot_bgcolor="rgba(0,0,0,0)",
    height=500
)
st.subheader("Does Toss Decision Affect Winning?")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(toss_pivot[["toss_decision", "Won Match After Toss",
             "Lost Match After Toss", "Win Percentage"]])


# Top Run Scorers (Table + Bar Chart)

runs = deliveries.groupby(
    "batter")["batsman_runs"].sum().reset_index()
runs = runs.sort_values(
    "batsman_runs", ascending=False).head(20)

fig_batsmen = px.bar(runs, x="batter", y="batsman_runs",
                     title="Top 20 Run Scorers", color="batsman_runs")
st.plotly_chart(fig_batsmen, use_container_width=True)

# Top Wicket takers

bowler_wickets = deliveries[deliveries["dismissal_kind"].notna()]
bowler_wickets = bowler_wickets.groupby(
    "bowler")["dismissal_kind"].count().reset_index()
fig_bowlers = px.bar(bowler_wickets.sort_values("dismissal_kind", ascending=False).head(20),
                     x="bowler", y="dismissal_kind", title="Top 20 Wicket Takers", color="dismissal_kind")
st.plotly_chart(fig_bowlers, use_container_width=True)

# Batter's Performance

deliveries = deliveries.merge(
    matches[["id", "season"]], left_on="match_id", right_on="id", how="left")
selected_player = st.selectbox(
    "Select a batter", sorted(deliveries["batter"].unique()))

# Filter deliveries for the selected player
player_data = deliveries[deliveries["batter"] == selected_player]

# Group by season and sum batsman runs
season_wise = player_data.groupby("season")["batsman_runs"].sum().reset_index()
season_wise["season"] = season_wise["season"].astype(str)
season_wise = season_wise.sort_values("season")
# Plot season-wise performance
fig_player = px.line(season_wise, x="season", y="batsman_runs", markers=True,
                     title=f"{selected_player}'s Season-wise Performance")
fig_line.update_traces(connectgaps=True)
fig_player.update_layout(xaxis=dict(type='category'))
st.plotly_chart(fig_player, use_container_width=True)


# Bowler analysis

st.title("IPL Bowler Analysis")
bowler_name = st.selectbox(
    "Select a Bowler", sorted(deliveries['bowler'].unique()))
bowler_data = deliveries[deliveries['bowler'] == bowler_name]

total_balls = len(bowler_data)
total_runs = bowler_data['total_runs'].sum()
dismissals = bowler_data[bowler_data['dismissal_kind'].notna()]
total_wickets = len(dismissals)

economy = round((total_runs / total_balls) * 6, 2)
strike_rate = round(total_balls / total_wickets,
                    2) if total_wickets > 0 else None
average = round(total_runs / total_wickets, 2) if total_wickets > 0 else None

st.subheader(f"Performance Summary for {bowler_name}")
st.markdown(f"- **Total Wickets:** {total_wickets}")
st.markdown(f"- **Economy Rate:** {economy}")
st.markdown(f"- **Strike Rate:** {strike_rate}")
st.markdown(f"- **Average (runs:wickets):** {average}")


# Venue Analysis carrousel

# Strongest Venue for Each Team
venue_mapping = {
    "M Chinnaswamy Stadium, Bangalore": "M Chinnaswamy Stadium",
    "M Chinnaswamy Stadium, Bengaluru": "M Chinnaswamy Stadium",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium",
    "MA Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium",
    "Rajiv Gandhi International Stadium, Uppal": "Rajiv Gandhi International Stadium",
    "Arun Jaitley Stadium, Delhi": "Arun Jaitley Stadium",
    "Punjab Cricket Association Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Rajiv Gandhi International Stadium, Uppal": "Rajiv Gandhi International Stadium",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium",
    "Eden Gardens, Kolkata": "Eden Gardens",
    "Brabourne Stadium, Mumbai": "Brabourne Stadium",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "Dr Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "ACA-VDCA Stadium, Visakhapatnam": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "ACA-VDCA Cricket Stadium": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "Wankhede Stadium, Mumbai": "Wankhede Stadium",
    "Dr DY Patil Sports Academy, Mumbai": "Dr DY Patil Sports Academy",
    "Maharashtra Cricket Association Stadium, Pune": "Maharashtra Cricket Association Stadium",
    "Maharashtra Cricket Association Stadium, Gahunje": "Maharashtra Cricket Association Stadium",
    "Sawai Mansingh Stadium, Jaipur": "Sawai Mansingh Stadium",
    "Sawai Mansingh Stadium": "Sawai Mansingh Stadium",
    "Punjab Cricket Association Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Punjab Cricket Association IS Bindra Stadium": "Punjab Cricket Association Stadium",
    "IS Bindra Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Punjab Cricket Association Stadium": "Punjab Cricket Association Stadium",
    "Himachal Pradesh Cricket Association Stadium, Dharamsala": "Himachal Pradesh Cricket Association Stadium",
    "Himachal Pradesh Stadium": "Himachal Pradesh Cricket Association Stadium",
    "HPCA Stadium, Dharamshala": "Himachal Pradesh Cricket Association Stadium"



    # Add more mappings as you notice them
}


# Replace based on mapping
matches["venue"] = matches["venue"].replace(venue_mapping)


# Matches at each venue
venue_counts = matches["venue"].value_counts().reset_index()
fig_venue = px.bar(venue_counts.head(10), x="count", y="venue",
                   orientation="h", title="Top 10 IPL Venues by Matches")

venue_wins = matches.groupby(
    ['winner', 'venue']).size().reset_index(name='wins')

strongest_venues = venue_wins.sort_values(
    'wins', ascending=False).drop_duplicates('winner')

fig_strongest = px.bar(
    strongest_venues,
    x="winner",
    y="wins",
    color="venue",
    title="Strongest Venue for Each Team (Based on Most Wins)",
    labels={"winner": "team", "wins": "Wins"},
)

# venue wise advantage to bat or field first analysis

matches["toss_win_and_match_win"] = matches["toss_winner"] == matches["winner"]
venue_strategy = matches[matches["toss_win_and_match_win"]].groupby(
    ["venue", "toss_decision"]
).size().reset_index(name="wins")

fig_strategy = px.bar(
    venue_strategy,
    x="venue",
    y="wins",
    color="toss_decision",
    title="Is it More Advantageous to Bat or Field First at Each Venue?",
    labels={"wins": "Matches Won", "toss_decision": "Decision After Toss"},
)

fig_strategy.update_layout(xaxis_tickangle=-45)

tab1, tab2, tab3 = st.tabs(
    ["Number of matches at each venue", "Strongest team at each venue", "Advantage to bat or field first at a given venue"])

with tab1:
    st.plotly_chart(fig_venue, use_container_width=True)

with tab2:
    st.plotly_chart(fig_strongest, use_container_width=True)

with tab3:
    st.plotly_chart(fig_strategy, use_container_width=True)
