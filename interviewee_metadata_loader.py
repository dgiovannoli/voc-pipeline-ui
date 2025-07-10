"""
Interviewee Metadata Loader
Handles loading and mapping of interviewee metadata from CSV files.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class IntervieweeMetadataLoader:
    """Loads and manages interviewee metadata for attribution in findings"""
    
    def __init__(self, metadata_path: str = 'interviewee_metadata.csv'):
        self.metadata_path = metadata_path
        self.metadata_df = None
        self.interview_mapping = {}
        self.load_metadata()
    
    def load_metadata(self) -> bool:
        """Load interviewee metadata from CSV file"""
        try:
            self.metadata_df = pd.read_csv(self.metadata_path)
            logger.info(f"✅ Loaded {len(self.metadata_df)} interviewee records from {self.metadata_path}")
            
            # Create mapping for quick lookups
            self.interview_mapping = self.metadata_df.set_index('interview_id').to_dict('index')
            
            return True
        except FileNotFoundError:
            logger.warning(f"⚠️ Metadata file not found: {self.metadata_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading metadata: {e}")
            return False
    
    def get_interviewee_info(self, interview_id: int) -> Optional[Dict]:
        """Get interviewee information by interview ID"""
        if interview_id in self.interview_mapping:
            return self.interview_mapping[interview_id]
        return None
    
    def get_company_and_interviewee(self, interview_id: int) -> Tuple[str, str]:
        """Get company and interviewee name for a given interview ID"""
        info = self.get_interviewee_info(interview_id)
        if info:
            return info.get('company', 'Unknown'), info.get('interviewee_name', 'Unknown')
        return 'Unknown', 'Unknown'
    
    def get_all_companies(self) -> List[str]:
        """Get list of all companies in metadata"""
        if self.metadata_df is not None:
            return self.metadata_df['company'].unique().tolist()
        return []
    
    def get_all_interviewees(self) -> List[str]:
        """Get list of all interviewees in metadata"""
        if self.metadata_df is not None:
            return self.metadata_df['interviewee_name'].unique().tolist()
        return []
    
    def validate_interview_id(self, interview_id: int) -> bool:
        """Check if interview ID exists in metadata"""
        return interview_id in self.interview_mapping
    
    def get_metadata_summary(self) -> Dict:
        """Get summary statistics of loaded metadata"""
        if self.metadata_df is None:
            return {'total_interviews': 0, 'total_companies': 0, 'total_interviewees': 0}
        
        return {
            'total_interviews': len(self.metadata_df),
            'total_companies': self.metadata_df['company'].nunique(),
            'total_interviewees': self.metadata_df['interviewee_name'].nunique(),
            'companies': self.get_all_companies(),
            'interviewees': self.get_all_interviewees()
        }

def create_sample_metadata():
    """Create a sample metadata file if it doesn't exist"""
    sample_data = {
        'interview_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'interviewee_name': [
            'Company A Interviewee 1', 'Company B Interviewee 2', 'Company C Interviewee 1',
            'Company D Interviewee 1', 'Company E Interviewee 1', 'Company F Interviewee 1',
            'Company G Interviewee 1', 'Company H Interviewee 1', 'Company I Interviewee 1',
            'Company J Interviewee 1'
        ],
        'company': [
            'Company A', 'Company B', 'Company C', 'Company D', 'Company E',
            'Company F', 'Company G', 'Company H', 'Company I', 'Company J'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv('interviewee_metadata.csv', index=False)
    logger.info("✅ Created sample interviewee metadata file")

if __name__ == "__main__":
    # Test the loader
    loader = IntervieweeMetadataLoader()
    summary = loader.get_metadata_summary()
    print(f"Metadata Summary: {summary}")
    
    # Test lookup
    company, interviewee = loader.get_company_and_interviewee(1)
    print(f"Interview 1: {interviewee} from {company}") 