"""
Email providers module - exports all available email providers
"""

from .mail_cx import MailCxProvider

__all__ = [
    'MailCxProvider',
]
