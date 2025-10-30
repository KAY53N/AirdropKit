"""
Base provider interface for email services
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailMessage:
    """Email message data structure"""
    id: str
    subject: str
    sender: str
    recipient: str
    body_text: str
    body_html: Optional[str] = None
    received_at: Optional[datetime] = None
    headers: Optional[Dict[str, str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class BaseEmailProvider(ABC):
    """Base class for all email providers"""

    def __init__(self, email: str, password: Optional[str] = None, **kwargs):
        """
        Initialize email provider

        Args:
            email: Email address
            password: Email password (not needed for temporary email services)
            **kwargs: Additional provider-specific parameters
        """
        self.email = email
        self.password = password
        self.config = kwargs

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to email service

        Returns:
            bool: True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from email service"""
        pass

    @abstractmethod
    def get_messages(
        self,
        folder: str = 'INBOX',
        limit: int = 10,
        unread_only: bool = False,
        since: Optional[datetime] = None
    ) -> List[EmailMessage]:
        """
        Retrieve email messages

        Args:
            folder: Email folder/label to check
            limit: Maximum number of messages to retrieve
            unread_only: Only retrieve unread messages
            since: Only retrieve messages received after this datetime

        Returns:
            List of EmailMessage objects
        """
        pass

    @abstractmethod
    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email message

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            body_html: HTML email body (optional)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach

        Returns:
            bool: True if sent successfully
        """
        pass

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """
        Delete an email message

        Args:
            message_id: Message ID to delete

        Returns:
            bool: True if deleted successfully
        """
        pass

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark message as read

        Args:
            message_id: Message ID to mark as read

        Returns:
            bool: True if marked successfully
        """
        pass

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
