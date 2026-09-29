# Argos — Security Orchestration Platform

Reference infrastructure for the Argos C2 platform architecture.

> Companion repository for the paper:
> **Argos: An Accessible Open-Source Command-and-Control Framework
> for Orchestrating Edge Devices**

---

## Architecture

```
┌─── VPS (AWS EC2 / any cloud) ─────────────────────────────────────┐
│                                                                    │
│  [Frontend :3000]  [Backend API :8000]                            │
│  [Keycloak :8080]  [N8N :5678]  [PostgreSQL]                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
              ↑  Cloudflare Tunnel (outbound, encrypted)
┌─── Edge Device (client network) ──────────────────────────────────┐
│                                                                    │
│  [Flask Agent :5000]  →  [argos-discovery container]             │
│  [Cloudflare Tunnel]                                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Quick start

### VPS — Control plane

```bash
cd vps
cp .env.example .env
docker compose up -d
```

| Service  | URL                         | Credentials   |
|----------|-----------------------------|---------------|
| Frontend | http://localhost:3000       | admin / admin |
| API docs | http://localhost:8000/docs  | —             |
| Keycloak | http://localhost:8080       | admin / admin |
| N8N      | http://localhost:5678       | admin / admin |

### Edge device

```bash
# 1. Build the discovery task image
cd edge-device/tasks/nmap
docker build -t argos-discovery .

# 2. Start the agent
cd ../..
cp .env.example .env
docker compose up -d
```

### Test the agent

```bash
# Health check
curl http://localhost:5000/health

# Trigger async discovery
curl -X POST http://localhost:5000/scan/discovery \
  -H "Content-Type: application/json" \
  -d '{"target": "192.168.1.1"}'

# Response (immediate):
# {"job_id": "A3F2C1B0", "status": "accepted", ...}
```

---

## File structure

```
argos/
├── vps/
│   ├── docker-compose.yml      # Full control plane stack
│   ├── .env.example
│   ├── frontend/
│   │   ├── index.html          # Login + dashboard
│   │   ├── nginx.conf          # Port 3000
│   │   └── Dockerfile
│   └── backend/
│       ├── main.py             # FastAPI with JWT auth
│       ├── init.sql            # Schema + seed (admin/admin)
│       ├── requirements.txt
│       └── Dockerfile
└── edge-device/
    ├── docker-compose.yml
    ├── .env.example
    ├── agent/
    │   ├── app.py              # Flask async agent
    │   ├── requirements.txt
    │   └── Dockerfile
    └── tasks/
        └── nmap/
            └── Dockerfile      # Network discovery
```

---

## Notes

- **Keycloak and N8N** are included as placeholders for future
  IAM and automation integration.
- **Default credentials** (`admin`/`admin`) are for local
  development only. Change before any production deployment.

---

## Citation

```bibtex
@inproceedings{dibartolo2026jnic,
  author    = {Di Bartolo, Agustín Javier and others},
  title     = {Arquitectura de comando y control basada en roles
               para la orquestación segura de nodos de auditoría distribuidos},
  booktitle = {Actas de las XI Jornadas Nacionales de Investigación
               en Ciberseguridad (JNIC 2026)},
  pages     = {246--253},
  year      = {2026},
  doi       = {10.5821/ebook-9791388098437}
}
```
