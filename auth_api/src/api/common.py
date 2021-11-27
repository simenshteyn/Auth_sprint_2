from api.v1.routes import v1
from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

api.register_blueprint(v1)
