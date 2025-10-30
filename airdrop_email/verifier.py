"""
Verification code extractor for email messages
"""

import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .base import EmailMessage


class CodeExtractor:
    """Extract verification codes from email messages"""

    # Common verification code patterns
    PATTERNS = [
        # 6-digit codes
        r'\b(\d{6})\b',
        # 4-digit codes
        r'\b(\d{4})\b',
        # 8-digit codes
        r'\b(\d{8})\b',
        # Alphanumeric codes (6-8 characters)
        r'\b([A-Z0-9]{6,8})\b',
        # Common phrases with codes
        r'(?:code|verification code|verify code|confirmation code|otp|pin)[\s:：]*([A-Z0-9]{4,8})',
        r'(?:验证码|確認碼|驗證碼)[\s:：]*([A-Z0-9]{4,8})',
        # URL parameters
        r'[?&]code=([A-Z0-9]+)',
        r'[?&]token=([A-Z0-9]+)',
    ]

    @staticmethod
    def extract_code(
        message: EmailMessage,
        pattern: Optional[str] = None,
        use_html: bool = True
    ) -> Optional[str]:
        """
        Extract verification code from email message

        Args:
            message: EmailMessage object
            pattern: Custom regex pattern (if None, use default patterns)
            use_html: Try to extract from HTML body first (more accurate)

        Returns:
            str: Extracted code, or None if not found
        """
        text = message.body_text or ''

        # Try HTML body first if available
        if use_html and message.body_html:
            soup = BeautifulSoup(message.body_html, 'html.parser')
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            html_text = soup.get_text(separator=' ', strip=True)
            text = html_text + '\n' + text

        # Use custom pattern if provided
        if pattern:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
            return None

        # Try all default patterns
        for p in CodeExtractor.PATTERNS:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                # Validate code (avoid false positives like years)
                if CodeExtractor._is_valid_code(code):
                    return code

        return None

    @staticmethod
    def _is_valid_code(code: str) -> bool:
        """
        Validate if extracted string is likely a verification code

        Args:
            code: Extracted string

        Returns:
            bool: True if likely a verification code
        """
        # Skip common false positives
        false_positives = [
            '2024', '2023', '2022', '2021', '2020',  # Years
            '1234', '0000', '9999',  # Too simple
        ]

        if code in false_positives:
            return False

        # Must be 4-8 characters
        if len(code) < 4 or len(code) > 8:
            return False

        return True

    @staticmethod
    def extract_all_codes(
        message: EmailMessage,
        use_html: bool = True
    ) -> List[str]:
        """
        Extract all possible verification codes from email

        Args:
            message: EmailMessage object
            use_html: Try to extract from HTML body

        Returns:
            List of extracted codes
        """
        text = message.body_text or ''

        if use_html and message.body_html:
            soup = BeautifulSoup(message.body_html, 'html.parser')
            for script in soup(['script', 'style']):
                script.decompose()
            html_text = soup.get_text(separator=' ', strip=True)
            text = html_text + '\n' + text

        codes = []
        seen = set()

        for p in CodeExtractor.PATTERNS:
            matches = re.finditer(p, text, re.IGNORECASE)
            for match in matches:
                code = match.group(1)
                if code not in seen and CodeExtractor._is_valid_code(code):
                    codes.append(code)
                    seen.add(code)

        return codes

    @staticmethod
    def extract_link(
        message: EmailMessage,
        keyword: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract verification/confirmation link from email

        Args:
            message: EmailMessage object
            keyword: Keyword to filter links (e.g., 'verify', 'confirm')

        Returns:
            str: Extracted URL, or None if not found
        """
        # Pattern for URLs
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

        text = message.body_text or ''

        # Try HTML body for more accurate link extraction
        if message.body_html:
            soup = BeautifulSoup(message.body_html, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                link_text = link.get_text(strip=True)

                # Filter by keyword if provided
                if keyword:
                    if keyword.lower() in href.lower() or keyword.lower() in link_text.lower():
                        return href
                else:
                    # Return first http(s) link
                    if href.startswith(('http://', 'https://')):
                        return href

        # Fallback to regex on plain text
        matches = re.findall(url_pattern, text)
        for url in matches:
            if keyword:
                if keyword.lower() in url.lower():
                    return url
            else:
                return url

        return None

    @staticmethod
    def extract_info(message: EmailMessage) -> Dict[str, Any]:
        """
        Extract all useful information from email

        Args:
            message: EmailMessage object

        Returns:
            dict: Extracted information including codes, links, etc.
        """
        info = {
            'codes': CodeExtractor.extract_all_codes(message),
            'primary_code': CodeExtractor.extract_code(message),
            'links': [],
            'verification_link': None,
            'subject': message.subject,
            'sender': message.sender,
        }

        # Extract all links
        if message.body_html:
            soup = BeautifulSoup(message.body_html, 'html.parser')
            links = soup.find_all('a', href=True)
            info['links'] = [link['href'] for link in links if link['href'].startswith(('http://', 'https://'))]

        # Try to find verification link
        for keyword in ['verify', 'confirm', 'activate', 'validation', '验证', '確認']:
            link = CodeExtractor.extract_link(message, keyword)
            if link:
                info['verification_link'] = link
                break

        return info
