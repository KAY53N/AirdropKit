"""
Email module for AirdropKit

Supports mail.cx temporary email service
"""

from .client import EmailClient
from .providers import MailCxProvider
from .verifier import CodeExtractor
from .base import EmailMessage

__all__ = [
    'EmailClient',
    'EmailMessage',
    'MailCxProvider',
    'CodeExtractor',
]
