"""CLI management script for the school team management system.

Usage:
    python manage.py init          # Initialize database + seed admin
    python manage.py seed          # Seed sample data
    python manage.py scrape        # Trigger a full scrape (for testing)
    python manage.py scrape <uid>  # Scrape a single user
    python manage.py ranking       # Recompute rankings
    python manage.py run           # Start the dev server
"""

import os
import sys

print(">>> 正在加载...", flush=True)

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_init():
    """Initialize database tables."""
    print(">>> 正在初始化数据库...", flush=True)
    from app import create_app
    from app.database import init_db
    app = create_app('development')
    with app.app_context():
        # init_db is already called in create_app, so tables exist
        print("[OK] Database tables created.", flush=True)


def cmd_seed():
    """Seed sample data."""
    print(">>> 正在导入模块...", flush=True)
    import seed
    seed.init_db()
    print("[DONE] Database seeded successfully!")


def cmd_scrape(user_id=None):
    """Run the scraper."""
    print(">>> 正在加载爬虫...", flush=True)
    from app import create_app
    from app.scraper.orchestrator import scrape_all, scrape_all_users, scrape_single_user, scrape_contests
    app = create_app('development')
    with app.app_context():
        if user_id:
            scrape_single_user(int(user_id))
        else:
            scrape_all_users()
            scrape_contests()
    print("[DONE] Scraping completed.")


def cmd_ranking():
    """Recompute rankings."""
    from app import create_app
    from app.models.registration import recompute_rankings
    app = create_app('development')
    with app.app_context():
        count = recompute_rankings()
        print(f"[DONE] Rankings recomputed for {count} users.")


def cmd_run():
    """Start development server."""
    print(">>> 正在启动服务器...", flush=True)
    from app import create_app
    app = create_app('development')
    print(">>> 服务器启动: http://localhost:5000", flush=True)
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == 'init':
        cmd_init()
    elif args[0] == 'seed':
        cmd_seed()
    elif args[0] == 'scrape':
        cmd_scrape(args[1] if len(args) > 1 else None)
    elif args[0] == 'ranking':
        cmd_ranking()
    elif args[0] == 'run':
        cmd_run()
    elif args[0] == 'setup':
        cmd_init()
        cmd_seed()
        print(">>> 初始化完成！运行 'python manage.py run' 启动服务器。", flush=True)
    else:
        print(f"Unknown command: {args[0]}")
        print(__doc__)
