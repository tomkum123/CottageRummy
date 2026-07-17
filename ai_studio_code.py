import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

# Set page to wide mode
st.set_page_config(page_title="Cottage Rummy Stats", layout="wide")

# YOUR DIRECT GITHUB LINK
GITHUB_URL = "https://github.com/tomkum123/CottageRummy/raw/main/docs/Cottage%20Rummy%20Data%20File.xlsx"

@st.cache_data(ttl=600)
def load_data():
    try:
        # Download from GitHub
        response = requests.get(GITHUB_URL)
        response.raise_for_status()
        
        # Read Excel
        df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        
        players = ['Christine', 'Michael', 'Alaura', 'Matthew', 'Kirby', 'Annmarie', 'Tom']
        
        # Basic Cleaning
        df = df[['Date'] + players].dropna(how='all')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Year'] = df['Date'].dt.year
        
        # Calculate Player Count
        df['Player_Count'] = df[players].notna().sum(axis=1)
        df = df[df['Player_Count'] > 1].copy()
        
        # Rank players (Low score = Rank 1)
        ranks = df[players].rank(axis=1, method='min', ascending=True)
        return df, players, ranks
    except Exception as e:
        st.error(f"Error loading from GitHub: {e}")
        return None, None, None

df, players, ranks = load_data()

if df is not None:
    # --- HEADER SECTION ---
    st.title("🃏 Cottage Rummy Analytics")
    
    # Calculate Last Entry Date
    last_entry_date = df['Date'].max().strftime('%B %d, %Y')
    st.markdown(f"📅 **Last Data Entry:** {last_entry_date}")
    
    # --- TOP FILTERS (No Sidebar) ---
    counts = sorted(df['Player_Count'].unique().astype(int))
    
    # Keep the selector from being too wide
    col_f, col_e = st.columns([1, 3])
    with col_f:
        p_count = st.selectbox("Select Number of Players:", options=counts, index=len(counts)-1)

    f_df = df[df['Player_Count'] == p_count].sort_values('Date')
    f_ranks = ranks.loc[f_df.index]

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🏆 Placements", "🚀 Advanced Analytics", "📋 Raw Data"])

    # --- TAB 1: SUMMARY ---
    with tab1:
        st.info("**Note:** Total Wins tracks 1st place finishes. Average Score tracks overall skill.")
        averages = f_df[players].mean().dropna().sort_values()
        wins = (f_ranks == 1).sum().reindex(players).fillna(0)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_avg = px.bar(averages, title="Average Score (Lower is Better)", color=averages.values, 
                             color_continuous_scale="RdYlGn_r", text_auto='.1f')
            fig_avg.update_traces(textposition='inside')
            # Option 2: Disable zooming/magnifying
            fig_avg.update_layout(xaxis_fixedrange=True, yaxis_fixedrange=True)
            st.plotly_chart(fig_avg, use_container_width=True, config={'displayModeBar': False})

        with c2:
            fig_wins = px.bar(x=wins.index, y=wins.values, title="Total Wins (1st Places)", 
                              color=wins.values, color_continuous_scale="Greens", text_auto=True)
            fig_wins.update_traces(textposition='inside')
            # Option 2: Disable zooming/magnifying
            fig_wins.update_layout(xaxis_fixedrange=True, yaxis_fixedrange=True)
            st.plotly_chart(fig_wins, use_container_width=True, config={'displayModeBar': False})

        st.write("---")
        st.subheader("📖 Dashboard Legend & Definitions")
        l1, l2, l3 = st.columns(3)
        with l1:
            st.markdown("**Total Wins (1st Place Finish)**")
            st.caption("This counts the individual games where a player achieved the absolute lowest score at the table, earning them a 1st place victory.")
        with l2:
            st.markdown("**Average Score**")
            st.caption("The sum of all points a player earned divided by games played. A lower number represents a more skilled player.")
        with l3:
            st.markdown("**Color Coding**")
            st.caption("Green = Top performance. Red = High-point finishes (unfavorable).")

    # --- TAB 2: PLACEMENT ANALYSIS (Card Style) ---
    with tab2:
        st.subheader(f"Placement Breakdown ({p_count} Player Games)")
        cols = st.columns(3)
        for i, p in enumerate(players):
            with cols[i % 3]:
                p_ranks = f_ranks[p].dropna()
                if not p_ranks.empty:
                    win_rate = (p_ranks == 1).sum() / len(p_ranks) * 100
                    avg_p = p_ranks.mean()
                    counts = p_ranks.value_counts().sort_index()
                    counts.index = [f"{int(x)}st" if x==1 else f"{int(x)}nd" if x==2 else f"{int(x)}rd" if x==3 else f"{int(x)}th" for x in counts.index]
                    
                    st.markdown(f"""<div style="line-height:1.2;"><b style="font-size: 16px;">{p}</b><br>
                        <span style="background-color:#4A90E2; color:white; padding:2px 6px; border-radius:8px; font-size:10px;">{win_rate:.1f}% Win Rate</span>
                        <span style="background-color:#4A90E2; color:white; padding:2px 6px; border-radius:8px; font-size:10px;">{avg_p:.2f} Avg Placement</span></div>""", unsafe_allow_html=True)
                    
                    fig = px.bar(x=counts.index, y=counts.values, height=200, text_auto=True)
                    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="", yaxis_title="", 
                                      font=dict(size=10), xaxis_fixedrange=True, yaxis_fixedrange=True)
                    fig.update_traces(marker_color='#8EBAE3', textposition='inside')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    st.write("---")

    # --- TAB 3: ADVANCED ANALYTICS ---
    with tab3:
        st.header("🚀 Advanced Insights")
        r1_1, r1_2 = st.columns(2)
        with r1_1:
            clobber = f_df[players].max().dropna().sort_values(ascending=False)
            fig_clobber = px.bar(clobber, title="Hall of Shame: Highest Single Game Score", color=clobber.values, 
                                 color_continuous_scale="Reds", text_auto=True)
            fig_clobber.update_layout(xaxis_fixedrange=True, yaxis_fixedrange=True)
            fig_clobber.update_traces(textposition='inside')
            st.plotly_chart(fig_clobber, use_container_width=True, config={'displayModeBar': False})
        with r1_2:
            stdev = f_df[players].std().dropna().sort_values()
            fig_stdev = px.bar(stdev, title="Stability Rating (Lower = More Consistent)", color=stdev.values, 
                               color_con