"""
Client Configuration for Single Client Focus
Simple, clean configuration for managing client access
"""

import os
from typing import Dict, Any, Optional

class ClientConfig:
    """Simple client configuration for single client focus"""
    
    def __init__(self):
        # Default client configuration
        self.default_client_id = "rev_winloss_2024"
        
        # Client metadata
        self.client_metadata = {
            "rev_winloss_2024": {
                "company": "Rev",
                "project": "Win/Loss Analysis",
                "year": "2024",
                "description": "Customer interview analysis for Rev's win/loss research",
                "data_sources": ["stage1_data_responses", "stage3_findings", "stage4_themes", "executive_themes", "criteria_scorecard"],
                "access_level": "full",
                "features_enabled": ["chat", "insights", "executive_summary", "data_export"]
            }
        }
    
    def get_client_id(self) -> str:
        """Get the current client ID from environment or default"""
        return os.getenv('CLIENT_ID', self.default_client_id)
    
    def validate_client_id(self, client_id: str) -> bool:
        """Validate client ID format"""
        if not client_id:
            return False
        
        # Simple validation: must contain underscore and be alphanumeric + underscore
        parts = client_id.split('_')
        if len(parts) < 2:
            return False
        
        # Check if all parts are valid
        for part in parts:
            if not part.replace('_', '').isalnum():
                return False
        
        return True
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client information"""
        return self.client_metadata.get(client_id)
    
    def get_supported_client_ids(self) -> list:
        """Get list of supported client IDs"""
        return list(self.client_metadata.keys())
    
    def format_client_id(self, company: str, project: str, year: str) -> str:
        """Format a client ID from components"""
        return f"{company.lower()}_{project.lower()}_{year}"
    
    def parse_client_id(self, client_id: str) -> Dict[str, str]:
        """Parse client ID into components"""
        parts = client_id.split('_')
        if len(parts) >= 3:
            return {
                'company': parts[0],
                'project': parts[1],
                'year': parts[2]
            }
        elif len(parts) == 2:
            return {
                'company': parts[0],
                'project': parts[1],
                'year': 'current'
            }
        else:
            return {'company': client_id, 'project': 'unknown', 'year': 'unknown'}

# Global client configuration instance
client_config = ClientConfig()

def get_client_id() -> str:
    """Get current client ID"""
    return client_config.get_client_id()

def validate_client_id(client_id: str) -> bool:
    """Validate client ID format"""
    return client_config.validate_client_id(client_id)

def get_client_info(client_id: str) -> Optional[Dict[str, Any]]:
    """Get client information"""
    return client_config.get_client_info(client_id)

def format_client_id(company: str, project: str, year: str) -> str:
    """Format a client ID from components"""
    return client_config.format_client_id(company, project, year)

def parse_client_id(client_id: str) -> Dict[str, str]:
    """Parse client ID into components"""
    return client_config.parse_client_id(client_id) 