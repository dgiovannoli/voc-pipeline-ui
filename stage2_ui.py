import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import time

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

def run_stage2_analysis():
    """Run Stage 2 analysis using database with progress tracking"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return None
    
    try:
        from enhanced_stage2_analyzer import SupabaseStage2Analyzer, stage2_progress_data, stage2_progress_lock
        client_id = get_client_id()
        
        # Create analyzer with conservative parallel processing
        analyzer = SupabaseStage2Analyzer(batch_size=50, max_workers=2)
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Start the analysis in a separate thread to allow progress updates
        import threading
        
        def run_analysis():
            return analyzer.process_incremental(client_id=client_id)
        
        # Start analysis thread
        analysis_thread = threading.Thread(target=run_analysis)
        analysis_thread.start()
        
        # Monitor progress
        while analysis_thread.is_alive():
            with stage2_progress_lock:
                completed = stage2_progress_data.get("completed_batches", 0)
                total = stage2_progress_data.get("total_batches", 0)
                progress = completed / total if total > 0 else 0
            
            progress_bar.progress(progress)
            status_text.text(f"Processing batches... {completed}/{total} completed")
            
            # Update every 1 second
            time.sleep(1)
        
        # Get final result
        result = run_analysis()  # This will be the actual result
        
        # Final progress update
        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")
        
        return result
        
    except Exception as e:
        st.error(f"❌ Stage 2 analysis failed: {e}")
        return None

def get_stage2_summary():
    """Get Stage 2 summary from database"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        client_id = get_client_id()
        summary = db.get_summary_statistics(client_id=client_id)
        return summary
    except Exception as e:
        st.error(f"❌ Failed to get summary: {e}")
        return None

def show_labeled_quotes():
    """Show labeled quotes with color coding"""
    st.subheader("📋 Labeled Quotes (Stage 2 Results)")
    client_id = get_client_id()
    df = db.get_stage2_response_labeling(client_id=client_id)
    if df.empty:
        st.info("No labeled quotes found. Run Stage 2 analysis.")
        return
    
    # Show a summary table with new scoring system
    display_cols = [
        'quote_id', 'criterion', 'relevance_score', 'sentiment', 'priority', 'confidence',
        'relevance_explanation', 'deal_weighted_score', 'context_keywords', 'question_relevance'
    ]
    display_cols = [col for col in display_cols if col in df.columns]
    
    # Create a styled dataframe with color coding for sentiment
    styled_df = df[display_cols].copy()
    
    # Apply color coding to sentiment column
    def color_sentiment(val):
        if pd.isna(val):
            return 'background-color: lightgray'
        elif val == 'positive':
            return 'background-color: lightgreen; color: darkgreen'
        elif val == 'negative':
            return 'background-color: lightcoral; color: darkred'
        elif val == 'neutral':
            return 'background-color: lightblue; color: darkblue'
        else:
            return 'background-color: lightyellow'
    
    # Apply styling
    styled_df = styled_df.style.applymap(color_sentiment, subset=['sentiment'])
    
    # Display the styled dataframe
    st.dataframe(styled_df, use_container_width=True)
    
    # Show scoring legend
    st.markdown("**🎨 Sentiment Color Coding:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🟢 **Positive** - Favorable feedback")
    with col2:
        st.markdown("🔴 **Negative** - Critical feedback")
    with col3:
        st.markdown("🔵 **Neutral** - Balanced feedback")
    with col4:
        st.markdown("🟡 **Other** - Mixed or unclear")
    
    # Show relevance score legend
    st.markdown("**📊 Relevance Score Interpretation:**")
    st.markdown("- **0-1.9**: Low relevance/not mentioned")
    st.markdown("- **2.0-2.9**: Clear mention/direct relevance")
    st.markdown("- **3.0-3.9**: Strong emphasis/important feedback")
    st.markdown("- **4.0-5.0**: Critical feedback/deal-breaking issue")
    
    # Export option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Labeled Quotes CSV",
        data=csv,
        file_name="labeled_quotes.csv",
        mime="text/csv",
        key="download_labeled_quotes"
    )

def show_stage2_response_labeling():
    """Stage 2: Response Labeling - Score quotes against 10 evaluation criteria"""
    st.title("🎯 Stage 2: Response Labeling")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        st.info("Please configure your .env file with database credentials")
        return
    
    # Check for data availability
    try:
        client_summary = db.get_client_summary()
        current_client = get_client_id()
        current_count = client_summary.get(current_client, 0)
        total_records = sum(client_summary.values())
        
        if total_records > 0 and current_count == 0:
            st.warning("⚠️ **Data Found But Not for Current Client**")
            st.info(f"📊 Found {total_records} total records across {len(client_summary)} clients, but 0 for current client '{current_client}'")
            st.info("💡 **Solution**: Go to 'Admin / Utilities' to see all data and set the correct client ID")
            
            if len(client_summary) > 1:
                st.subheader("🔧 Quick Fix: Switch Client")
                col1, col2 = st.columns(2)
                with col1:
                    available_clients = list(client_summary.keys())
                    new_client = st.selectbox(
                        "Select Client with Data",
                        available_clients,
                        index=0
                    )
                with col2:
                    if st.button("✅ Switch to This Client"):
                        st.session_state.client_id = new_client
                        st.success(f"✅ Switched to client: {new_client}")
                        st.info("🔄 Refreshing...")
                        st.rerun()
    except Exception as e:
        st.error(f"❌ Error loading client data: {e}")
    
    # Get summary statistics
    summary = get_stage2_summary()
    if summary and summary.get('total_quotes', 0) > 0:
        st.success(f"✅ Found {summary['total_quotes']} quotes ready for labeling")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Quotes", summary['total_quotes'])
        with col2:
            st.metric("Labeled Quotes", summary['quotes_with_scores'])
        with col3:
            st.metric("Analysis Coverage", f"{summary['coverage_percentage']}%")
        
        # Run analysis button
        if st.button("🔄 Label Quotes", type="primary", help="Label quotes against 10 evaluation criteria"):
            with st.spinner("Labeling quotes against criteria..."):
                # Add processing mode selection
                processing_mode = st.radio(
                    "Processing Mode",
                    ["Parallel (Faster)", "Sequential (More Stable)"],
                    horizontal=True,
                    help="Parallel processing is faster but may use more resources"
                )
                
                if processing_mode == "Parallel (Faster)":
                    result = run_stage2_analysis()
                else:
                    # Use sequential processing
                    from enhanced_stage2_analyzer import SupabaseStage2Analyzer
                    client_id = get_client_id()
                    analyzer = SupabaseStage2Analyzer(batch_size=50, max_workers=1)  # Sequential
                    result = analyzer.process_incremental(client_id=client_id)
                
                if result:
                    st.success("✅ Quote labeling complete!")
                    st.rerun()
                else:
                    st.error("❌ Quote labeling failed")
        
        # Show labeled quotes
        show_labeled_quotes()
        
        # Proceed to Stage 3
        if summary['quotes_with_scores'] > 0:
            if st.button("🔍 Proceed to Stage 3: Identify Findings", type="primary"):
                st.session_state.current_step = 3
                st.rerun()
    else:
        st.info("📤 Please upload and process files first, then extract quotes")
    
    # Show criteria information
    st.subheader("📊 10 Executive Criteria")
    criteria_info = """
    1. **Product Capability**: Functionality, features, performance, core solution fit
    2. **Implementation Onboarding**: Deployment ease, time-to-value, setup complexity
    3. **Integration Technical Fit**: APIs, data compatibility, technical architecture
    4. **Support Service Quality**: Post-sale support, responsiveness, expertise, SLAs
    5. **Security Compliance**: Data protection, certifications, governance, risk management
    6. **Market Position Reputation**: Brand trust, references, analyst recognition
    7. **Vendor Stability**: Financial health, roadmap clarity, long-term viability
    8. **Sales Experience Partnership**: Buying process quality, relationship building
    9. **Commercial Terms**: Price, contract flexibility, ROI, total cost of ownership
    10. **Speed Responsiveness**: Implementation timeline, decision-making speed, agility
    """
    st.markdown(criteria_info)
    
    # Show scoring system
    st.subheader("🎯 Scoring System")
    scoring_info = """
    **Binary + Intensity Scoring:**
    - **0**: Not relevant/not mentioned
    - **1**: Slight mention/indirect relevance  
    - **2**: Clear mention/direct relevance
    - **3**: Strong emphasis/important feedback
    - **4**: Critical feedback/deal-breaking issue
    - **5**: Exceptional praise/deal-winning strength
    
    **Deal Weighting:**
    - Lost deals: 1.2x base multiplier
    - Won deals: 0.9x base multiplier
    - Critical feedback: 1.5x multiplier
    - Minor feedback: 0.7x multiplier
    """
    st.markdown(scoring_info) 