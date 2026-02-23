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


## Troubleshooting (Windows)

Se aparecer erro parecido com:

```text
unable to get image 'divulgador-inteligente-frontend': error during connect:
open //./pipe/dockerDesktopLinuxEngine: O sistema não pode encontrar o arquivo especificado.
```

isso normalmente significa que o daemon do Docker Desktop (engine Linux) **não está rodando**.

Passos para resolver:

1. Abra o **Docker Desktop** e aguarde status `Engine running`.
2. No Docker Desktop, confirme que está em **Linux containers** (não Windows containers).
3. No PowerShell/CMD, valide:
   ```bash
   docker version
   docker info
   ```
   Se esses comandos falharem no bloco `Server`, o daemon ainda não subiu.
4. Tente novamente na raiz do projeto:
   ```bash
   docker compose up --build
   ```
5. Se persistir, reinicie o Docker Desktop e rode:
   ```bash
   docker context ls
   docker context use default
   ```

Se você usa WSL2, confira também se a integração da distro está habilitada em:
`Settings > Resources > WSL integration`.

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