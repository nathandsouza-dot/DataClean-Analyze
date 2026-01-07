import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="FIFA Stats Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {background-color: #0e1117;}
    .stMetric {background-color: #1e2130; padding: 15px; border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect('fifa_stats.db', check_same_thread=False)

@st.cache_data(ttl=600)
def load_data(query):
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    return df

# Header
st.title("⚽ FIFA Player Statistics Dashboard")
st.markdown("**Comprehensive analysis of FIFA player data**")
st.markdown("---")

# Sidebar
st.sidebar.header("🎮 Filters & Settings")
st.sidebar.markdown("---")

# Load basic data for filters
positions_df = load_data("SELECT DISTINCT Position FROM players WHERE Position != '' ORDER BY Position")
clubs_df = load_data("SELECT DISTINCT Club FROM players WHERE Club != '' ORDER BY Club")

selected_position = st.sidebar.selectbox(
    "🎯 Position",
    ["All"] + positions_df['Position'].tolist()
)

selected_club = st.sidebar.selectbox(
    "🏆 Club", 
    ["All"] + clubs_df['Club'].head(50).tolist()
)

min_rating, max_rating = st.sidebar.slider(
    "⭐ Overall Rating Range",
    0, 100, (60, 100)
)

min_age, max_age = st.sidebar.slider(
    "👤 Age Range",
    16, 45, (18, 35)
)

# Build filter query
filter_clause = f"WHERE Overall BETWEEN {min_rating} AND {max_rating} AND Age BETWEEN {min_age} AND {max_age}"
if selected_position != "All":
    filter_clause += f" AND Position = '{selected_position}'"
if selected_club != "All":
    filter_clause += f" AND Club = '{selected_club}'"

# KPI Metrics
col1, col2, col3, col4, col5 = st.columns(5)

try:
    with col1:
        total = load_data(f"SELECT COUNT(*) as count FROM players {filter_clause}")
        total_count = total['count'].iloc[0] if not total.empty else 0
        st.metric("👥 Total Players", f"{total_count:,}")

    with col2:
        avg_rating = load_data(f"SELECT ROUND(AVG(Overall), 1) as avg FROM players {filter_clause}")
        avg_val = avg_rating['avg'].iloc[0] if not avg_rating.empty and pd.notna(avg_rating['avg'].iloc[0]) else 0
        st.metric("⭐ Avg Rating", f"{avg_val}")

    with col3:
        avg_age = load_data(f"SELECT ROUND(AVG(Age), 1) as avg FROM players {filter_clause}")
        age_val = avg_age['avg'].iloc[0] if not avg_age.empty and pd.notna(avg_age['avg'].iloc[0]) else 0
        st.metric("👤 Avg Age", f"{age_val}")

    with col4:
        top_player = load_data(f"SELECT Name, Overall FROM players {filter_clause} ORDER BY Overall DESC LIMIT 1")
        if not top_player.empty:
            st.metric("🏆 Top Player", top_player['Name'].iloc[0], f"{top_player['Overall'].iloc[0]}")
        else:
            st.metric("🏆 Top Player", "N/A", "0")

    with col5:
        clubs = load_data(f"SELECT COUNT(DISTINCT Club) as count FROM players {filter_clause}")
        clubs_count = clubs['count'].iloc[0] if not clubs.empty else 0
        st.metric("🏟️ Clubs", f"{clubs_count}")
except Exception as e:
    st.error(f"Error loading metrics: {e}")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏆 Top Players", "⚽ Best XI", "🏟️ Club Analysis"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Rating Distribution")
        rating_dist = load_data(f"""
            SELECT Overall, COUNT(*) as count 
            FROM players {filter_clause}
            GROUP BY Overall 
            ORDER BY Overall
        """)
        fig = px.area(rating_dist, x='Overall', y='count',
                     title='Player Rating Distribution',
                     labels={'count': 'Number of Players'},
                     color_discrete_sequence=['#00ff41'])
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🌍 Top 15 Nationalities")
        nations = load_data(f"""
            SELECT Nationality, COUNT(*) as count, ROUND(AVG(Overall), 1) as avg_rating
            FROM players {filter_clause}
            GROUP BY Nationality 
            ORDER BY count DESC 
            LIMIT 15
        """)
        fig = px.bar(nations, x='Nationality', y='count',
                    title='Players by Nationality',
                    color='avg_rating',
                    color_continuous_scale='Turbo',
                    labels={'count': 'Player Count', 'avg_rating': 'Avg Rating'})
        fig.update_layout(template='plotly_dark', xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Age Distribution")
        age_dist = load_data(f"""
            SELECT Age, COUNT(*) as count 
            FROM players {filter_clause}
            GROUP BY Age 
            ORDER BY Age
        """)
        fig = px.line(age_dist, x='Age', y='count',
                     title='Players by Age',
                     markers=True,
                     color_discrete_sequence=['#ff6b6b'])
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏟️ Top 15 Clubs")
        clubs = load_data(f"""
            SELECT Club, COUNT(*) as count, ROUND(AVG(Overall), 1) as avg_rating
            FROM players {filter_clause} AND Club != 'Hoffenheim' AND Club != ''
            GROUP BY Club 
            ORDER BY count DESC 
            LIMIT 15
        """)
        fig = px.bar(clubs, x='Club', y='count',
                    title='Players by Club',
                    color='avg_rating',
                    color_continuous_scale='Reds',
                    labels={'count': 'Player Count', 'avg_rating': 'Avg Rating'})
        fig.update_layout(template='plotly_dark', xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🏆 Top 50 Players")
    
    top_players = load_data(f"""
        SELECT Name, Age, Nationality, Overall, Potential, Club, Position, 
               PreferredFoot, WeakFoot, SkillMoves
        FROM players {filter_clause}
        ORDER BY Overall DESC 
        LIMIT 50
    """)
    
    st.dataframe(
        top_players,
        use_container_width=True,
        height=600
    )

with tab3:
    st.subheader("⚽ BEST XI - Dream Team")
    st.markdown("### 🏆 Formation: 4-3-3")
    
    try:
        # Get best players by position
        gk = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position = 'GK' ORDER BY Overall DESC LIMIT 1")
        lb = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('LB', 'LWB') ORDER BY Overall DESC LIMIT 1")
        cb1 = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position = 'CB' ORDER BY Overall DESC LIMIT 1")
        cb2 = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position = 'CB' ORDER BY Overall DESC LIMIT 1 OFFSET 1")
        rb = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('RB', 'RWB') ORDER BY Overall DESC LIMIT 1")
        cm1 = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('CM', 'CDM') ORDER BY Overall DESC LIMIT 1")
        cm2 = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('CM', 'CAM') ORDER BY Overall DESC LIMIT 1")
        cm3 = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('CM', 'CDM', 'CAM') ORDER BY Overall DESC LIMIT 1 OFFSET 1")
        lw = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('LW', 'LM') ORDER BY Overall DESC LIMIT 1")
        striker = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('ST', 'CF') ORDER BY Overall DESC LIMIT 1")
        rw = load_data("SELECT Name, Overall, Club, Age FROM players WHERE Position IN ('RW', 'RM') ORDER BY Overall DESC LIMIT 1")
        
        # Forward line
        st.markdown("#### ⚔️ Attack")
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            if not lw.empty:
                st.info(f"**LW**: {lw['Name'].iloc[0]}\n\n⭐ {lw['Overall'].iloc[0]} | {lw['Club'].iloc[0]}")
        with fcol2:
            if not striker.empty:
                st.success(f"**ST**: {striker['Name'].iloc[0]}\n\n⭐ {striker['Overall'].iloc[0]} | {striker['Club'].iloc[0]}")
        with fcol3:
            if not rw.empty:
                st.info(f"**RW**: {rw['Name'].iloc[0]}\n\n⭐ {rw['Overall'].iloc[0]} | {rw['Club'].iloc[0]}")
        
        # Midfield line
        st.markdown("#### 🎯 Midfield")
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            if not cm1.empty:
                st.warning(f"**CM**: {cm1['Name'].iloc[0]}\n\n⭐ {cm1['Overall'].iloc[0]} | {cm1['Club'].iloc[0]}")
        with mcol2:
            if not cm2.empty:
                st.warning(f"**CM**: {cm2['Name'].iloc[0]}\n\n⭐ {cm2['Overall'].iloc[0]} | {cm2['Club'].iloc[0]}")
        with mcol3:
            if not cm3.empty:
                st.warning(f"**CM**: {cm3['Name'].iloc[0]}\n\n⭐ {cm3['Overall'].iloc[0]} | {cm3['Club'].iloc[0]}")
        
        # Defense line
        st.markdown("#### 🛡️ Defense")
        dcol1, dcol2, dcol3, dcol4 = st.columns(4)
        with dcol1:
            if not lb.empty:
                st.error(f"**LB**: {lb['Name'].iloc[0]}\n\n⭐ {lb['Overall'].iloc[0]} | {lb['Club'].iloc[0]}")
        with dcol2:
            if not cb1.empty:
                st.error(f"**CB**: {cb1['Name'].iloc[0]}\n\n⭐ {cb1['Overall'].iloc[0]} | {cb1['Club'].iloc[0]}")
        with dcol3:
            if not cb2.empty:
                st.error(f"**CB**: {cb2['Name'].iloc[0]}\n\n⭐ {cb2['Overall'].iloc[0]} | {cb2['Club'].iloc[0]}")
        with dcol4:
            if not rb.empty:
                st.error(f"**RB**: {rb['Name'].iloc[0]}\n\n⭐ {rb['Overall'].iloc[0]} | {rb['Club'].iloc[0]}")
        
        # Goalkeeper
        st.markdown("#### 🧤 Goalkeeper")
        if not gk.empty:
            st.success(f"**GK**: {gk['Name'].iloc[0]}\n\n⭐ {gk['Overall'].iloc[0]} | {gk['Club'].iloc[0]}")
        
        # Team statistics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            all_players = pd.concat([gk, lb, cb1, cb2, rb, cm1, cm2, cm3, lw, striker, rw])
            avg_overall = all_players['Overall'].mean() if not all_players.empty else 0
            st.metric("Team Average Rating", f"{avg_overall:.1f}")
        
        with col2:
            avg_age = all_players['Age'].mean() if not all_players.empty else 0
            st.metric("Team Average Age", f"{avg_age:.1f}")
        
        with col3:
            unique_clubs = all_players['Club'].nunique() if not all_players.empty else 0
            st.metric("Clubs Represented", unique_clubs)
    
    except Exception as e:
        st.error(f"Error loading Best XI: {e}")

with tab4:
    st.subheader("🏟️ Club Analysis & Talent Index")
    
    try:
        # Club talent analysis
        club_talent = load_data("""
            SELECT 
                Club,
                COUNT(*) as TotalPlayers,
                ROUND(AVG(Overall), 2) as AvgRating,
                MAX(Overall) as BestPlayer,
                ROUND(AVG(Potential), 2) as AvgPotential,
                COUNT(CASE WHEN Age <= 23 THEN 1 END) as YoungTalents,
                COUNT(CASE WHEN Overall >= 80 THEN 1 END) as WorldClass,
                ROUND(AVG(CASE WHEN Age <= 23 THEN Potential ELSE 0 END), 2) as YouthPotential
            FROM players
            WHERE Club != '' AND Club IS NOT NULL AND Club != 'Hoffenheim'
            GROUP BY Club
            HAVING TotalPlayers >= 15
            ORDER BY AvgRating DESC
            LIMIT 30
        """)
        
        if not club_talent.empty:
            # Calculate Talent Index (weighted score)
            club_talent['TalentIndex'] = (
                club_talent['AvgRating'] * 0.4 + 
                club_talent['AvgPotential'] * 0.3 + 
                club_talent['YoungTalents'] * 2 + 
                club_talent['WorldClass'] * 1.5
            ).round(2)
            club_talent = club_talent.sort_values('TalentIndex', ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 🏆 Top 20 Clubs by Talent Index")
                fig = px.bar(club_talent.head(20), 
                             x='Club', y='TalentIndex',
                             color='AvgRating',
                             title='Club Talent Index (Quality + Potential + Youth)',
                             labels={'TalentIndex': 'Talent Index Score'},
                             color_continuous_scale='Plasma',
                             hover_data=['TotalPlayers', 'WorldClass', 'YoungTalents'])
                fig.update_layout(template='plotly_dark', xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📊 Talent Metrics")
                top_club = club_talent.head(10)
                st.dataframe(
                    top_club[['Club', 'TalentIndex', 'AvgRating', 'WorldClass', 'YoungTalents']],
                    use_container_width=True,
                    height=500
                )
        else:
            st.warning("No club data available with minimum 15 players.")
        
        st.markdown("---")
        
        # Youth vs Experience analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌟 Best Youth Academies (U23 Talent)")
            youth_clubs = load_data("""
                SELECT 
                    Club,
                    COUNT(*) as YoungPlayers,
                    ROUND(AVG(Overall), 1) as AvgRating,
                    ROUND(AVG(Potential), 1) as AvgPotential,
                    MAX(Potential) as BestPotential
                FROM players
                WHERE Age <= 23 AND Club != '' AND Club != 'Hoffenheim'
                GROUP BY Club
                HAVING YoungPlayers >= 5
                ORDER BY AvgPotential DESC
                LIMIT 15
            """)
            
            if not youth_clubs.empty:
                fig = px.scatter(youth_clubs, 
                                x='AvgRating', y='AvgPotential',
                                size='YoungPlayers', 
                                color='Club',
                                hover_data=['BestPotential'],
                                title='Youth Development: Current vs Potential')
                fig.update_layout(template='plotly_dark', height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No youth academy data available.")
        
        with col2:
            st.markdown("### 💎 Hidden Gems (High Potential, Low Current)")
            gems = load_data("""
                SELECT Name, Age, Club, Overall, Potential, (Potential - Overall) as Growth
                FROM players
                WHERE (Potential - Overall) >= 15 AND Age <= 24
                ORDER BY Growth DESC
                LIMIT 20
            """)
            if not gems.empty:
                st.dataframe(gems, use_container_width=True, height=400)
            else:
                st.info("No hidden gems found with current criteria.")
        
        st.markdown("---")
        
        # Squad depth analysis
        if not club_talent.empty:
            st.markdown("### 📊 Squad Depth Comparison (Top 5 Clubs)")
            depth_clubs = club_talent.head(5)['Club'].tolist()
            
            if depth_clubs:
                depth_data = load_data(f"""
                    SELECT 
                        Club,
                        Position,
                        COUNT(*) as Players,
                        ROUND(AVG(Overall), 1) as AvgRating
                    FROM players
                    WHERE Club IN ('{"','".join(depth_clubs)}')
                    GROUP BY Club, Position
                """)
                
                if not depth_data.empty:
                    fig = px.bar(depth_data, 
                                x='Position', y='Players',
                                color='Club', 
                                barmode='group',
                                title='Position Coverage by Top Clubs')
                    fig.update_layout(template='plotly_dark', xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error in club analysis: {e}")


    st.subheader("📈 Skill Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**⚔️ Attack vs Defense Skills**")
        skills = load_data(f"""
            SELECT 
                Name,
                Position,
                Overall,
                ROUND((Finishing + ShotPower + LongShots + Volleys + Penalties) / 5.0, 1) as AttackSkill,
                ROUND((Marking + StandingTackle + SlidingTackle + Interceptions) / 4.0, 1) as DefenseSkill
            FROM players 
            {filter_clause} AND Position != 'GK'
            ORDER BY Overall DESC
            LIMIT 100
        """)
        
        fig = px.scatter(skills, x='AttackSkill', y='DefenseSkill',
                        size='Overall', color='Position',
                        hover_data=['Name', 'Overall'],
                        title='Attack vs Defense Skills (Top 100)',
                        labels={'AttackSkill': 'Attack Skill', 'DefenseSkill': 'Defense Skill'})
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**🏃 Physical Attributes**")
        physical = load_data(f"""
            SELECT 
                Name,
                Position,
                Overall,
                ROUND((Acceleration + SprintSpeed + Agility) / 3.0, 1) as Speed,
                ROUND((Strength + Jumping + Stamina) / 3.0, 1) as Power
            FROM players 
            {filter_clause}
            ORDER BY Overall DESC
            LIMIT 100
        """)
        
        fig = px.scatter(physical, x='Speed', y='Power',
                        size='Overall', color='Position',
                        hover_data=['Name', 'Overall'],
                        title='Speed vs Power (Top 100)',
                        labels={'Speed': 'Speed', 'Power': 'Power'})
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("**🎯 Position Comparison**")
    position_comparison = load_data("""
        SELECT * FROM position_stats ORDER BY AvgRating DESC
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.bar(position_comparison, x='Position', y='PlayerCount',
                    color='AvgRating',
                    title='Position Analysis: Player Count & Average Rating',
                    color_continuous_scale='Viridis',
                    labels={'PlayerCount': 'Number of Players', 'AvgRating': 'Avg Rating'})
        fig.update_layout(template='plotly_dark', xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.dataframe(position_comparison, use_container_width=True, height=400)

with tab4:
    st.subheader("🔍 Player Search")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔎 Search by name, club, or nationality:", "")
    
    with col2:
        search_type = st.radio("Search in:", ["Name", "Club", "Nationality"])
    
    if search_term:
        search_column = search_type
        results = load_data(f"""
            SELECT ID, Name, Age, Nationality, Overall, Potential, Club, Position, 
                   Height, Weight, PreferredFoot, Value, Wage
            FROM players 
            WHERE {search_column} LIKE '%{search_term}%'
            ORDER BY Overall DESC
            LIMIT 100
        """)
        
        if len(results) > 0:
            st.write(f"Found **{len(results)}** results")
            st.dataframe(
                results,
                use_container_width=True,
                height=500
            )
        else:
            st.warning("No players found matching your search criteria.")


    st.subheader("🎯 Position Deep Dive")
    
    selected_pos = st.selectbox("Select Position:", positions_df['Position'].tolist())
    
    pos_players = load_data(f"""
        SELECT Name, Age, Nationality, Overall, Potential, Club,
               Crossing, Finishing, HeadingAccuracy, ShortPassing, Dribbling,
               BallControl, Acceleration, SprintSpeed, Strength, Stamina
        FROM players 
        WHERE Position = '{selected_pos}'
        ORDER BY Overall DESC
        LIMIT 30
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"**Top 10 {selected_pos} Players**")
        top_10 = pos_players[['Name', 'Club', 'Overall']].head(10)
        st.dataframe(top_10, use_container_width=True, height=400)
    
    with col2:
        st.markdown(f"**{selected_pos} Key Attributes**")
        avg_stats = pos_players[['Crossing', 'Finishing', 'HeadingAccuracy', 
                                 'ShortPassing', 'Dribbling', 'BallControl',
                                 'Acceleration', 'SprintSpeed', 'Strength', 'Stamina']].mean()
        
        fig = go.Figure(data=[
            go.Bar(x=avg_stats.index, y=avg_stats.values,
                  marker_color='lightblue')
        ])
        fig.update_layout(
            title=f'Average Stats for {selected_pos}',
            template='plotly_dark',
            xaxis_tickangle=-45,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Data Source:** FIFA EDA Stats Dataset | **Processing:** Shell Utilities + SQLite | **Visualization:** Streamlit + Plotly")
