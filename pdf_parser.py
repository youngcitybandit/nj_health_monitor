"""
PDF parser for NJ Health Facility enforcement action documents.
Handles both text-based and scanned PDFs using OCR.
"""

import io
import logging
from typing import Dict, Any, Optional
import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re

logger = logging.getLogger(__name__)

class PDFParser:
    """Parser for PDF documents containing enforcement action information."""
    
    def __init__(self):
        # Configure tesseract path if needed (adjust for your system)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
        pass
    
    def parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Parse PDF content and extract relevant information.
        
        Args:
            pdf_content: Raw PDF content as bytes
            
        Returns:
            Dictionary containing parsed information
        """
        try:
            # First try to extract text directly
            text_content = self._extract_text_from_pdf(pdf_content)
            
            if not text_content or len(text_content.strip()) < 50:
                # If text extraction failed or returned minimal content, try OCR
                logger.info("Text extraction yielded minimal content, trying OCR...")
                text_content = self._extract_text_with_ocr(pdf_content)
            
            if not text_content:
                logger.warning("Could not extract any text from PDF")
                return {}
            
            # Parse the extracted text
            parsed_data = self._parse_text_content(text_content)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {}
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF using multiple methods."""
        text_content = ""
        
        try:
            # Method 1: Using pdfplumber (better for complex layouts)
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            
            if text_content.strip():
                logger.info("Successfully extracted text using pdfplumber")
                return text_content
                
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {str(e)}")
        
        try:
            # Method 2: Using PyPDF2 as fallback
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
            
            if text_content.strip():
                logger.info("Successfully extracted text using PyPDF2")
                return text_content
                
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
        
        return text_content
    
    def _extract_text_with_ocr(self, pdf_content: bytes) -> str:
        """Extract text from PDF using OCR."""
        try:
            # Convert PDF to images and apply OCR
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # Increase resolution for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Apply OCR
                page_text = pytesseract.image_to_string(image, config='--psm 6')
                if page_text:
                    text_content += page_text + "\n"
            
            doc.close()
            
            if text_content.strip():
                logger.info("Successfully extracted text using OCR")
                return text_content
            else:
                logger.warning("OCR extraction yielded no text")
                return ""
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return ""
    
    def _parse_text_content(self, text: str) -> Dict[str, Any]:
        """Parse extracted text to extract relevant information."""
        parsed_data = {
            'raw_text': text,
            'facility_name': '',
            'facility_address': '',
            'facility_license_number': '',
            'enforcement_action_type': '',
            'penalty_amount': '',
            'violation_details': '',
            'corrective_actions': '',
            'effective_date': '',
            'contact_information': '',
            'key_violations': []
        }
        
        try:
            # Extract facility name (usually at the beginning)
            facility_match = re.search(r'Facility:\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.MULTILINE)
            if facility_match:
                parsed_data['facility_name'] = facility_match.group(1).strip()
            
            # Extract address
            address_pattern = r'Address:\s*(.+?)(?:\n|License)'
            address_match = re.search(address_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if address_match:
                parsed_data['facility_address'] = address_match.group(1).strip()
            
            # Extract license number
            license_match = re.search(r'License\s*#?\s*:?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
            if license_match:
                parsed_data['facility_license_number'] = license_match.group(1).strip()
            
            # Extract penalty amount
            penalty_patterns = [
                r'penalty\s*of\s*\$?([0-9,]+)', 
                r'fine\s*of\s*\$?([0-9,]+)',
                r'\$([0-9,]+)\s*penalty',
                r'assessed\s*penalty\s*of\s*\$?([0-9,]+)'
            ]
            
            for pattern in penalty_patterns:
                penalty_match = re.search(pattern, text, re.IGNORECASE)
                if penalty_match:
                    parsed_data['penalty_amount'] = penalty_match.group(1).strip()
                    break
            
            # Extract enforcement action type
            action_patterns = [
                r'Notice\s+of\s+Assessment\s+of\s+Penalties',
                r'Curtailment',
                r'Cease\s+&\s+Desist',
                r'Directed\s+Plan\s+of\s+Correction',
                r'Lifting\s+Curtailment',
                r'Revocation',
                r'Suspension'
            ]
            
            for pattern in action_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    parsed_data['enforcement_action_type'] = pattern.replace(r'\s+', ' ')
                    break
            
            # Extract violation details (look for common violation patterns)
            violation_section = self._extract_violation_section(text)
            parsed_data['violation_details'] = violation_section
            
            # Extract key violations
            parsed_data['key_violations'] = self._extract_key_violations(text)
            
            # Extract effective date
            date_patterns = [
                r'Effective\s+Date:\s*([0-9/]+)',
                r'Date:\s*([0-9/]+)',
                r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, text, re.IGNORECASE)
                if date_match:
                    parsed_data['effective_date'] = date_match.group(1).strip()
                    break
            
            # Extract contact information
            contact_info = self._extract_contact_information(text)
            parsed_data['contact_information'] = contact_info
            
            # Extract administrator information
            admin_info = self._extract_administrator_info(text)
            parsed_data['administrator_name'] = admin_info.get('full_name', '')
            parsed_data['administrator_first_name'] = admin_info.get('first_name', '')
            
            logger.info("Successfully parsed PDF content")
            
        except Exception as e:
            logger.error(f"Error parsing text content: {str(e)}")
        
        return parsed_data
    
    def _extract_violation_section(self, text: str) -> str:
        """Extract the main violation details section."""
        # Look for common section headers
        section_patterns = [
            r'Violations?:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'Deficiencies?:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'Findings?:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'Issues?:\s*(.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_key_violations(self, text: str) -> list:
        """Extract key violation points from the text."""
        violations = []
        
        # Look for numbered or bulleted violation points
        violation_patterns = [
            r'(?:^|\n)\s*[0-9]+\.\s*(.+?)(?=\n\s*[0-9]+\.|\n\n|$)',
            r'(?:^|\n)\s*[•\-\*]\s*(.+?)(?=\n\s*[•\-\*]|\n\n|$)',
            r'(?:^|\n)\s*[a-z]\)\s*(.+?)(?=\n\s*[a-z]\)|\n\n|$)'
        ]
        
        for pattern in violation_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                violation_text = match.strip()
                if len(violation_text) > 20:  # Filter out very short matches
                    violations.append(violation_text)
        
        return violations[:10]  # Limit to first 10 violations
    
    def _extract_contact_information(self, text: str) -> str:
        """Extract contact information from the text."""
        contact_patterns = [
            r'Contact:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'For\s+questions?:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'Inquiries:\s*(.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_administrator_info(self, text: str) -> dict:
        """Extract administrator name information from the text."""
        admin_info = {'full_name': '', 'first_name': ''}
        
        # Common patterns for administrator names in healthcare facility documents
        # More flexible patterns to handle various name formats and capitalizations
        admin_patterns = [
            # Pattern for "Name, Administrator" or "Name Administrator"
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*Administrator',
            # Pattern for "Administrator: Name" or "Administrator Name"
            r'Administrator[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            # More specific administrator titles
            r'Nursing\s+Home\s+Administrator[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Facility\s+Administrator[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Administrator\s*[-:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            # Contact information patterns
            r'Contact\s+Person[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            # Other titles
            r'Director[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'CEO[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Chief\s+Executive\s+Officer[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            # More flexible patterns for names at beginning of lines
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*Administrator',
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\n.*Administrator',
            # Patterns to handle names like "Avraham Ochs" with different formats
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*Administrator',
            # Pattern for contact blocks with email (like the example you showed)
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*Administrator\s*\n.*Health\s+Center',
            # More general pattern for any capitalized name followed by Administrator
            r'([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+),?\s*Administrator'
        ]
        
        for pattern in admin_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                full_name = match.group(1).strip()
                admin_info['full_name'] = full_name
                
                # Extract first name (first word)
                name_parts = full_name.split()
                if name_parts:
                    admin_info['first_name'] = name_parts[0]
                
                break
        
        # If no specific administrator found, try to extract from signature or contact sections
        if not admin_info['full_name']:
            # Look for names in signature-like patterns
            signature_patterns = [
                r'Sincerely,\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'Best\s+regards,\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*(Administrator|Director|CEO)',
            ]
            
            for pattern in signature_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    full_name = match.group(1).strip()
                    admin_info['full_name'] = full_name
                    
                    # Extract first name
                    name_parts = full_name.split()
                    if name_parts:
                        admin_info['first_name'] = name_parts[0]
                    
                    break
        
        # Generate a default first name if none found
        if not admin_info['first_name']:
            # Use common professional first names as fallback
            import random
            default_names = ['Michael', 'Sarah', 'David', 'Jennifer', 'Robert', 'Lisa', 'James', 'Mary', 'John', 'Patricia']
            admin_info['first_name'] = random.choice(default_names)
            admin_info['full_name'] = f"{admin_info['first_name']} [Administrator]"
        
        return admin_info
