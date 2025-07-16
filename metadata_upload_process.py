#!/usr/bin/env python3
"""
Metadata Upload Process for VOC Pipeline
Allows users to upload company information and other metadata for interviews
"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import streamlit as st
from datetime import datetime

load_dotenv()

class MetadataUploadProcess:
    def __init__(self):
        self.db = SupabaseDatabase()
    
    def get_existing_interviews(self, client_id):
        """Get existing interviews that need metadata"""
        try:
            response = self.db.supabase.table('stage1_data_responses').select(
                'response_id,interviewee_name,company,date_of_interview,subject'
            ).eq('client_id', client_id).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                # Group by interviewee to show unique interviews
                unique_interviews = df.groupby('interviewee_name').agg({
                    'response_id': 'count',
                    'company': 'first',
                    'date_of_interview': 'first',
                    'subject': lambda x: ', '.join(set(x))
                }).reset_index()
                
                unique_interviews.columns = ['Interviewee', 'Response Count', 'Current Company', 'Date', 'Subjects']
                return unique_interviews
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error fetching interviews: {e}")
            return pd.DataFrame()
    
    def update_interview_metadata(self, client_id, interviewee_name, company, industry, firm_size, role, notes):
        """Update metadata for a specific interviewee"""
        try:
            # Update all responses for this interviewee
            response = self.db.supabase.table('stage1_data_responses').update({
                'company': company,
                'industry': industry,
                'firm_size': firm_size,
                'interviewee_role': role,
                'metadata_notes': notes,
                'metadata_updated_at': datetime.now().isoformat()
            }).eq('client_id', client_id).eq('interviewee_name', interviewee_name).execute()
            
            if response.data:
                st.success(f"✅ Updated metadata for {interviewee_name}")
                return True
            else:
                st.warning(f"No responses found for {interviewee_name}")
                return False
                
        except Exception as e:
            st.error(f"Error updating metadata: {e}")
            return False
    
    def bulk_upload_metadata(self, client_id, csv_file):
        """Bulk upload metadata from CSV file"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            required_columns = ['interviewee_name', 'company']
            
            # Validate CSV structure
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"Missing required columns: {missing_columns}")
                return False
            
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Update metadata for each interviewee
                    response = self.db.supabase.table('stage1_data_responses').update({
                        'company': row.get('company', ''),
                        'industry': row.get('industry', ''),
                        'firm_size': row.get('firm_size', ''),
                        'interviewee_role': row.get('role', ''),
                        'metadata_notes': row.get('notes', ''),
                        'metadata_updated_at': datetime.now().isoformat()
                    }).eq('client_id', client_id).eq('interviewee_name', row['interviewee_name']).execute()
                    
                    if response.data:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    st.error(f"Error updating {row.get('interviewee_name', 'Unknown')}: {e}")
            
            st.success(f"✅ Bulk upload complete: {success_count} successful, {error_count} errors")
            return True
            
        except Exception as e:
            st.error(f"Error processing CSV file: {e}")
            return False
    
    def create_metadata_template(self):
        """Create a template CSV for metadata upload"""
        template_data = {
            'interviewee_name': ['Alex Vandenberg', 'Angela Law', 'Cyrus Nazarian'],
            'company': ['Company A', 'Company B', 'Company C'],
            'industry': ['Legal Services', 'Legal Services', 'Legal Services'],
            'firm_size': ['Solo Practice', 'Small Firm (2-10)', 'Mid-size Firm (11-50)'],
            'role': ['Attorney', 'Attorney', 'Attorney'],
            'notes': ['Criminal defense focus', 'Family law practice', 'Corporate litigation']
        }
        
        df = pd.DataFrame(template_data)
        return df

def main():
    st.title("📊 Metadata Upload Process")
    st.write("Upload and manage company information and metadata for interviews")
    
    # Initialize the process
    uploader = MetadataUploadProcess()
    
    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Choose an option:",
        ["View Existing Data", "Update Individual Metadata", "Bulk Upload", "Download Template"]
    )
    
    # Client ID selection
    client_id = st.sidebar.selectbox("Select Client ID:", ["Rev", "Test", "Demo"])
    
    if page == "View Existing Data":
        st.header("📋 Existing Interview Data")
        
        interviews = uploader.get_existing_interviews(client_id)
        if not interviews.empty:
            st.dataframe(interviews, use_container_width=True)
            
            # Show company distribution
            st.subheader("📊 Company Distribution")
            company_counts = interviews['Current Company'].value_counts()
            st.bar_chart(company_counts)
        else:
            st.info("No interview data found for this client")
    
    elif page == "Update Individual Metadata":
        st.header("✏️ Update Individual Metadata")
        
        # Get existing interviews
        interviews = uploader.get_existing_interviews(client_id)
        if not interviews.empty:
            # Select interviewee
            interviewee = st.selectbox("Select Interviewee:", interviews['Interviewee'].tolist())
            
            if interviewee:
                # Get current metadata
                current_data = interviews[interviews['Interviewee'] == interviewee].iloc[0]
                
                # Form for updating metadata
                with st.form("metadata_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        company = st.text_input("Company:", value=current_data['Current Company'])
                        industry = st.text_input("Industry:", value="Legal Services")
                        firm_size = st.selectbox("Firm Size:", [
                            "Solo Practice", "Small Firm (2-10)", "Mid-size Firm (11-50)", 
                            "Large Firm (50+)", "Government", "Non-profit"
                        ])
                    
                    with col2:
                        role = st.text_input("Role:", value="Attorney")
                        notes = st.text_area("Notes:", value="")
                    
                    submitted = st.form_submit_button("Update Metadata")
                    
                    if submitted:
                        uploader.update_interview_metadata(
                            client_id, interviewee, company, industry, firm_size, role, notes
                        )
        else:
            st.info("No interview data found for this client")
    
    elif page == "Bulk Upload":
        st.header("📁 Bulk Upload Metadata")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV file with metadata",
            type=['csv'],
            help="CSV should have columns: interviewee_name, company, industry, firm_size, role, notes"
        )
        
        if uploaded_file is not None:
            if st.button("Process Upload"):
                uploader.bulk_upload_metadata(client_id, uploaded_file)
    
    elif page == "Download Template":
        st.header("📄 Download Template")
        
        template_df = uploader.create_metadata_template()
        st.dataframe(template_df, use_container_width=True)
        
        # Download button
        csv = template_df.to_csv(index=False)
        st.download_button(
            label="Download Template CSV",
            data=csv,
            file_name=f"metadata_template_{client_id}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main() 