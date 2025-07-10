import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase database
try:
    db = SupabaseDatabase()
    SUPABASE_AVAILABLE = True
except Exception as e:
    SUPABASE_AVAILABLE = False
    st.error(f"❌ Failed to connect to Supabase: {e}")

def get_client_id():
    """Safely get client_id from session state."""
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        st.stop()
    return client_id

def run_stage4_analysis():
    """Run Stage 4 theme analysis"""
    try:
        from stage4_theme_analyzer import Stage4ThemeAnalyzer
        client_id = get_client_id()
        analyzer = Stage4ThemeAnalyzer()
        result = analyzer.process_themes(client_id=client_id)
        return result
    except Exception as e:
        st.error(f"Stage 4 analysis failed: {e}")
        return {"status": "error", "message": str(e)}

def get_stage4_summary():
    """Get Stage 4 themes summary"""
    try:
        client_id = get_client_id()
        db = SupabaseDatabase()
        return db.get_themes_summary(client_id=client_id)
    except Exception as e:
        st.error(f"Failed to get Stage 4 summary: {e}")
        return {}

def show_stage4_themes():
    """Display Stage 4 themes analysis"""
    st.subheader("🎯 Stage 4: Theme Generation")
    
    # Get summary
    summary = get_stage4_summary()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Themes", summary.get('total_themes', 0))
    
    with col2:
        st.metric("High Strength", summary.get('high_strength', 0))
    
    with col3:
        st.metric("Competitive", summary.get('competitive_themes', 0))
    
    with col4:
        st.metric("Companies", summary.get('companies_covered', 0))
    
    # Run analysis button
    if st.button("🔄 Run Stage 4 Analysis", type="primary"):
        run_stage4_analysis()
    
    # Show current themes status
    themes_summary = get_stage4_summary()
    if themes_summary:
        st.success(f"✅ Generated {themes_summary.get('total_themes', 0)} themes")
        # CTA button to go to Stage 5
        if st.button("📈 Continue to Stage 5: Executive Summary", type="primary"):
            st.session_state.current_step = 5
            st.rerun()
    else:
        st.info("📊 No themes available yet. Run the analysis to generate themes.")
    
    # Display themes table
    st.markdown("---")
    st.subheader("📋 Themes Table")
    
    client_id = get_client_id()
    themes_df = db.get_themes(client_id=client_id)
    
    if not themes_df.empty:
        # Prepare the table for display
        display_df = themes_df.copy()
        
        # Select and rename key columns for display
        display_columns = {
            'theme_statement': 'Theme Statement',
            'theme_strength': 'Strength',
            'competitive_flag': 'Competitive',
            'company_count': 'Companies',
            'finding_count': 'Findings',
            'avg_confidence_score': 'Confidence',
            'created_at': 'Created'
        }
        
        # Filter to only show columns that exist
        available_columns = {k: v for k, v in display_columns.items() if k in display_df.columns}
        
        if available_columns:
            # Select only the columns we want to display
            display_df = display_df[list(available_columns.keys())].copy()
            
            # Rename columns for display
            display_df = display_df.rename(columns=available_columns)
            
            # Format the data for better display
            if 'Competitive' in display_df.columns:
                display_df['Competitive'] = display_df['Competitive'].map({True: 'Yes', False: 'No'})
            
            if 'Created' in display_df.columns:
                display_df['Created'] = pd.to_datetime(display_df['Created']).dt.strftime('%Y-%m-%d %H:%M')
            
            if 'Strength' in display_df.columns:
                # Only round if the column is numeric
                if pd.api.types.is_numeric_dtype(display_df['Strength']):
                    display_df['Strength'] = display_df['Strength'].round(2)
                # If it's not numeric (e.g., string values like "weak", "strong"), leave as is
            
            if 'Confidence' in display_df.columns:
                # Only round if the column is numeric
                if pd.api.types.is_numeric_dtype(display_df['Confidence']):
                    display_df['Confidence'] = display_df['Confidence'].round(2)
                # If it's not numeric, leave as is
            
            # Truncate long theme statements for table display
            if 'Theme Statement' in display_df.columns:
                display_df['Theme Statement'] = display_df['Theme Statement'].apply(
                    lambda x: x[:100] + "..." if len(str(x)) > 100 else x
                )
            
            # Display the table
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Theme Statement": st.column_config.TextColumn(
                        "Theme Statement",
                        width="large",
                        help="The main theme statement"
                    ),
                    "Strength": st.column_config.NumberColumn(
                        "Strength",
                        format="%.2f",
                        help="Theme strength score"
                    ),
                    "Competitive": st.column_config.TextColumn(
                        "Competitive",
                        help="Whether this is a competitive theme"
                    ),
                    "Companies": st.column_config.NumberColumn(
                        "Companies",
                        help="Number of companies mentioned"
                    ),
                    "Findings": st.column_config.NumberColumn(
                        "Findings",
                        help="Number of supporting findings"
                    ),
                    "Confidence": st.column_config.NumberColumn(
                        "Confidence",
                        format="%.2f",
                        help="Average confidence score"
                    ),
                    "Created": st.column_config.DatetimeColumn(
                        "Created",
                        format="YYYY-MM-DD HH:MM",
                        help="When the theme was created"
                    )
                }
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Themes Table (CSV)",
                data=csv,
                file_name=f"stage4_themes_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No displayable columns found in themes data.")
    else:
        st.info("No themes found. Run Stage 4 analysis to generate themes.")
    
    # Show detailed theme information in expandable sections
    if not themes_df.empty:
        st.markdown("---")
        st.subheader("🔍 Detailed Theme Information")
        
        for idx, theme in themes_df.iterrows():
            with st.expander(f"Theme {idx + 1}: {theme.get('theme_statement', 'No description')[:50]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Theme Statement:** {theme.get('theme_statement', 'N/A')}")
                    st.write(f"**Strength:** {theme.get('theme_strength', 'N/A')}")
                    st.write(f"**Competitive:** {'Yes' if theme.get('competitive_flag', False) else 'No'}")
                    st.write(f"**Companies:** {theme.get('company_count', 'N/A')}")
                
                with col2:
                    st.write(f"**Findings:** {theme.get('finding_count', 'N/A')}")
                    st.write(f"**Confidence:** {theme.get('avg_confidence_score', 'N/A')}")
                    st.write(f"**Pattern Type:** {theme.get('pattern_type', 'N/A')}")
                    st.write(f"**Created:** {theme.get('created_at', 'N/A')}")
                
                # Show quotes if available
                if theme.get('quotes'):
                    st.write("**Supporting Quotes:**")
                    quotes = theme['quotes']
                    if isinstance(quotes, list):
                        for i, quote in enumerate(quotes[:3]):  # Show first 3 quotes
                            if isinstance(quote, dict):
                                quote_text = quote.get('text', str(quote))
                            else:
                                quote_text = str(quote)
                            st.write(f"• {quote_text[:200]}...")
                    else:
                        st.write(f"• {str(quotes)[:200]}...") 