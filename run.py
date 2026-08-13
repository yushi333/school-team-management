import os
import sys

print(">>> 正在加载，请稍候...", flush=True)

from app import create_app

if '--prod' in sys.argv:
    # Production mode: always use ProdConfig so the scheduler starts
    config_name = 'production'
else:
    config_name = os.environ.get('FLASK_ENV', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    if '--prod' in sys.argv:
        # Production mode with waitress (multi-threaded, stable)
        from waitress import serve
        port = int(os.environ.get('PORT', 5000))
        print(f">>> [生产模式] waitress 服务器启动: http://0.0.0.0:{port}", flush=True)
        serve(app, host='0.0.0.0', port=port, threads=4)
    else:
        # Dev mode
        port = int(os.environ.get('PORT', 5000))
        print(f">>> [开发模式] 服务器启动: http://localhost:{port}", flush=True)
        app.run(debug=True, host='0.0.0.0', port=port)
