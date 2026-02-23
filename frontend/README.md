# SmartDeals Bot (Divulgador Inteligente)

Bot local com FastAPI + React para coletar ofertas de Mercado Livre/Amazon, pontuar com regras explicáveis, passar por aprovação manual e publicar em Telegram + WhatsApp (draft ou Cloud API).

## 1) Como rodar (jeito leigo)

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

## 2) Fluxo do bot

- Scheduler roda a cada N minutos (configurável via `.env`) ou manualmente em **Rodar Scan Agora**.
- Fontes:
  - Mercado Livre via API oficial de busca (`/sites/MLB/search`).
  - Amazon em modo leve por links/ASINs manuais (sem scraping agressivo).
- Ofertas entram no SQLite, passam por deduplicação e scoring.
- Em `MANUAL`, ficam `pending_approval`; em `AUTO`, aprovam por threshold.
- Publicação:
  - Telegram: Bot API
  - WhatsApp:
    - `draft`: gera link `wa.me/?text=...`
    - `cloud_api`: envia via Meta Cloud API se credenciais existirem

## 3) Endpoints principais

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

## 4) Configuração de canais

No dashboard, na seção de configuração:
- Telegram: `bot_token` e `chat_id`
- WhatsApp:
  - `provider=draft` (seguro para uso local/manual)
  - `provider=cloud_api` + `phone_number_id` + `token` + números destino

## 5) Notas de segurança

- Tokens sensíveis ficam no backend/DB, não em variáveis front-end.
- API protegida por JWT simples via `/auth/login`.
- Troque `SECRET_KEY` e senha admin em produção.

## 6) Estrutura

- `backend/`: API, scheduler, fontes, scoring, posters
- `frontend/`: dashboard React + Vite
- `data/`: sqlite e dados persistentes
- `seeds.json`: sugestões iniciais de busca/categorias
- `message_templates.md`: modelos de texto
