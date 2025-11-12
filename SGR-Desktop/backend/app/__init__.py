from flask import Flask
from flask_cors import CORS

from .config import (
    API_EXTERNA_BASE_URL,
    API_EXTERNA_HOST,
    API_EXTERNA_PORT,
    API_EXTERNA_PROTOCOL,
    API_TIMEOUT,
)
from .proxy import api_session  # noqa: F401  # garante inicialização da sessão
from .routes.analytics import analytics_bp
from .routes.avaliacoes import avaliacoes_bp
from .routes.cardapio import cardapio_bp
from .routes.pedidos import pedidos_bp
from .routes.system import system_bp


def register_blueprints(flask_app: Flask) -> None:
    flask_app.register_blueprint(cardapio_bp)
    flask_app.register_blueprint(pedidos_bp)
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(avaliacoes_bp)
    flask_app.register_blueprint(system_bp)


def create_app() -> Flask:
    flask_app = Flask(__name__)
    CORS(flask_app)

    flask_app.config['API_EXTERNA_BASE_URL'] = API_EXTERNA_BASE_URL
    flask_app.config['API_EXTERNA_TIMEOUT'] = API_TIMEOUT
    flask_app.config['API_EXTERNA_PROTOCOL'] = API_EXTERNA_PROTOCOL
    flask_app.config['API_EXTERNA_HOST'] = API_EXTERNA_HOST
    flask_app.config['API_EXTERNA_PORT'] = API_EXTERNA_PORT

    register_blueprints(flask_app)
    return flask_app


app = create_app()

__all__ = ['app', 'create_app']

