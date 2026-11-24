# Proyecto final: infraestructura containerizada con monitoreo

Nginx (proxy inverso + balanceo) → 3 backends Flask → métricas en Prometheus → dashboards en Grafana.
Incluye Nginx Prometheus Exporter y cAdvisor.

**Integrantes:** Julian Esteban Perez

## Arquitectura

```
Cliente → Nginx :8080 → backend1 / backend2 / backend3 (:5000, /metrics)
                 │
   nginx-exporter ← stub_status (Nginx, red interna :8080)
   cAdvisor (métricas de contenedores)
         ↓
     Prometheus :9090 → Grafana :3000
```
Todos los servicios comparten la red Docker `monitoring-net`.

## Requisitos previos
- Docker y Docker Compose v2 (`docker --version`, `docker compose version`)
- (Pruebas de carga) [k6](https://k6.io/docs/get-started/installation/)
- Linux/WSL2/Docker Desktop. cAdvisor requiere acceso a `/sys`, `/var/lib/docker` y `/dev/kmsg`.

## Levantar la infraestructura
```bash
docker compose up -d --build
docker compose ps
```

## URLs
| Servicio | URL |
|---|---|
| Aplicación (Nginx) | http://localhost:8080 |
| Prometheus | http://localhost:9090 (Status → Targets) |
| Grafana | http://localhost:3000 (admin / admin) |
| cAdvisor | http://localhost:8081 |

## Verificar el balanceo de carga
```bash
for i in $(seq 1 9); do curl -s localhost:8080/; echo; done
```
Cada respuesta muestra `"instancia"` rotando entre 1, 2 y 3 (round robin). El encabezado `X-Upstream` indica el backend atendido: `curl -i localhost:8080/`.

## Verificar métricas
1. Prometheus → Status → Targets: todos en estado **UP** (backend x3, nginx, cadvisor).
2. Consultas de ejemplo: `http_requests_total`, `nginx_http_requests_total`, `container_memory_usage_bytes`.
3. Grafana → Dashboards → *Rendimiento general de la infraestructura* (se provisiona automáticamente).

## Pruebas de carga
```bash
k6 run k6/load-test.js
```
Mientras corre, observe el dashboard de Grafana (tasa de solicitudes, latencia p95, CPU/memoria).

## Detener
```bash
docker compose down        # conserva los volúmenes (datos de Prometheus/Grafana)
docker compose down -v     # borra también los volúmenes
```

## Estructura
```
docker-compose.yml
backend/            app.py, requirements.txt, Dockerfile
nginx/nginx.conf
prometheus/prometheus.yml
grafana/            provisioning/ y dashboards/
k6/load-test.js
```
