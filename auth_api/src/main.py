from flask_jwt_extended import JWTManager

from api.common import api
from core.commands import commands
from core.containers import Container
from core.settings import config
from db.pg import PG_URI, db


def create_app():
    container = Container()
    app = container.app()
    app.container = container
    app.config['SQLALCHEMY_DATABASE_URI'] = PG_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['OAUTH_CREDENTIALS'] = {
        'vk': {
            'id': config.oauth_vk_id,
            'secret': config.oauth_vk_secret
        }
    }
    db.init_app(app)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(commands)

    app.config['JWT_SECRET_KEY'] = config.jwt_secret_key
    JWTManager(app)

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(host="0.0.0.0", port=8000, debug=True)
