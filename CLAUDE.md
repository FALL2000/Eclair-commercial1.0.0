# CLAUDE.md — Eclair Commercial 1.0.0

## Projet
SaaS de **gestion commerciale multi-secteurs** pour le **Cameroun / CEMAC** (boutiques, supermarchés, pressings,
restaurants, quincailleries/B2B, ateliers de production, boulangeries, pharmacies). Un seul noyau, piloté par un
`config_json` par entreprise (presets métier, modules activables, libellés d'interface dynamiques).

**Spécification complète et à jour : [`docs/SPECIFICATIONS_CONSOLIDEES.md`](docs/SPECIFICATIONS_CONSOLIDEES.md)** —
à lire avant toute tâche fonctionnelle, modèle de données, API ou UI. Elle synthétise les 18 documents sources de
`D:\document gestcom` (cahiers des charges v1→v8, diagrammes de classes v0→v9, guide CI/CD). En cas de doute,
la version la plus récente des sources l'emporte.

## Décisions structurantes (ne pas remettre en cause sans validation)
- **100 % connecté** (Cloud ou LAN on-premise). **Pas d'offline, pas de SQLite, pas de file de synchro.**
- Stack : **Angular 22 + PrimeNG 22 (thème Aura) + Capacitor** (Web/Android/iOS) · **Python 3.12 + FastAPI**
  (Pydantic v2, **SQLModel synchrone + psycopg 3**, comme Eclair-school) · **PostgreSQL 16** · Alembic ·
  **RabbitMQ 3.13 + worker aio-pika** (e-mails, à venir) · Docker Compose.
- **Multi-tenant schema-per-tenant** : `public` (`tenants`, `global_users`) + un schéma `tenant_xyz` par entreprise,
  provisionné à l'inscription ; le schéma vient du JWT et est appliqué via `search_path` à chaque requête
  (avec PgBouncer en mode transaction → `SET LOCAL` par transaction).
- **Cycle commercial unifié** : une table `commercial_documents` (+ `document_lines`) pour Ventes et Achats,
  `doc_stage` ∈ QUOTE, RFQ, ORDER, DELIVERY, RECEIPT, INVOICE, BILL, CREDIT_NOTE, chaînage `parent_doc_id`.
  Le stock bouge à DELIVERY/RECEIPT (ou immédiatement en vente directe POS).
- **Factures validées verrouillées**, numérotation continue par agence ; correction uniquement par **Avoir**.
  Jamais de suppression physique d'une entité ayant un historique → `is_active = false`.
- **Vente libre** : `document_lines.item_id = NULL` + `item_name` obligatoire ; marges valorisées a posteriori par
  regroupement `LOWER(TRIM(item_name))`.
- `stock_movements` = journal immuable par deltas. Coût d'achat figé sur chaque ligne (`unit_cost_price`).
- Clients à crédit identifiés par **téléphone normalisé `+237…` unique (partiel)** + `aliases` ; plafond de crédit
  déblocable par PIN manager. PIN toujours **hashé**.
- Fiscalité : FCFA, TVA 19,25 %, NIU, RCCM, précompte, droit de timbre ; remises en cascade **avant** TVA (SYSCOHADA).
- Paiements : espèces, MTN MoMo, Orange Money (Campay/CinetPay), virement, chèque, crédit client.
- iOS : aucun paiement d'abonnement dans l'app ; suppression de compte obligatoire.
- Aucun libellé métier en dur dans Angular : `TenantConfigService` + pipe `tenantLabel`.

## Architecture du code (calquée sur `D:\Eclair-school-1.0.0`)
```
backend/                      # FastAPI, lancé depuis ce dossier (imports absolus : `from config.settings import ...`)
  main.py                     # init_api(), CORS, handler d'erreurs de validation (400), /ping
  config/                     # settings.py (pydantic-settings, .env), database.py (engine, sessions public/tenant)
  common/                     # dependencies.py (get_db…), enumeration.py (enums canoniques §19.3), validators.py
  controllers/<domaine>/      # <entite>_controllers.py : APIRouter + factory get_<entite>_service(db)
  controllers/router.py       # include_router(..., prefix="/<entite>", tags=[...]) ; préfixe global /api/v1
  services/<domaine>/         # <entite>_service.py : logique métier, commit/rollback, HTTPException {error_code, message}
  repositories/<domaine>/     # <entite>_repository.py : hérite de BaseRepository[Model] (findOne, findAll, findBy…, save)
  models/<domaine>/           # tables SQLModel (table=True) héritant de <Entite>Base ; auto-importées par models/__init__.py
  schemas/<domaine>/          # <entite>_dto.py : <Entite>Base, CreateDTO, UpdateDTO, ResponseDTO
  security/                   # jwt_handler.py (le JWT porte `tenant_schema`), password_hacher.py (bcrypt)
  utils/logger.py             # logs fichiers rotatifs dans backend/logs/
  migrations/                 # Alembic ; start.sh exécute `alembic upgrade head` puis Uvicorn
  tests/                      # pytest (+ couverture), conftest.py fournit `client`
frontend/                     # Angular 22 standalone, PrimeNG (providePrimeNG dans app.config.ts), tests Vitest
.github/workflows/ci.yml      # CI : tests backend + frontend ; sur main : push Docker Hub
docker-compose.yml            # db (PostgreSQL 16), backend (:8000), frontend (Nginx :80 → proxy /api/ vers backend)
```
- Sessions BD : `config.database.create_public_session()` pour `public`, `create_tenant_session(schema)` pour les
  données d'une entreprise (applique `SET LOCAL search_path` à chaque transaction ; schéma validé par
  `common.validators.validate_tenant_schema`). Ne jamais interpoler un nom de schéma non validé.
- Dépendances Python : éditer `requirements.in` (prod) / `requirements-dev.in` (tests, inclut la prod) puis
  `pip-compile --strip-extras requirements.in` **puis** `pip-compile --strip-extras requirements-dev.in` (dans cet ordre) ;
  en local : `pip install -r requirements-dev.txt` ; l'image Docker n'installe que `requirements.txt` ;
  ne pas modifier les `.txt` à la main. Derrière l'antivirus Avast : `PIP_CERT="C:\ProgramData\Avast Software\Avast\wscert.pem"`.
- Commandes : backend `pytest` (depuis `backend/`, couverture ≥ 75 % bloquante) ; frontend `npm run test:ci`, `npm run build`.

## Qualité / CI
- Pytest avec **couverture ≥ 75 % bloquante** ; CD = build & push des images
  Docker Hub `eclair-commercial-backend` / `eclair-commercial-frontend` (tags `latest` + SHA) sur push `main` uniquement.
- Secrets GitHub requis : `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.
- Langue du projet et de la documentation : **français**.

## Arbitrages (2026-11-23) — font foi
Les §19 (noms canoniques, enums, routage PgBouncer/`SET LOCAL`, Alembic par schéma) et §20 (modèle final :
2 tables `public` + 23 tables tenant) de la spécification consolidée tranchent toutes les contradictions des sources.
À retenir : mode hors-ligne, lots/dates de péremption et tables de gestion de la plateforme (abonnements, super-admin), zones de livraison **retirés du périmètre** par le porteur de projet ; `sales_workflow_mode` remplacé par des
booléens + `ui.home_screen` ; stock **par agence** dans `item_stocks` (plus de `items.current_stock`) ; caisses,
sessions de caisse, dépenses, n° de série, compteurs de numérotation (`document_sequences`) modélisés ;
`commercial_documents.status` DRAFT/VALIDATED/CANCELLED. Utiliser exclusivement les noms du §19.
