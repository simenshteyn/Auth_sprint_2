from flask import Blueprint

from api.v1.routes import v1

api = Blueprint('api', __name__, url_prefix='/api')

api.register_blueprint(v1)
