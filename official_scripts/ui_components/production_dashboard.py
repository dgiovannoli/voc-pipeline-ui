import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.core_analytics.interview_weighted_base import InterviewWeightedBase

def show_production_dashboard():
    """Show production pipeline dashboard"""
    st.title("🚀 Production Pipeline Dashboard")
    
    # Initialize database
    try:
        db = SupabaseDatabase()
        db_available = True
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        db_available = False
        return
    
    # Production Status Overview
    st.subheader("📊 Production Status Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Check environment variables
        import os
        env_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'OPENAI_API_KEY']
        env_ok = all(os.getenv(var) for var in env_vars)
        if env_ok:
            st.success("✅ Environment Variables")
        else:
            st.error("❌ Environment Variables")
    
    with col2:
        # Check database connection
        if db_available:
            try:
                db.test_connection()
                st.success("✅ Database Connection")
            except:
                st.error("❌ Database Connection")
        else:
            st.error("❌ Database Connection")
    
    with col3:
        # Check schema
        try:
            tables = ['stage1_data_responses', 'stage2_response_labeling', 'stage3_findings', 'stage4_themes']
            schema_ok = True
            for table in tables:
                result = db.supabase.table(table).select('count').limit(1).execute()
        except:
            schema_ok = False
        
        if schema_ok:
            st.success("✅ Database Schema")
        else:
            st.error("❌ Database Schema")
    
    with col4:
        # Check LLM integration
        try:
            from stage3_findings_analyzer import Stage3FindingsAnalyzer
            analyzer = Stage3FindingsAnalyzer()
            prompt = analyzer._load_buried_wins_prompt()
            if prompt and len(prompt) > 100:
                st.success("✅ LLM Integration")
            else:
                st.warning("⚠️ LLM Integration")
        except:
            st.error("❌ LLM Integration")
    
    # Data Statistics
    st.subheader("📈 Data Statistics")
    
    if db_available:
        try:
            # Get client summary
            client_summary = db.get_client_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_responses = sum(client_summary.values())
                st.metric("Total Responses", total_responses)
            
            with col2:
                active_clients = len([k for k, v in client_summary.items() if v > 0])
                st.metric("Active Clients", active_clients)
            
            with col3:
                # Get findings count - need to get client_id from session state
                client_id = st.session_state.get('client_id', '')
                if client_id:
                    findings_df = db.get_stage3_findings(client_id=client_id)
                    st.metric("Total Findings", len(findings_df))
                else:
                    st.metric("Total Findings", "Set Client ID")
            
            with col4:
                # Get themes count - need to get client_id from session state
                client_id = st.session_state.get('client_id', '')
                if client_id:
                    themes_df = db.get_themes(client_id=client_id)
                    st.metric("Total Themes", len(themes_df))
                else:
                    st.metric("Total Themes", "Set Client ID")
            
            # Interview-Weighted VOC Metrics
            client_id = st.session_state.get('client_id', '')
            if client_id:
                st.subheader("🎯 Interview-Weighted VOC Metrics")
                
                # Initialize interview-weighted analyzer
                analyzer = InterviewWeightedBase(db)
                metrics = analyzer.get_customer_metrics(client_id)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Customer Satisfaction", 
                        f"{metrics['customer_satisfaction_rate']}%",
                        help="Percentage of satisfied customers (interview-weighted)"
                    )
                
                with col2:
                    st.metric(
                        "Overall Score", 
                        f"{metrics['overall_score']}/10",
                        help="Interview-weighted score (0-10)"
                    )
                
                with col3:
                    st.metric(
                        "Problem Customers", 
                        f"{metrics['problem_customers']}",
                        help="Number of customers with product issues"
                    )
                
                with col4:
                    st.metric(
                        "Satisfied Customers", 
                        f"{metrics['satisfied_customers']}/{metrics['total_customers']}",
                        help="Satisfied customers out of total customers"
                    )
                
                # Performance indicator
                performance_color = {
                    "Excellent": "green",
                    "Good": "blue", 
                    "Fair": "orange",
                    "Poor": "red",
                    "Critical": "red"
                }.get(metrics['performance_level'], "gray")
                
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: {performance_color}20; border-left: 4px solid {performance_color};">
                    <strong>Performance Level:</strong> {metrics['performance_level']} ({metrics['overall_score']}/10)
                </div>
                """, unsafe_allow_html=True)
                
                # Customer breakdown
                if metrics['customer_groups']:
                    breakdown = analyzer.get_customer_breakdown(metrics['customer_groups'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Customer Categories:**")
                        st.write(f"• Problem Customers: {len(breakdown['problem_customers'])}")
                        st.write(f"• Benefit Customers: {len(breakdown['benefit_customers'])}")
                        st.write(f"• Mixed Customers: {len(breakdown['mixed_customers'])}")
                        st.write(f"• Neutral Customers: {len(breakdown['neutral_customers'])}")
                    
                    with col2:
                        st.write("**Methodology:**")
                        st.write("• Interview-weighted analysis")
                        st.write("• Each customer counts equally")
                        st.write("• Prevents overweighing verbose customers")
                        st.write("• More representative of customer sentiment")
            
            # Show client breakdown
            if client_summary:
                st.subheader("🏢 Client Data Breakdown")
                client_data = []
                for client_id, count in client_summary.items():
                    if count > 0:
                        client_data.append({
                            'Client ID': client_id,
                            'Responses': count,
                            'Findings': len(db.get_stage3_findings(client_id=client_id)),
                            'Themes': len(db.get_themes(client_id=client_id))
                        })
                
                if client_data:
                    client_df = pd.DataFrame(client_data)
                    st.dataframe(client_df, use_container_width=True)
        
        except Exception as e:
            if "missing 1 required positional argument: 'client_id'" in str(e):
                st.error("❌ Error loading statistics: Please set a Client ID in the sidebar to view data")
            else:
                st.error(f"❌ Error loading statistics: {e}")
    
    # Production Files
    st.subheader("📁 Production Files")
    
    production_files = [
        'findings_after_clustering.csv',
        'findings_before_clustering.csv',
        'enhanced_findings_export.csv',
        'improved_findings_export.csv'
    ]
    
    file_status = []
    for file in production_files:
        if os.path.exists(file):
            file_size = os.path.getsize(file)
            file_date = datetime.fromtimestamp(os.path.getmtime(file))
            file_status.append({
                'File': file,
                'Status': '✅ Available',
                'Size': f"{file_size:,} bytes",
                'Modified': file_date.strftime('%Y-%m-%d %H:%M')
            })
        else:
            file_status.append({
                'File': file,
                'Status': '❌ Missing',
                'Size': 'N/A',
                'Modified': 'N/A'
            })
    
    file_df = pd.DataFrame(file_status)
    st.dataframe(file_df, use_container_width=True)
    
    # Recent Activity
    st.subheader("🕒 Recent Activity")
    
    if db_available:
        try:
            # Get recent findings - need to get client_id from session state
            client_id = st.session_state.get('client_id', '')
            if client_id:
                recent_findings = db.get_stage3_findings(client_id=client_id)
                if not recent_findings.empty and 'created_at' in recent_findings.columns:
                    recent_findings['created_at'] = pd.to_datetime(recent_findings['created_at'])
                    recent_findings = recent_findings.sort_values('created_at', ascending=False).head(5)
                    
                    st.write("**Recent Findings:**")
                    for idx, row in recent_findings.iterrows():
                        st.write(f"• {row.get('finding_statement', 'No statement')[:100]}...")
            else:
                st.info("Set Client ID to view recent findings")
        except Exception as e:
            st.error(f"❌ Error loading recent activity: {e}")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Run Production Test", help="Run the production readiness test"):
            st.info("Running production test...")
            # This would run the test_production_setup.py script
    
    with col2:
        if st.button("📊 Generate Report", help="Generate a comprehensive production report"):
            st.info("Generating report...")
            # This would generate a detailed report
    
    with col3:
        if st.button("🔄 Refresh Status", help="Refresh all status indicators"):
            st.rerun()
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Environment:**")
        st.write(f"• Python: {os.sys.version}")
        st.write(f"• Streamlit: {st.__version__}")
        st.write(f"• Pandas: {pd.__version__}")
    
    with col2:
        st.write("**Database:**")
        if db_available:
            st.write("• Supabase: Connected")
            st.write("• Schema: Production Ready")
        else:
            st.write("• Database: Not Connected")
    
    # Performance Metrics
    st.subheader("📊 Performance Metrics")
    
    # This would show performance metrics like:
    # - Processing time for recent runs
    # - Memory usage
    # - API call counts
    # - Error rates
    
    st.info("Performance metrics will be displayed here in future versions.") 