"""
Data processor for structuring and validating parsed enforcement action data.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and structures parsed enforcement action data."""
    
    def __init__(self):
        self.enforcement_action_types = [
            'Notice of Assessment of Penalties',
            'Curtailment',
            'Cease & Desist',
            'Directed Plan of Correction',
            'Lifting Curtailment',
            'Revocation',
            'Suspension',
            'Amended Notice of Assessment of Penalties'
        ]
    
    def process_entry(self, web_entry: Dict[str, Any], pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and structure a complete enforcement action entry.
        
        Args:
            web_entry: Data scraped from the website
            pdf_data: Data parsed from the PDF
            
        Returns:
            Structured data ready for storage and email generation
        """
        try:
            # Merge web and PDF data
            processed_data = {
                'id': self._generate_entry_id(web_entry),
                'scraped_at': datetime.now().isoformat(),
                'web_data': web_entry,
                'pdf_data': pdf_data,
                'structured_data': {}
            }
            
            # Extract and structure key information
            structured = self._extract_structured_data(web_entry, pdf_data)
            processed_data['structured_data'] = structured
            
            # Validate the data
            validation_result = self._validate_data(processed_data)
            processed_data['validation'] = validation_result
            
            logger.info(f"Successfully processed entry: {structured.get('facility_name', 'Unknown')}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return {
                'id': self._generate_entry_id(web_entry),
                'scraped_at': datetime.now().isoformat(),
                'web_data': web_entry,
                'pdf_data': pdf_data,
                'structured_data': {},
                'validation': {'valid': False, 'errors': [str(e)]}
            }
    
    def _generate_entry_id(self, web_entry: Dict[str, Any]) -> str:
        """Generate a unique ID for the entry."""
        facility_name = web_entry.get('facility_name', 'unknown')
        date = web_entry.get('date', datetime.now())
        
        # Create a hash-based ID
        id_string = f"{facility_name}_{date.strftime('%Y%m%d')}"
        return id_string.replace(' ', '_').replace('/', '_').lower()
    
    def _extract_structured_data(self, web_entry: Dict[str, Any], pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure the key data points."""
        structured = {
            'facility_name': self._extract_facility_name(web_entry, pdf_data),
            'facility_address': pdf_data.get('facility_address', ''),
            'facility_license_number': pdf_data.get('facility_license_number', ''),
            'enforcement_date': self._format_date(web_entry.get('date')),
            'enforcement_action_type': self._extract_enforcement_type(web_entry, pdf_data),
            'penalty_amount': self._extract_penalty_amount(pdf_data),
            'violation_summary': self._extract_violation_summary(pdf_data),
            'key_violations': pdf_data.get('key_violations', []),
            'effective_date': pdf_data.get('effective_date', ''),
            'contact_information': pdf_data.get('contact_information', ''),
            'pdf_url': web_entry.get('pdf_url', ''),
            'severity_level': self._assess_severity(web_entry, pdf_data),
            'priority_score': self._calculate_priority_score(web_entry, pdf_data)
        }
        
        return structured
    
    def _extract_facility_name(self, web_entry: Dict[str, Any], pdf_data: Dict[str, Any]) -> str:
        """Extract the most accurate facility name."""
        web_name = web_entry.get('facility_name', '')
        pdf_name = pdf_data.get('facility_name', '')
        
        # Prefer PDF name if it's more complete, otherwise use web name
        if pdf_name and len(pdf_name) > len(web_name):
            return pdf_name
        return web_name or pdf_name
    
    def _extract_enforcement_type(self, web_entry: Dict[str, Any], pdf_data: Dict[str, Any]) -> str:
        """Extract the enforcement action type."""
        web_action = web_entry.get('enforcement_action', '')
        pdf_action = pdf_data.get('enforcement_action_type', '')
        
        # Prefer PDF action if available, otherwise use web action
        if pdf_action:
            return pdf_action
        return web_action
    
    def _extract_penalty_amount(self, pdf_data: Dict[str, Any]) -> str:
        """Extract and format penalty amount."""
        penalty = pdf_data.get('penalty_amount', '')
        if penalty:
            # Clean up the penalty amount
            penalty = re.sub(r'[^\d,]', '', penalty)
            if penalty:
                return f"${penalty}"
        return penalty
    
    def _extract_violation_summary(self, pdf_data: Dict[str, Any]) -> str:
        """Extract a summary of violations."""
        violation_details = pdf_data.get('violation_details', '')
        key_violations = pdf_data.get('key_violations', [])
        
        if key_violations:
            # Use key violations as summary
            return '; '.join(key_violations[:3])  # First 3 violations
        elif violation_details:
            # Truncate violation details
            return violation_details[:500] + '...' if len(violation_details) > 500 else violation_details
        
        return ''
    
    def _assess_severity(self, web_entry: Dict[str, Any], pdf_data: Dict[str, Any]) -> str:
        """Assess the severity level of the enforcement action."""
        action_type = self._extract_enforcement_type(web_entry, pdf_data).lower()
        penalty_amount = self._extract_penalty_amount(pdf_data)
        
        # High severity indicators
        if any(keyword in action_type for keyword in ['revocation', 'suspension', 'cease']):
            return 'HIGH'
        
        # Check penalty amount
        if penalty_amount:
            try:
                amount = float(re.sub(r'[^\d.]', '', penalty_amount))
                if amount >= 10000:
                    return 'HIGH'
                elif amount >= 1000:
                    return 'MEDIUM'
            except ValueError:
                pass
        
        # Medium severity indicators
        if any(keyword in action_type for keyword in ['curtailment', 'penalties']):
            return 'MEDIUM'
        
        return 'LOW'
    
    def _calculate_priority_score(self, web_entry: Dict[str, Any], pdf_data: Dict[str, Any]) -> int:
        """Calculate a priority score for the entry (0-100)."""
        score = 0
        
        # Base score by action type
        action_type = self._extract_enforcement_type(web_entry, pdf_data).lower()
        if 'revocation' in action_type or 'suspension' in action_type:
            score += 40
        elif 'cease' in action_type:
            score += 30
        elif 'curtailment' in action_type:
            score += 20
        elif 'penalties' in action_type:
            score += 15
        
        # Penalty amount bonus
        penalty_amount = self._extract_penalty_amount(pdf_data)
        if penalty_amount:
            try:
                amount = float(re.sub(r'[^\d.]', '', penalty_amount))
                if amount >= 50000:
                    score += 30
                elif amount >= 10000:
                    score += 20
                elif amount >= 1000:
                    score += 10
            except ValueError:
                pass
        
        # Number of violations bonus
        key_violations = pdf_data.get('key_violations', [])
        if len(key_violations) >= 5:
            score += 15
        elif len(key_violations) >= 3:
            score += 10
        elif len(key_violations) >= 1:
            score += 5
        
        # Recent date bonus
        entry_date = web_entry.get('date')
        if entry_date:
            days_old = (datetime.now() - entry_date).days
            if days_old <= 1:
                score += 10
            elif days_old <= 7:
                score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _format_date(self, date_obj) -> str:
        """Format date object to string."""
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d')
        elif isinstance(date_obj, str):
            # If it's already a string, try to parse and reformat it
            try:
                if '/' in date_obj:
                    # Handle MM/DD/YYYY format
                    parsed = datetime.strptime(date_obj, '%m/%d/%Y')
                    return parsed.strftime('%Y-%m-%d')
                return date_obj
            except ValueError:
                return date_obj
        return ''
    
    def _validate_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the processed data."""
        errors = []
        warnings = []
        
        structured = processed_data.get('structured_data', {})
        
        # Required fields validation
        if not structured.get('facility_name'):
            errors.append('Missing facility name')
        
        if not structured.get('enforcement_action_type'):
            warnings.append('Missing enforcement action type')
        
        if not structured.get('enforcement_date'):
            warnings.append('Missing enforcement date')
        
        # Data quality checks
        if structured.get('penalty_amount') and not re.match(r'^\$?[\d,]+$', structured['penalty_amount']):
            warnings.append('Penalty amount format may be incorrect')
        
        if structured.get('facility_license_number') and len(structured['facility_license_number']) < 3:
            warnings.append('License number seems too short')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'completeness_score': self._calculate_completeness_score(structured)
        }
    
    def _calculate_completeness_score(self, structured: Dict[str, Any]) -> float:
        """Calculate a completeness score for the data (0-100)."""
        required_fields = [
            'facility_name', 'enforcement_action_type', 'enforcement_date'
        ]
        
        optional_fields = [
            'facility_address', 'facility_license_number', 'penalty_amount',
            'violation_summary', 'key_violations', 'effective_date'
        ]
        
        required_score = sum(1 for field in required_fields if structured.get(field)) / len(required_fields) * 60
        optional_score = sum(1 for field in optional_fields if structured.get(field)) / len(optional_fields) * 40
        
        return round(required_score + optional_score, 1)
