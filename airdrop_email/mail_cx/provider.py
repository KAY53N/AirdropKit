"""
mail.cx temporary email provider implementation

Based on the mail.cx API structure where:
1. You generate a random email address
2. Use the API to check for emails at that address
"""

import time
import random
import string
from typing import List, Optional
from datetime import datetime
from urllib.parse import unquote, quote
import requests
import re

from ..base import BaseEmailProvider, EmailMessage


class MailCxProvider(BaseEmailProvider):
    """mail.cx temporary email service provider"""

    MAIL_CX_URL = "https://mail.cx/zh/"
    MAIL_CX_API_BASE = "https://mail.cx/api/api/v1/mailbox"
    MAIL_HOSTS = ["qabq.com", "nqmo.com", "end.tw", "uuf.me", "6n9.net"]

    def __init__(self, email: Optional[str] = None, **kwargs):
        """
        Initialize mail.cx provider

        Args:
            email: Optional email address (will be generated if not provided)
            **kwargs: Additional configuration
                - auto_create: Automatically create new email (default: True)
                - timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(email or "", None, **kwargs)
        self.auth_token = None
        self.session = requests.Session()
        self.timeout = kwargs.get('timeout', 30)
        self.registration_time = None  # 用于过滤邮件
        self._setup_headers()

    def _setup_headers(self):
        """Setup default headers for requests"""
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'origin': 'https://mail.cx',
            'referer': 'https://mail.cx/zh/'
        })

    def get_auth_token(self) -> Optional[str]:
        """
        Get auth_token from mail.cx for API requests

        Returns:
            str: Decoded auth_token, or None if failed
        """
        try:
            print(f"🔑 Requesting auth_token from mail.cx...")

            # 如果已经有邮箱地址，设置 mtd_address cookie
            if self.email:
                self.session.cookies.set('mtd_address', quote(self.email))

            response = self.session.get(
                self.MAIL_CX_URL,
                timeout=self.timeout
            )

            if 'auth_token' in response.cookies:
                raw_token = response.cookies['auth_token']
                decoded_token = unquote(raw_token).strip().strip('"').strip("'").strip()
                print(f"✅ Got auth_token: {decoded_token[:20]}...")
                return decoded_token
            else:
                print(f"❌ No auth_token in response. Available cookies: {list(response.cookies.keys())}")
                return None
        except Exception as e:
            print(f"❌ Failed to get auth_token: {e}")
            return None

    def generate_random_email(self) -> str:
        """
        Generate a random temporary email address

        Returns:
            str: Generated email address
        """
        username_length = random.randint(6, 10)
        username = ''.join(random.choices(string.ascii_lowercase, k=username_length))
        domain = random.choice(self.MAIL_HOSTS)
        email = f"{username}@{domain}"
        print(f"📧 Generated random email: {email}")
        return email

    def create_email(self) -> Optional[str]:
        """
        Create (generate) a new temporary email address

        Returns:
            str: Generated email address
        """
        self.email = self.generate_random_email()
        self.registration_time = int(time.time() * 1000)  # 毫秒时间戳
        return self.email

    def connect(self) -> bool:
        """
        Connect to mail.cx service

        Returns:
            bool: True if connection successful
        """
        # 获取 auth_token
        self.auth_token = self.get_auth_token()
        if not self.auth_token:
            return False

        # 如果没有邮箱地址或需要自动创建，生成新邮箱
        if not self.email or self.config.get('auto_create', True):
            self.create_email()

        return True

    def disconnect(self):
        """Disconnect from mail.cx service"""
        if self.session:
            self.session.close()

    def get_messages(
        self,
        folder: str = 'INBOX',
        limit: int = 10,
        unread_only: bool = False,
        since: Optional[datetime] = None
    ) -> List[EmailMessage]:
        """
        Retrieve email messages from mail.cx

        Args:
            folder: Not used for mail.cx (kept for interface compatibility)
            limit: Maximum number of messages to retrieve
            unread_only: Not used for mail.cx (kept for interface compatibility)
            since: Only retrieve messages after this datetime

        Returns:
            List of EmailMessage objects
        """
        if not self.auth_token:
            print("❌ Not connected. Call connect() first.")
            return []

        if not self.email:
            print("❌ No email address. Call connect() first.")
            return []

        try:
            print(f"📬 Fetching messages for {self.email}...")

            # 更新 headers 以包含 authorization
            headers = {
                'authorization': f'bearer {self.auth_token}',
                'referer': 'https://mail.cx/zh/',
            }

            response = self.session.get(
                f"{self.MAIL_CX_API_BASE}/{self.email}",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code != 200:
                print(f"❌ Failed to fetch messages: {response.status_code}")
                return []

            data = response.json()
            messages = []

            # 转换时间戳（如果提供）
            since_millis = None
            if since:
                since_millis = int(since.timestamp() * 1000)
            elif self.registration_time:
                since_millis = self.registration_time

            for msg_data in data[:limit]:
                # 过滤时间
                msg_time = msg_data.get('posix-millis', 0)
                if since_millis and msg_time <= since_millis:
                    continue

                # 解析时间
                received_at = None
                if msg_time:
                    try:
                        received_at = datetime.fromtimestamp(msg_time / 1000)
                    except:
                        pass

                message = EmailMessage(
                    id=msg_data.get('id', ''),
                    subject=msg_data.get('subject', ''),
                    sender=msg_data.get('from', {}).get('address', '') if isinstance(msg_data.get('from'), dict) else str(msg_data.get('from', '')),
                    recipient=self.email,
                    body_text=msg_data.get('text', ''),
                    body_html=msg_data.get('html', ''),
                    received_at=received_at,
                    headers=msg_data.get('headers', {})
                )
                messages.append(message)

            print(f"✅ Retrieved {len(messages)} messages")
            return messages

        except Exception as e:
            print(f"❌ Failed to fetch messages: {e}")
            import traceback
            traceback.print_exc()
            return []

    def wait_for_message(
        self,
        timeout: int = 300,
        interval: int = 5,
        filter_subject: Optional[str] = None,
        filter_sender: Optional[str] = None
    ) -> Optional[EmailMessage]:
        """
        Wait for a new message to arrive

        Args:
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds
            filter_subject: Only return message with matching subject (substring match)
            filter_sender: Only return message from matching sender (substring match)

        Returns:
            EmailMessage if found, None if timeout
        """
        print(f"⏳ Waiting for message (timeout: {timeout}s, interval: {interval}s)...")
        start_time = time.time()
        seen_ids = set()

        # 记录开始等待的时间
        wait_start_millis = int(time.time() * 1000)

        while time.time() - start_time < timeout:
            time.sleep(interval)

            messages = self.get_messages(limit=20)

            for msg in messages:
                # 跳过已见过的消息
                if msg.id in seen_ids:
                    continue

                seen_ids.add(msg.id)

                # 检查时间（只看等待开始后的邮件）
                if msg.received_at:
                    msg_millis = int(msg.received_at.timestamp() * 1000)
                    if msg_millis < wait_start_millis:
                        continue

                # 检查过滤条件
                if filter_subject and filter_subject.lower() not in msg.subject.lower():
                    continue

                if filter_sender and filter_sender.lower() not in msg.sender.lower():
                    continue

                print(f"✅ New message received: {msg.subject}")
                return msg

            elapsed = int(time.time() - start_time)
            print(f"⏳ Still waiting... ({elapsed}/{timeout}s)")

        print(f"⌛ Timeout reached, no matching message found")
        return None

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
        mail.cx is receive-only, sending is not supported

        Returns:
            bool: Always False
        """
        print("❌ mail.cx does not support sending emails")
        return False

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message from mail.cx

        Args:
            message_id: Message ID to delete

        Returns:
            bool: True if deleted successfully
        """
        if not self.auth_token or not self.email:
            print("❌ Not connected. Call connect() first.")
            return False

        try:
            headers = {
                'authorization': f'bearer {self.auth_token}',
            }

            response = self.session.delete(
                f"{self.MAIL_CX_API_BASE}/{self.email}/{message_id}",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                print(f"✅ Message {message_id} deleted")
                return True
            else:
                print(f"❌ Failed to delete message: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed to delete message: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """
        mail.cx doesn't have read/unread status

        Returns:
            bool: Always True
        """
        return True
