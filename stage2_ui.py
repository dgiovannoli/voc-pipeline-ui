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
        st.warning("⚠️ **Client ID Required**")
        st.info("Please set a Client ID in the sidebar before proceeding.")
        st.info("💡 **How to set Client ID:**")
        st.info("1. Look in the sidebar under '🏢 Client Settings'")
        st.info("2. Enter a unique identifier for this client's data")
        st.info("3. Press Enter to save")
        st.stop()
    return client_id

def run_stage2_analysis():
    """Run Stage 2 analysis using enhanced single-table analyzer with progress tracking"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return None
    
    try:
        from enhanced_single_table_stage2 import EnhancedSingleTableStage2, stage2_progress_data, stage2_progress_lock
        client_id = get_client_id()
        
        # Create enhanced analyzer with conservative parallel processing
        analyzer = EnhancedSingleTableStage2(batch_size=50, max_workers=2)
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Start the analysis in a separate thread to allow progress updates
        import threading
        result_container = {"result": None, "error": None}
        
        def run_analysis():
            try:
                result = analyzer.process_incremental(client_id=client_id)
                result_container["result"] = result
            except Exception as e:
                result_container["error"] = str(e)
        
        # Start analysis thread
        analysis_thread = threading.Thread(target=run_analysis)
        analysis_thread.start()
        
        # Monitor progress
        while analysis_thread.is_alive():
            with stage2_progress_lock:
                if stage2_progress_data["total_responses"] > 0:
                    progress = stage2_progress_data["completed_responses"] / stage2_progress_data["total_responses"]
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {stage2_progress_data['completed_responses']}/{stage2_progress_data['total_responses']} responses")
                else:
                    status_text.text("Initializing enhanced analysis...")
            time.sleep(0.1)
        
        # Wait for completion
        analysis_thread.join()
        
        # Final progress update
        progress_bar.progress(1.0)
        status_text.text("✅ Enhanced analysis complete!")
        
        # Check for errors
        if result_container["error"]:
            st.error(f"❌ Analysis failed: {result_container['error']}")
            return None
            
        return result_container["result"]
        
    except ImportError as e:
        st.error(f"❌ Failed to import enhanced analyzer: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Analysis failed: {e}")
        return None

def show_stage2_overview():
    """Show Stage 2 overview with enhanced single-table approach"""
    st.title("📊 Stage 2: Enhanced Sentiment & Impact Analysis")
    
    # Enhanced description
    st.markdown("""
    **🎯 Simplified Single-Table Analysis**
    
    Stage 2 now uses a **unified approach** that enhances your Stage 1 data directly:
    
    **✨ Key Features:**
    - **🎭 Sentiment Analysis**: Positive, negative, neutral, or mixed customer emotions
    - **📈 Impact Scoring**: 1-5 scale rating of business decision influence  
    - **🎯 Harmonized Categories**: Uses Stage 1 harmonized subjects as natural criteria
    - **⚡ Single Table**: All data stored in enhanced `stage1_data_responses` table
    
    **📋 What This Replaces:**
    - ❌ Complex business criteria mapping
    - ❌ Separate Stage 2 labeling table
    - ❌ Manual relevance scoring
    - ❌ Multiple impact metrics
    
    **🎉 Benefits:**
    - ✅ **Simpler workflow** - one table, cleaner data flow
    - ✅ **Voice-of-customer driven** - uses actual customer language patterns  
    - ✅ **Higher quality** - LLM focuses on sentiment + impact only
    - ✅ **Better performance** - eliminates complex joins and mappings
    """)

def show_stage2_analysis():
    """Main Stage 2 analysis interface with enhanced single-table approach"""
    client_id = get_client_id()
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return
    
    # Header with enhanced branding
    st.header("🚀 Enhanced Stage 2 Analysis")
    st.markdown(f"**Client:** `{client_id}` | **Approach:** Single-Table Sentiment & Impact")
    
    try:
        # Get Stage 1 data to check readiness
        stage1_df = db.get_stage1_data_responses(client_id=client_id)
        
        if stage1_df.empty:
            st.warning("⚠️ **No Stage 1 Data Found**")
            st.info("📋 Please complete Stage 1 processing first.")
            st.info("🔄 Go to **Stage 1** tab to upload and process interview transcripts.")
            return
        
        # Check harmonization status
        harmonized_count = stage1_df[stage1_df['harmonized_subject'].notna()].shape[0] if 'harmonized_subject' in stage1_df.columns else 0
        total_responses = len(stage1_df)
        
        # Status metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Total Responses", total_responses)
        
        with col2:
            st.metric("🎯 Harmonized", harmonized_count)
        
        with col3:
            # Check if Stage 2 analysis has been run
            stage2_analyzed = stage1_df[stage1_df['sentiment'].notna()].shape[0] if 'sentiment' in stage1_df.columns else 0
            st.metric("📊 Analyzed", stage2_analyzed)
        
        with col4:
            coverage = (stage2_analyzed / total_responses * 100) if total_responses > 0 else 0
            st.metric("📈 Coverage", f"{coverage:.1f}%")
        
        # Harmonization status
        if harmonized_count == 0:
            st.warning("⚠️ **Harmonization Recommended**")
            st.info("🎯 While not required, **harmonized subjects** provide better insights for Stage 2 analysis.")
            st.info("📍 Go to **Stage 1** → **Enhanced Subject Analysis** to run harmonization.")
        elif harmonized_count < total_responses:
            st.info(f"📊 **Partial Harmonization**: {harmonized_count}/{total_responses} responses harmonized")
        else:
            st.success("✅ **Full Harmonization Complete!**")
        
        # Analysis status and action
        if stage2_analyzed == 0:
            st.info("🚀 **Ready for Enhanced Stage 2 Analysis**")
            st.markdown("**This will add:**")
            st.markdown("- 🎭 **Sentiment scores** (positive/negative/neutral/mixed)")
            st.markdown("- 📈 **Impact ratings** (1-5 scale for business decision influence)")
            st.markdown("- 🧠 **LLM reasoning** for transparency")
            
            if st.button("🚀 Run Enhanced Stage 2 Analysis", type="primary"):
                with st.spinner("Running enhanced sentiment & impact analysis..."):
                    result = run_stage2_analysis()
                    
                    if result:
                        st.success("✅ **Enhanced Stage 2 Analysis Complete!**")
                        
                        # Show summary results
                        st.subheader("📊 Analysis Summary")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("✅ Successful", result.get('successful_analyses', 0))
                        with col2:
                            st.metric("❌ Failed", result.get('failed_analyses', 0))
                        with col3:
                            avg_impact = result.get('average_impact_score', 0)
                            st.metric("📊 Avg Impact", f"{avg_impact:.1f}/5")
                        
                        if result.get('sentiment_distribution'):
                            st.subheader("🎭 Sentiment Distribution")
                            sentiment_data = result['sentiment_distribution']
                            sentiment_df = pd.DataFrame(list(sentiment_data.items()), columns=['Sentiment', 'Count'])
                            st.dataframe(sentiment_df, use_container_width=True)
                        
                        st.rerun()
                    else:
                        st.error("❌ Analysis failed. Check logs for details.")
        
        elif stage2_analyzed < total_responses:
            st.warning(f"⚠️ **Partial Analysis**: {stage2_analyzed}/{total_responses} responses analyzed")
            
            if st.button("🔄 Complete Analysis", type="secondary"):
                with st.spinner("Completing enhanced analysis..."):
                    result = run_stage2_analysis()
                    if result:
                        st.success("✅ Analysis completed!")
                        st.rerun()
        
        else:
            st.success("✅ **Enhanced Stage 2 Analysis Complete!**")
            
            # Show enhanced analysis results
            st.subheader("📊 Enhanced Analysis Results")
            
            # Refresh data to get latest analysis
            enhanced_df = db.get_stage1_data_responses(client_id=client_id)
            
            if 'sentiment' in enhanced_df.columns and 'impact_score' in enhanced_df.columns:
                # Sentiment distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🎭 Sentiment Distribution**")
                    sentiment_counts = enhanced_df['sentiment'].value_counts()
                    st.dataframe(sentiment_counts.reset_index().rename(columns={'index': 'Sentiment', 'sentiment': 'Count'}), use_container_width=True)
                
                with col2:
                    st.write("**📈 Impact Score Distribution**")
                    impact_counts = enhanced_df['impact_score'].value_counts().sort_index()
                    st.dataframe(impact_counts.reset_index().rename(columns={'index': 'Impact Score', 'impact_score': 'Count'}), use_container_width=True)
                
                # High-impact insights
                st.subheader("🚨 High-Impact Insights")
                high_impact = enhanced_df[enhanced_df['impact_score'] >= 4]
                
                if not high_impact.empty:
                    st.write(f"**Found {len(high_impact)} high-impact responses (score ≥4):**")
                    
                    display_cols = ['subject', 'sentiment', 'impact_score']
                    if 'harmonized_subject' in high_impact.columns:
                        display_cols.insert(1, 'harmonized_subject')
                    
                    display_cols.extend(['verbatim_response'])
                    available_cols = [col for col in display_cols if col in high_impact.columns]
                    
                    display_df = high_impact[available_cols].copy()
                    if 'verbatim_response' in display_df.columns:
                        display_df['verbatim_response'] = display_df['verbatim_response'].str[:150] + '...'
                    
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("No high-impact responses found (score ≥4)")
                
                # Download enhanced data
                st.subheader("📥 Download Enhanced Data")
                enhanced_csv = enhanced_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download Enhanced Stage 1+2 Data",
                    data=enhanced_csv,
                    file_name=f"enhanced_stage1_stage2_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
    except Exception as e:
        st.error(f"❌ Error in Stage 2 analysis: {e}")
        import traceback
        st.text(traceback.format_exc())

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
                
                # Enhanced system info
                st.info("🎯 **Enhanced Single-Table Analysis**: This system provides simplified sentiment and impact analysis directly in the Stage 1 table for streamlined workflow.")
                
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
                    from enhanced_single_table_stage2 import EnhancedSingleTableStage2
                    client_id = get_client_id()
                    analyzer = EnhancedSingleTableStage2(batch_size=50, max_workers=1)  # Sequential
                    result = analyzer.process_incremental(client_id=client_id)
                
                if result:
                    st.success("✅ Quote labeling complete!")
                    
                    # Show enhancement information if available
                    enhancement_info = result.get('enhancement_info', {})
                    mapping_stats = result.get('mapping_stats', {})
                    
                    if enhancement_info.get('subject_driven_routing'):
                        st.success("🎯 **Enhanced Analysis Complete!**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Responses Processed", result.get('processed', 0))
                        with col2:
                            st.metric("Subject Mappings Used", enhancement_info.get('mappings_used', 0))
                        with col3:
                            quality_enabled = "✅ Enabled" if enhancement_info.get('quality_weighting') else "❌ Disabled"
                            st.metric("Quality Weighting", quality_enabled)
                        
                        # Show criterion distribution
                        if mapping_stats.get('criterion_distribution'):
                            st.subheader("📊 Subject-to-Criteria Distribution")
                            criterion_dist = mapping_stats['criterion_distribution']
                            
                            # Create a simple bar chart of criteria distribution
                            import pandas as pd
                            dist_df = pd.DataFrame(list(criterion_dist.items()), columns=['Criterion', 'Count'])
                            st.bar_chart(dist_df.set_index('Criterion'))
                            
                            # Show high-confidence routing
                            high_conf = mapping_stats.get('high_confidence_responses', 0)
                            total_responses = result.get('processed', 0)
                            if total_responses > 0:
                                conf_percentage = (high_conf / total_responses) * 100
                                st.info(f"🎯 **Routing Quality**: {high_conf}/{total_responses} responses ({conf_percentage:.1f}%) had high-confidence subject mapping")
                    
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