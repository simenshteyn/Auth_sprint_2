from flask import Blueprint, jsonify

from api.v1.permission.routes import permission
from api.v1.role.routes import role
from api.v1.user.routes import user

v1 = Blueprint('v1', __name__, url_prefix='/v1')
v1.register_blueprint(user)
v1.register_blueprint(role)
v1.register_blueprint(permission)


@v1.route('/')
def index():
    return jsonify(result="Hello, World!")
