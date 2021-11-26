from flask import Flask
from jaeger_client import Config
from flask_opentracing import FlaskTracer


class TracerService:
    def __init__(self):
        self.flask_tracer = None

    def initialize_tracer(self):
        config = Config(
            config={
                'sampler': {'type': 'const', 'param': 1}
            },
            service_name='hello-world')
        return config.initialize_tracer()

    def init_app(self, app: Flask) -> FlaskTracer:
        new_tracer = FlaskTracer(self.initialize_tracer, app=app)
        self.flask_tracer = new_tracer

    def get_flask_tracer(self) -> FlaskTracer:
        return self.flask_tracer


tracer = TracerService()
