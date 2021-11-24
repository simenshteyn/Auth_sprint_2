from gevent import monkey

monkey.patch_all()

from gevent.pywsgi import WSGIServer  # noqa: E402

from db.pg import db  # noqa: E402
from main import create_app  # noqa: E402

if __name__ == '__main__':
    app = create_app()
    db.init_app(app)

    http_server = WSGIServer(('', 8000), app)
    http_server.serve_forever()
