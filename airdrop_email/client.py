"""
High-level email client for easy usage
"""

from typing import Optional
from .base import EmailMessage
from .providers import MailCxProvider
from .verifier import CodeExtractor


class EmailClient:
    """
    High-level email client for mail.cx temporary email
    """

    @staticmethod
    def create_temp_email(**kwargs) -> MailCxProvider:
        """
        Create a temporary email using mail.cx

        Args:
            **kwargs: Additional configuration for MailCxProvider
                - auto_create: Automatically create new email (default: True)
                - timeout: Request timeout in seconds (default: 30)

        Returns:
            MailCxProvider instance

        Example:
            >>> client = EmailClient.create_temp_email()
            >>> client.connect()
            >>> print(f"Your temp email: {client.email}")
        """
        return MailCxProvider(**kwargs)

    @staticmethod
    def extract_code(message: EmailMessage, pattern: Optional[str] = None) -> Optional[str]:
        """
        Extract verification code from email message

        Args:
            message: EmailMessage object
            pattern: Custom regex pattern (optional)

        Returns:
            str: Extracted code, or None if not found

        Example:
            >>> messages = client.get_messages()
            >>> code = EmailClient.extract_code(messages[0])
            >>> print(f"Verification code: {code}")
        """
        return CodeExtractor.extract_code(message, pattern)

    @staticmethod
    def extract_link(message: EmailMessage, keyword: Optional[str] = None) -> Optional[str]:
        """
        Extract verification/confirmation link from email

        Args:
            message: EmailMessage object
            keyword: Keyword to filter links (optional)

        Returns:
            str: Extracted URL, or None if not found

        Example:
            >>> messages = client.get_messages()
            >>> link = EmailClient.extract_link(messages[0], keyword='verify')
            >>> print(f"Verification link: {link}")
        """
        return CodeExtractor.extract_link(message, keyword)
