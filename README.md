# SmartDeals Bot (Divulgador Inteligente)

Bot local com FastAPI + React para coletar ofertas de Mercado Livre/Amazon, pontuar com regras explicáveis, passar por aprovação manual e publicar em Telegram + WhatsApp (draft ou Cloud API).

## Como rodar

1. Copie variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
2. Suba os containers:
   ```bash
   docker compose up --build
   ```
3. Abra:
   - Dashboard: http://localhost:5173
   - API: http://localhost:8000/docs
4. Login padrão do dashboard:
   - usuário: `admin`
   - senha: `admin123`

## Checklist rápido de persistência SQLite

- O caminho padrão do banco é `data/smartdeals.db` (container resolve para `/app/data/smartdeals.db`).
- O `docker-compose.yml` monta volume persistente `./data:/app/data`.
- O backend cria pasta e tabelas no startup (`init_db()`).

## Endpoints principais

- `POST /auth/login`
- `GET /config`
- `PUT /config`
- `POST /sources/test`
- `POST /scan/run`
- `GET /deals?status=&q=&min_score=&source=`
- `POST /deals/{id}/approve`
- `POST /deals/{id}/reject`
- `POST /deals/{id}/post`
- `GET /posts`
- `GET /runs`
- `GET /health`

## Estrutura

- `backend/`: API, scheduler, fontes, scoring, posters.
- `frontend/`: dashboard React + Vite.
- `data/`: sqlite e dados persistentes em runtime.