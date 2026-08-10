"""Database initialization and seed data script.

Usage:
    python seed.py          # Initialize DB and seed admin account
"""

import os
import sys
from datetime import datetime

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.user import User
from app.models.platform import set_handle
from app.models.content import create_tutorial, create_online_contest


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

        # Seed sample online contests
        from app.models.content import get_online_contests
        if not get_online_contests():
            contests = [
                ('2026 ICPC Asia Regional Contest', 'codeforces',
                 'https://codeforces.com/contests', datetime(2026, 12, 15, 10, 0), datetime(2026, 12, 15, 15, 0),
                 'ICPC亚洲区域赛在线同步赛。'),
                ('Codeforces Round #1020 (Div. 2)', 'codeforces',
                 'https://codeforces.com/contests', datetime(2026, 8, 16, 14, 35), datetime(2026, 8, 16, 16, 35),
                 'Codeforces常规Div.2比赛。'),
                ('Codeforces Round #1021 (Div. 1 + Div. 2)', 'codeforces',
                 'https://codeforces.com/contests', datetime(2026, 8, 22, 14, 35), datetime(2026, 8, 22, 17, 5),
                 '联合Div.1+Div.2，题目质量高。'),
                ('AtCoder Beginner Contest 380', 'atcoder',
                 'https://atcoder.jp/contests', datetime(2026, 8, 17, 19, 0), datetime(2026, 8, 17, 20, 40),
                 'ABC系列，适合新手到进阶。'),
                ('AtCoder Regular Contest 175', 'atcoder',
                 'https://atcoder.jp/contests', datetime(2026, 8, 24, 20, 0), datetime(2026, 8, 24, 22, 0),
                 'ARC系列，难度较高。'),
                ('牛客练习赛150', 'nowcoder',
                 'https://ac.nowcoder.com/acm/contest/discuss', datetime(2026, 8, 15, 19, 0), datetime(2026, 8, 15, 21, 0),
                 '牛客平台常规练习赛。'),
                ('牛客寒假算法训练营', 'nowcoder',
                 'https://ac.nowcoder.com/acm/contest/discuss', datetime(2026, 12, 20, 9, 0), datetime(2026, 12, 25, 18, 0),
                 '为期一周的寒假集训营。'),
                ('洛谷月赛 2026年8月', 'luogu',
                 'https://www.luogu.com.cn/contest/list', datetime(2026, 8, 20, 14, 0), datetime(2026, 8, 20, 18, 0),
                 '洛谷每月一度的公开赛。'),
                ('洛谷月赛 2026年9月', 'luogu',
                 'https://www.luogu.com.cn/contest/list', datetime(2026, 9, 15, 14, 0), datetime(2026, 9, 15, 18, 0),
                 '洛谷九月公开赛，四道题。'),
            ]
            for c in contests:
                create_online_contest(*c, posted_by=admin_id)
            print(f"[Seed] {len(contests)} sample online contests added.")

        print("[Seed] Database initialization complete!")


if __name__ == '__main__':
    init_db()
