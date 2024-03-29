from api.v1.oauth.routes import oauth
from api.v1.permission.routes import permission
from api.v1.role.routes import role
from api.v1.user.routes import user
from flask import Blueprint, jsonify

v1 = Blueprint('v1', __name__, url_prefix='/v1')
v1.register_blueprint(user)
v1.register_blueprint(role)
v1.register_blueprint(permission)
v1.register_blueprint(oauth)


@v1.route('/')
def index():
    return jsonify(result="Hello, World!")
