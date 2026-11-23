import os
import random
import socket
import time

from flask import Flask, Response, jsonify, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

app = Flask(__name__)

INSTANCE = os.getenv("INSTANCE_ID", "1")

REQUESTS = Counter(
    "http_requests_total",
    "Total de solicitudes HTTP",
    ["method", "endpoint", "status", "instance"],
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latencia de las solicitudes HTTP en segundos",
    ["method", "endpoint", "instance"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)


@app.before_request
def start_timer():
    request._start = time.perf_counter()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        endpoint = request.url_rule.rule if request.url_rule else "unknown"
        elapsed = time.perf_counter() - getattr(request, "_start", time.perf_counter())
        REQUESTS.labels(request.method, endpoint, response.status_code, INSTANCE).inc()
        LATENCY.labels(request.method, endpoint, INSTANCE).observe(elapsed)
    return response


@app.route("/")
def index():
    return jsonify(
        mensaje="Hola desde el backend",
        instancia=INSTANCE,
        hostname=socket.gethostname(),
    )


@app.route("/slow")
def slow():
    """Simula trabajo con latencia variable (útil para los dashboards)."""
    time.sleep(random.uniform(0.05, 0.5))
    return jsonify(instancia=INSTANCE, mensaje="respuesta lenta")


@app.route("/health")
def health():
    return jsonify(status="ok", instancia=INSTANCE)


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
