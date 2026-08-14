import os
import threading
from flask import Flask
from config import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    from app.extensions import login_manager, csrf
    from app.database import init_db
    login_manager.init_app(app)
    csrf.init_app(app)
    init_db(app)

    # Set up user loader
    from app.models.user import load_user
    login_manager.user_loader(load_user)

    # Inject wuyu constants into all templates
    from app.constants import WUYU_TYPES, WUYU_LABELS

    @app.context_processor
    def inject_wuyu_constants():
        return {'WUYU_TYPES': WUYU_TYPES, 'WUYU_LABELS': WUYU_LABELS}

    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Error handlers
    register_error_handlers(app)

    # Scheduler (lazy init)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        _start_scheduler(app)

    return app


def register_error_handlers(app):
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def _start_scheduler(app):
    def _run():
        import time
        # Wait for app to fully start before initiating scheduler
        time.sleep(5)
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            scheduler = BackgroundScheduler(daemon=True)
            if not scheduler.get_job('scrape_job'):
                def job():
                    with app.app_context():
                        try:
                            from app.scraper.orchestrator import scrape_all
                            scrape_all()
                        except Exception as e:
                            print(f"[Scheduler] Error: {e}")
                from datetime import datetime
                scheduler.add_job(job, IntervalTrigger(hours=2), id='scrape_job', next_run_time=datetime.now())
                scheduler.start()
                print("[Scheduler] Started (every 2 hours)")
        except Exception as e:
            print(f"[Scheduler] Not available: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
