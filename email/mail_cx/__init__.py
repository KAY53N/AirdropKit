"""
mail.cx temporary email provider

Simple temporary email service that generates random email addresses
and allows you to receive emails without registration.
"""

from .provider import MailCxProvider

__all__ = ['MailCxProvider']
