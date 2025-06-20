import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data function with caching
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)
        
        # Convert relevant columns to numeric
        numeric_cols = ['Matches_Played', 'Runs_Scored', 'Batting_Average', 
                       'Batting_Strike_Rate', 'Centuries', 'Half_Centuries',
                       'Wickets_Taken', 'Bowling_Average', 'Economy_Rate']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert 'Year' column to numeric
        if 'Year' in df.columns:
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            # Optionally drop rows with NaN in 'Year'
            df = df.dropna(subset=['Year'])
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return None

# App title and description
st.title("🏏 Advanced Cricket Analytics Dashboard")
st.markdown("""
Explore comprehensive performance metrics with interactive visualizations.
Select players and metrics to generate customized comparisons.
""")

# File uploader for CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Load the data with error handling
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success("✅ Data loaded successfully!")
        
        # Sidebar filters
        st.sidebar.header("🔍 Filter Options")
        
        # Year selection with range slider
        if 'Year' in df.columns:
            min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
            selected_years = st.sidebar.slider(
                "Select Year Range",
                min_year, max_year,
                (min_year, max_year)
            )
        else:
            st.sidebar.warning("No 'Year' column found in dataset")
            selected_years = (None, None)
        
        # Player selection with search
        all_players = sorted(df['Player_Name'].unique()) if 'Player_Name' in df.columns else []
        selected_players = st.sidebar.multiselect(
            "Select Players (max 6)",
            options=all_players,
            default=all_players[:2] if len(all_players) >= 2 else [],
            max_selections=6
        )
        
        # Apply filters
        if 'Year' in df.columns:
            filtered_df = df[
                (df['Year'].between(*selected_years)) & 
                (df['Player_Name'].isin(selected_players))
            ]
        else:
            filtered_df = df[df['Player_Name'].isin(selected_players)]
        
        # Page selection with icons
        page = st.radio("Navigate to:", 
                       ["📊 Data Explorer", "📈 Performance Analysis", "🔍 Advanced Comparisons"],
                       horizontal=True,
                       label_visibility="hidden")
        
        # Data Explorer Tab
        if page == "📊 Data Explorer":
            st.subheader("Dataset Overview")
            
            with st.expander("📋 Raw Data Preview"):
                st.dataframe(filtered_df, height=400)
                
                # Download button
                st.download_button(
                    label="💾 Download Current Data",
                    data=filtered_df.to_csv(index=False).encode('utf-8'),
                    file_name='filtered_cricket_stats.csv',
                    mime='text/csv'
                )
            
            with st.expander("📈 Dataset Statistics"):
                st.write("Summary Statistics:")
                st.dataframe(filtered_df.describe())
                
                st.write("Missing Values:")
                missing_data = filtered_df.isnull().sum().reset_index()
                missing_data.columns = ['Column', 'Missing Values']
                st.dataframe(missing_data)
        
        # Performance Analysis Tab
        elif page == "📈 Performance Analysis":
            st.subheader("Interactive Visualizations")
            
            if not selected_players:
                st.warning("Please select at least one player")
            else:
                # Available metrics for visualization
                available_metrics = [col for col in filtered_df.columns 
                                   if filtered_df[col].dtype in ['int64', 'float64']]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    primary_metric = st.selectbox(
                        "Primary Metric",
                        options=available_metrics,
                        index=available_metrics.index('Runs_Scored') if 'Runs_Scored' in available_metrics else 0
                    )
                
                with col2:
                    secondary_metric = st.selectbox(
                        "Secondary Metric (for combo charts)",
                        options=['None'] + available_metrics,
                        index=0
                    )
                
                # Visualization type selection
                viz_type = st.selectbox(
                    "Visualization Type",
                    options=[
                        "Bar Chart", "Line Chart", "Scatter Plot", 
                        "Radar Chart", "Box Plot", "Violin Plot",
                        "Combo Chart", "Heatmap", "Parallel Coordinates"
                    ]
                )
                
                # Generate visualizations based on selection
                if viz_type == "Bar Chart":
                    fig = px.bar(
                        filtered_df,
                        x="Player_Name",
                        y=primary_metric,
                        color="Player_Name",
                        animation_frame="Year" if 'Year' in filtered_df.columns else None,
                        title=f"{primary_metric} Comparison"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "Line Chart":
                    fig = px.line(
                        filtered_df,
                        x="Year" if 'Year' in filtered_df.columns else "Player_Name",
                        y=primary_metric,
                        color="Player_Name",
                        markers=True,
                        title=f"{primary_metric} Trend Over Time"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "Scatter Plot":
                    if secondary_metric != 'None':
                        fig = px.scatter(
                            filtered_df,
                            x=primary_metric,
                            y=secondary_metric,
                            color="Player_Name",
                            size="Matches_Played" if 'Matches_Played' in filtered_df.columns else None,
                            hover_name="Year" if 'Year' in filtered_df.columns else "Player_Name",
                            title=f"{primary_metric} vs {secondary_metric}"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Please select a secondary metric for scatter plot")
                
                elif viz_type == "Radar Chart":
                    if len(selected_players) > 0:
                        metrics_for_radar = st.multiselect(
                            "Select metrics for radar chart",
                            options=available_metrics,
                            default=available_metrics[:5] if len(available_metrics) >=5 else available_metrics
                        )
                        
                        if metrics_for_radar:
                            radar_df = filtered_df.groupby('Player_Name')[metrics_for_radar].mean().reset_index()
                            
                            fig = go.Figure()
                            
                            for player in selected_players:
                                player_data = radar_df[radar_df['Player_Name'] == player]
                                fig.add_trace(go.Scatterpolar(
                                    r=player_data[metrics_for_radar].values[0],
                                    theta=metrics_for_radar,
                                    fill='toself',
                                    name=player
                                ))
                            
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True)),
                                showlegend=True,
                                title="Player Comparison Radar Chart"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type in ["Box Plot", "Violin Plot"]:
                    if viz_type == "Box Plot":
                        fig = px.box(
                            filtered_df,
                            x="Player_Name",
                            y=primary_metric,
                            color="Player_Name",
                            title=f"Distribution of {primary_metric}"
                        )
                    else:
                        fig = px.violin(
                            filtered_df,
                            x="Player_Name",
                            y=primary_metric,
                            color="Player_Name",
                            box=True,
                            title=f"Distribution of {primary_metric}"
                        )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "Combo Chart":
                    if secondary_metric != 'None':
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # Add primary metric (bar)
                        fig.add_trace(
                            go.Bar(
                                x=filtered_df['Player_Name'],
                                y=filtered_df[primary_metric],
                                name=primary_metric
                            ),
                            secondary_y=False
                        )
                        
                        # Add secondary metric (line)
                        fig.add_trace(
                            go.Scatter(
                                x=filtered_df['Player_Name'],
                                y=filtered_df[secondary_metric],
                                name=secondary_metric,
                                mode='lines+markers'
                            ),
                            secondary_y=True
                        )
                        
                        fig.update_layout(
                            title_text=f"{primary_metric} vs {secondary_metric}",
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Please select a secondary metric for combo chart")
                
                elif viz_type == "Heatmap":
                    if len(selected_players) > 1:
                        metrics_for_heatmap = st.multiselect(
                            "Select metrics for heatmap",
                            options=available_metrics,
                            default=available_metrics[:5] if len(available_metrics) >=5 else available_metrics
                        )
                        
                        if metrics_for_heatmap:
                            heatmap_df = filtered_df.groupby('Player_Name')[metrics_for_heatmap].mean()
                            
                            fig = px.imshow(
                                heatmap_df,
                                labels=dict(x="Metric", y="Player", color="Value"),
                                x=metrics_for_heatmap,
                                y=heatmap_df.index,
                                aspect="auto",
                                title="Player Performance Heatmap"
                            )
                            fig.update_xaxes(side="top")
                            st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "Parallel Coordinates":
                    if len(selected_players) > 1:
                        metrics_for_parallel = st.multiselect(
                            "Select metrics for parallel coordinates",
                            options=available_metrics,
                            default=available_metrics[:5] if len(available_metrics) >=5 else available_metrics
                        )
                        
                        if metrics_for_parallel:
                            fig = px.parallel_coordinates(
                                filtered_df,
                                color="Player_Name",
                                dimensions=metrics_for_parallel,
                                title="Parallel Coordinates Analysis"
                            )
                            st.plotly_chart(fig, use_container_width=True)
        
        # Advanced Comparisons Tab
        elif page == "🔍 Advanced Comparisons":
            st.subheader("Comprehensive Player Comparison")
            
            if len(selected_players) < 2:
                st.warning("Please select at least 2 players for comparison")
            else:
                # Available metrics for comparison
                available_metrics = [col for col in filtered_df.columns 
                                   if filtered_df[col].dtype in ['int64', 'float64']]
                
                if not available_metrics:
                    st.error("No numeric metrics found for comparison")
                else:
                    with st.expander("⚙️ Comparison Settings"):
                        comparison_metrics = st.multiselect(
                            "Select metrics to compare",
                            options=available_metrics,
                            default=available_metrics[:3] if len(available_metrics) >=3 else available_metrics
                        )
                        
                        comparison_method = st.radio(
                            "Comparison method",
                            options=["Mean", "Sum", "Max", "Min"],
                            horizontal=True
                        )
                    
                    if comparison_metrics:
                        try:
                            # Calculate comparison based on selected method
                            if comparison_method == "Mean":
                                comparison_df = filtered_df.groupby('Player_Name')[comparison_metrics].mean().reset_index()
                            elif comparison_method == "Sum":
                                comparison_df = filtered_df.groupby('Player_Name')[comparison_metrics].sum().reset_index()
                            elif comparison_method == "Max":
                                comparison_df = filtered_df.groupby('Player_Name')[comparison_metrics].max().reset_index()
                            else:
                                comparison_df = filtered_df.groupby('Player_Name')[comparison_metrics].min().reset_index()
                            
                            # Display comparison results
                            st.subheader("📊 Comparison Results")
                            
                            tab1, tab2, tab3 = st.tabs(["Table View", "Visual Comparison", "Radar View"])
                            
                            with tab1:
                                st.dataframe(
                                    comparison_df.style
                                    .background_gradient(cmap='Blues')
                                    .format("{:.2f}", subset=comparison_metrics),
                                    height=400,
                                    use_container_width=True
                                )
                            
                            with tab2:
                                viz_type = st.selectbox(
                                    "Visualization Type",
                                    options=["Bar Chart", "Line Chart", "Scatter Matrix"],
                                    key="comparison_viz"
                                )
                                
                                if viz_type == "Bar Chart":
                                    fig = px.bar(
                                        comparison_df.melt(id_vars='Player_Name'),
                                        x='Player_Name',
                                        y='value',
                                        color='variable',
                                        barmode='group',
                                        title="Metric Comparison"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif viz_type == "Line Chart":
                                    fig = px.line(
                                        comparison_df.melt(id_vars='Player_Name'),
                                        x='variable',
                                        y='value',
                                        color='Player_Name',
                                        markers=True,
                                        title="Metric Trends by Player"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif viz_type == "Scatter Matrix":
                                    fig = px.scatter_matrix(
                                        comparison_df,
                                        dimensions=comparison_metrics,
                                        color="Player_Name",
                                        title="Scatter Matrix of Player Metrics"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            with tab3:
                                fig = go.Figure()
                                
                                for player in selected_players:
                                    player_data = comparison_df[comparison_df['Player_Name'] == player]
                                    fig.add_trace(go.Scatterpolar(
                                        r=player_data[comparison_metrics].values[0],
                                        theta=comparison_metrics,
                                        fill='toself',
                                        name=player
                                    ))
                                
                                fig.update_layout(
                                    polar=dict(radialaxis=dict(visible=True)),
                                    showlegend=True,
                                    title="Player Comparison Radar Chart"
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                        
                        except Exception as e:
                            st.error(f"Error generating comparison: {str(e)}")
                            st.write("Debug Info - Filtered Data:")
                            st.write(filtered_df[['Player_Name'] + comparison_metrics].head())


#  run the app    python -m streamlit run cricket_analytics_app.py