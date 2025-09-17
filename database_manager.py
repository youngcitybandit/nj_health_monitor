"""
Database manager for storing enforcement action data in Supabase.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for enforcement action data."""
    
    def __init__(self):
        """Initialize the database connection."""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    def store_entry(self, processed_data: Dict[str, Any]) -> bool:
        """
        Store a processed enforcement action entry in the database.
        
        Args:
            processed_data: The processed entry data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare data for storage
            db_data = self._prepare_db_data(processed_data)
            
            # Insert into database
            result = self.supabase.table('enforcement_actions').insert(db_data).execute()
            
            if result.data:
                logger.info(f"Successfully stored entry: {db_data['facility_name']}")
                return True
            else:
                logger.error("Failed to store entry - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error storing entry: {str(e)}")
            return False
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get an entry by its ID."""
        try:
            result = self.supabase.table('enforcement_actions').select('*').eq('id', entry_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting entry by ID: {str(e)}")
            return None
    
    def get_recent_entries(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent entries from the last N days."""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            result = self.supabase.table('enforcement_actions').select('*').gte('enforcement_date', cutoff_date.isoformat()).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting recent entries: {str(e)}")
            return []
    
    def get_entries_by_facility(self, facility_name: str) -> List[Dict[str, Any]]:
        """Get all entries for a specific facility."""
        try:
            result = self.supabase.table('enforcement_actions').select('*').ilike('facility_name', f'%{facility_name}%').execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting entries by facility: {str(e)}")
            return []
    
    def get_high_priority_entries(self) -> List[Dict[str, Any]]:
        """Get high priority entries."""
        try:
            result = self.supabase.table('enforcement_actions').select('*').eq('severity_level', 'HIGH').order('priority_score', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting high priority entries: {str(e)}")
            return []
    
    def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing entry."""
        try:
            result = self.supabase.table('enforcement_actions').update(updates).eq('id', entry_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating entry: {str(e)}")
            return False
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry."""
        try:
            result = self.supabase.table('enforcement_actions').delete().eq('id', entry_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting entry: {str(e)}")
            return False
    
    def _prepare_db_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for database storage."""
        structured = processed_data.get('structured_data', {})
        
        db_data = {
            'id': processed_data.get('id'),
            'scraped_at': processed_data.get('scraped_at'),
            'facility_name': structured.get('facility_name', ''),
            'facility_address': structured.get('facility_address', ''),
            'facility_license_number': structured.get('facility_license_number', ''),
            'enforcement_date': structured.get('enforcement_date', ''),
            'enforcement_action_type': structured.get('enforcement_action_type', ''),
            'penalty_amount': structured.get('penalty_amount', ''),
            'violation_summary': structured.get('violation_summary', ''),
            'key_violations': structured.get('key_violations', []),
            'effective_date': structured.get('effective_date', ''),
            'contact_information': structured.get('contact_information', ''),
            'pdf_url': structured.get('pdf_url', ''),
            'severity_level': structured.get('severity_level', 'LOW'),
            'priority_score': structured.get('priority_score', 0),
            'raw_web_data': processed_data.get('web_data', {}),
            'raw_pdf_data': processed_data.get('pdf_data', {}),
            'validation': processed_data.get('validation', {})
        }
        
        return db_data
    
    def create_tables(self) -> bool:
        """Create the necessary database tables (if they don't exist)."""
        try:
            # Note: In Supabase, tables are typically created through the dashboard
            # This method is here for reference and could be used with SQL commands
            logger.info("Tables should be created through Supabase dashboard")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            # Get total count
            total_result = self.supabase.table('enforcement_actions').select('id', count='exact').execute()
            total_count = total_result.count if hasattr(total_result, 'count') else 0
            
            # Get recent count (last 30 days)
            recent_result = self.supabase.table('enforcement_actions').select('id', count='exact').gte('enforcement_date', 
                (datetime.now().replace(day=datetime.now().day - 30)).isoformat()).execute()
            recent_count = recent_result.count if hasattr(recent_result, 'count') else 0
            
            # Get severity breakdown
            severity_result = self.supabase.table('enforcement_actions').select('severity_level').execute()
            severity_breakdown = {}
            if severity_result.data:
                for entry in severity_result.data:
                    level = entry.get('severity_level', 'UNKNOWN')
                    severity_breakdown[level] = severity_breakdown.get(level, 0) + 1
            
            return {
                'total_entries': total_count,
                'recent_entries_30_days': recent_count,
                'severity_breakdown': severity_breakdown,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
