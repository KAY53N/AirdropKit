#!/usr/bin/env python3
"""
mail.cx 定时获取邮件测试
支持定时轮询邮箱，自动提取验证码
"""

import sys
import time
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from airdrop_email import EmailClient


def poll_emails(client, interval=5, max_polls=12):
    """
    定时轮询邮件

    Args:
        client: EmailClient 实例
        interval: 轮询间隔（秒），默认 5 秒
        max_polls: 最大轮询次数，默认 12 次（1 分钟）

    Returns:
        bool: 是否找到新邮件
    """
    print(f"\n⏰ 开始定时获取邮件（间隔: {interval}秒，最多: {max_polls}次）")
    print(f"   邮箱地址: {client.email}")
    print(f"   你可以向这个地址发送测试邮件")
    print(f"   按 Ctrl+C 可以随时停止\n")

    seen_ids = set()

    for poll_count in range(1, max_polls + 1):
        try:
            print(f"[轮询 {poll_count}/{max_polls}] 检查新邮件...")

            # 获取邮件
            messages = client.get_messages(limit=10)

            # 检查新邮件
            new_messages = [msg for msg in messages if msg.id not in seen_ids]

            if new_messages:
                print(f"✅ 发现 {len(new_messages)} 封新邮件！\n")

                for i, msg in enumerate(new_messages, 1):
                    print(f"📧 新邮件 {i}:")
                    print(f"   主题: {msg.subject}")
                    print(f"   发件人: {msg.sender}")
                    print(f"   时间: {msg.received_at}")

                    # 提取验证码
                    code = EmailClient.extract_code(msg)
                    if code:
                        print(f"   🔑 验证码: {code}")

                    # 提取链接
                    link = EmailClient.extract_link(msg, keyword='verify')
                    if link:
                        print(f"   🔗 验证链接: {link[:80]}...")

                    # 显示邮件预览
                    if msg.body_text:
                        preview = msg.body_text[:150].replace('\n', ' ')
                        print(f"   预览: {preview}...")

                    print()

                    # 标记为已见
                    seen_ids.add(msg.id)

                return True
            else:
                # 更新已见邮件
                for msg in messages:
                    seen_ids.add(msg.id)

                print(f"   暂无新邮件（已有 {len(messages)} 封）")

            # 如果不是最后一次轮询，等待
            if poll_count < max_polls:
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
            return False
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            if poll_count < max_polls:
                time.sleep(interval)

    print(f"\n⌛ 已完成 {max_polls} 次轮询，未发现新邮件")
    return False


def test_with_polling():
    """测试定时获取邮件功能"""
    print("=" * 60)
    print("mail.cx 定时获取邮件测试")
    print("=" * 60)

    # 创建临时邮箱
    print("\n[1] 创建临时邮箱...")
    client = EmailClient.create_temp_email()

    if not client.connect():
        print("❌ 连接失败")
        return False

    print(f"✅ 成功创建邮箱: {client.email}")
    print(f"   注册时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 显示现有邮件
    print("\n[2] 检查现有邮件...")
    existing_messages = client.get_messages(limit=5)
    if existing_messages:
        print(f"   找到 {len(existing_messages)} 封历史邮件")
        for i, msg in enumerate(existing_messages, 1):
            print(f"   {i}. {msg.subject} ({msg.sender})")
    else:
        print("   📭 邮箱为空")

    # 定时轮询新邮件
    print("\n[3] 定时轮询新邮件...")
    found = poll_emails(client, interval=5, max_polls=12)

    # 清理
    client.disconnect()

    print("\n" + "=" * 60)
    if found:
        print("✅ 测试完成！成功接收到新邮件")
    else:
        print("✅ 测试完成！邮件系统工作正常")
    print("=" * 60)
    return True


def test_wait_for_specific():
    """测试等待特定邮件（带验证码）"""
    print("=" * 60)
    print("mail.cx 等待验证邮件测试")
    print("=" * 60)

    # 创建临时邮箱
    print("\n[1] 创建临时邮箱...")
    client = EmailClient.create_temp_email()

    if not client.connect():
        print("❌ 连接失败")
        return False

    print(f"✅ 成功创建邮箱: {client.email}")

    # 等待验证邮件
    print("\n[2] 等待验证邮件...")
    print("   提示：可以向这个邮箱发送包含 'verify' 或 'verification' 的邮件")
    print("   按 Ctrl+C 可以随时停止\n")

    try:
        message = client.wait_for_message(
            timeout=60,           # 等待 60 秒
            interval=5,           # 每 5 秒检查一次
            filter_subject=None   # 不过滤主题，接收所有新邮件
        )

        if message:
            print(f"\n✅ 收到新邮件！")
            print(f"   主题: {message.subject}")
            print(f"   发件人: {message.sender}")

            # 提取验证码
            code = EmailClient.extract_code(message)
            if code:
                print(f"   🔑 验证码: {code}")
            else:
                print(f"   ℹ️  未找到验证码")

            # 提取链接
            link = EmailClient.extract_link(message)
            if link:
                print(f"   🔗 链接: {link}")
        else:
            print(f"\n⌛ 超时：60 秒内未收到新邮件")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")

    # 清理
    client.disconnect()

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    return True


def show_menu():
    """显示菜单"""
    print("\n请选择测试模式：")
    print("1. 定时轮询模式（主动检查，默认 1 分钟）")
    print("2. 等待模式（等待新邮件，默认 60 秒）")
    print("3. 快速测试（仅检查当前邮件）")
    print("0. 退出")

    choice = input("\n请输入选项 (1/2/3/0): ").strip()
    return choice


def quick_test():
    """快速测试 - 仅检查当前邮件"""
    print("=" * 60)
    print("mail.cx 快速测试")
    print("=" * 60)

    client = EmailClient.create_temp_email()

    if not client.connect():
        print("❌ 连接失败")
        return False

    print(f"\n✅ 邮箱: {client.email}")

    messages = client.get_messages(limit=5)
    print(f"✅ 找到 {len(messages)} 封邮件")

    if messages:
        for i, msg in enumerate(messages, 1):
            print(f"\n邮件 {i}:")
            print(f"  主题: {msg.subject}")
            print(f"  发件人: {msg.sender}")

            code = EmailClient.extract_code(msg)
            if code:
                print(f"  验证码: {code}")

    client.disconnect()
    print(f"\n✅ 测试完成")
    return True


if __name__ == '__main__':
    try:
        while True:
            choice = show_menu()

            if choice == '1':
                test_with_polling()
                break
            elif choice == '2':
                test_wait_for_specific()
                break
            elif choice == '3':
                quick_test()
                break
            elif choice == '0':
                print("\n👋 再见！")
                sys.exit(0)
            else:
                print("\n❌ 无效选项，请重新选择")

    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
