"""Database initialization and seed data script.

Usage:
    python seed.py          # Initialize DB and seed admin account
"""

import os
import sys


# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.user import User
from app.models.platform import set_handle
from app.models.content import create_tutorial


def init_db():
    app = create_app('development')
    with app.app_context():
        # Tables are auto-created by database.init_db()

        # Seed admin user
        admin = User.find_by_username('admin')
        if not admin:
            admin = User.create(
                username='admin',
                password='admin123',
                role='admin',
                real_name='系统管理员',
                grade='',
            )
            print("[Seed] Admin user created: admin / admin123")
        else:
            print("[Seed] Admin user already exists.")
        admin_id = admin.id

        # Seed test members
        test_users = [
            {'username': 'zhangsan', 'password': '123456', 'real_name': '张三', 'grade': '2026级'},
            {'username': 'lisi', 'password': '123456', 'real_name': '李四', 'grade': '2025级'},
            {'username': 'wangwu', 'password': '123456', 'real_name': '王五', 'grade': '2026级'},
        ]
        member_ids = {}
        for tu in test_users:
            existing = User.find_by_username(tu['username'])
            if not existing:
                user_obj = User.create(
                    username=tu['username'],
                    password=tu['password'],
                    role='member',
                    real_name=tu['real_name'],
                    grade=tu['grade'],
                )
                member_ids[tu['username']] = user_obj.id
                print(f"[Seed] Test user created: {tu['username']} / {tu['password']}")
            else:
                member_ids[tu['username']] = existing.id

        # Add sample platform handles for test users
        from app.models.platform import get_handles
        sample_handles = {
            'zhangsan': {'luogu': '123456', 'codeforces': 'tourist'},
            'lisi': {'atcoder': 'chokudai', 'codeforces': 'Petr'},
            'wangwu': {'luogu': '789012', 'nowcoder': '12345'},
        }
        for username, handles in sample_handles.items():
            uid = member_ids.get(username)
            if uid:
                existing_handles = {h['platform']: h for h in get_handles(uid)}
                for platform, handle in handles.items():
                    if platform not in existing_handles:
                        set_handle(uid, platform, handle)
        print("[Seed] Sample platform handles added.")

        # Seed sample tutorials
        from app.models.content import get_tutorials
        if not get_tutorials():
            tutorials = [
                {
                    'title': '动态规划入门',
                    'description': '从斐波那契到背包问题，系统讲解动态规划的核心思想。',
                    'video_url': 'https://www.bilibili.com/video/example1',
                },
                {
                    'title': '图论基础 - DFS与BFS',
                    'description': '深度优先搜索和广度优先搜索的详细讲解与应用。',
                    'video_url': 'https://www.bilibili.com/video/example2',
                },
            ]
            for t in tutorials:
                create_tutorial(
                    t['title'], t['description'], t['video_url'], admin_id
                )
            print("[Seed] Sample tutorials added.")

        # Online contests are auto-scraped daily — no seed needed

        print("[Seed] Database initialization complete!")


if __name__ == '__main__':
    init_db()
