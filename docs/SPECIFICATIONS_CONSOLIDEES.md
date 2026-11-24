# Spécifications consolidées — Eclair Commercial (SaaS Gestion Commerciale Cameroun)

> Synthèse de **18 documents** source situés dans `D:\document gestcom` (8 cahiers des charges v1→v8,
> 9 diagrammes de classes / schémas relationnels v0→v9, 1 guide CI/CD Docker).
> Règle de lecture : **la version la plus récente l'emporte**. Les contradictions entre versions et les
> manques ont été **arbitrés en §19 et §20** (décisions du 2026-11-23) : ces deux sections font foi sur le reste du document.

---

## 1. Vision produit

Logiciel **SaaS de gestion commerciale modulaire et multi-secteurs** pour les entreprises du **Cameroun / zone CEMAC**
(de la boutique de quartier à la grande entreprise multi-agences).

- **Un seul noyau logiciel piloté par la configuration** (Feature Flags / "Metadata-Driven") : à l'inscription,
  l'entreprise choisit un *preset* métier ; un `config_json` active/masque les écrans, les étapes du cycle
  commercial et **change le vocabulaire** de l'interface. Pas de duplication de code par secteur.
- **Mode 100 % connecté** : Internet (Cloud SaaS) **ou** réseau local LAN (serveur Docker dans l'entreprise).
  **Aucun mode hors-ligne / aucune synchronisation différée** (le tout premier diagramme "Offline-First / SQLite /
  SyncQueue" est **OBSOLÈTE**).
- **Multi-plateforme** : un seul code Angular → Web (PC/tablette), Android (Play Store), iOS (App Store) via Capacitor.
- **Double déploiement** : Cloud mutualisé (isolation par schéma PostgreSQL) ou On-Premise via Docker Desktop.
- **Conformité locale** : FCFA (XAF), TVA 19,25 %, NIU, RCCM, précompte sur achat, droit de timbre,
  OHADA/SYSCOHADA, DGI (numérotation continue, préparation eBilling), MTN MoMo & Orange Money.

## 2. Stack technique (retenue)

| Couche | Technologie |
|---|---|
| Frontend Web & mobile | **Angular 22 + PrimeNG 22** (thème Aura ; « 18+ » dans les sources) (p-table, p-chart, p-dialog, p-steps, p-menubar, p-panelMenu, p-calendar, p-tabView). Tailwind cité seulement en v1. |
| Apps natives | **Capacitor** (Android .aab/.apk, iOS IPA) — caméra (scan), partage PDF/WhatsApp, imprimantes BLE |
| Backend | **Python 3.12 + FastAPI**, **Pydantic v2**, **SQLModel (synchrone) + psycopg 3**, Alembic, Uvicorn, OpenAPI/Swagger auto — choix aligné sur le projet Eclair-school (les sources proposaient SQLAlchemy async/asyncpg) |
| BDD | **PostgreSQL 16**, multi-schémas (schema-per-tenant), JSONB ; PgBouncer (mode transaction) |
| Messagerie | **RabbitMQ 3.13** + Worker Python (**aio-pika**) pour e-mails SMTP |
| Paiements | Agrégateurs **Campay / CinetPay** (webhooks) + saisie manuelle de référence |
| Auth | **JWT** (contient le schéma tenant + permissions) + **code PIN** pour changement rapide de caissier |
| Docs générés | Factures A4 PDF, tickets thermiques ESC/POS 58/80 mm, planches d'étiquettes code-barres |
| CI/CD | **GitHub Actions** (Pytest couverture ≥ 75 % bloquante, tests et build Angular ; pas d'analyse SonarCloud) **+ Docker Hub** |
| Conteneurs | Docker / Docker Compose, images alpine/slim |

## 3. Secteurs cibles & presets

| Preset (exemples de codes vus) | Flux | Spécificités |
|---|---|---|
| Boutique de quartier (`BOUTIQUE_EXPRESS`, `BOUTIQUE_VENTE_DIRECTE`) | Vente directe 1 clic, vente libre sans catalogue ; achats NONE ou DIRECT | Caisse express, anti-vol par PIN vendeur, carnet de dettes par téléphone, dépenses du jour, valorisation groupée des marges |
| Supermarché / Alimentation (`SUPERMARCHE_POS`, `SUPERMARCHE_ALIMENTATION`) | POS + scan ; achats DIRECT | Codes-barres multi-conditionnements (unité/carton/casier), tickets 58/80 mm, multi-caisses, étiquettes |
| Pressing / Blanchisserie (`PRESSING`, `PRESSING_SERVICE`, `PRESSING_PRO`) | Commande (Dépôt + acompte) → Livraison (Retrait) → Facture | Statuts Reçu → Lavé → Repassé → Prêt → Livré, n° cintre/lot, QR code, alerte "linge prêt" (SMS/WhatsApp/e-mail), écran Kanban |
| Restaurant / Snack / Bar / Traiteur (`RESTAURANT_POS`) | Commande (Table) → Livraison (Servi) → Facture (Addition) ; devis traiteur | Plan de tables (JSONB), bon cuisine, déstockage auto des ingrédients au service |
| Quincaillerie / Grossiste / Négoce B2B (`QUINCAILLERIE_B2B`) | Ventes : Devis → Cmd → BL → Facture ; Achats FULL_B2B | Livraisons partielles/reliquats, transport, plafonds de crédit, factures A4 NIU/RCCM, RRR & ristournes |
| Atelier / Production (`ATELIER_PROD`, `ATELIER_MENUISERIE_COUTURE`) | Devis → Cmd → OF → Livraison → Facture | BOM, OF partiels, rebuts, coût de revient, sur-mesure (mesures JSONB) |
| Boulangerie / industrie légère (`BOULANGERIE_SUPERMARCHE`, `GROSSISTE_ET_BOULANGERIE`) | Caisse + commandes + production + commandes internes | Recette par lot (yield) ou déclaration réelle par fournée |
| Pharmacie / Électronique / Garage | POS + achats fournisseurs | Vente au détail (plaquette vs boîte via conditionnements), IMEI/n° série, main-d'œuvre + pièces |

**Flux combinables** : une boulangerie avec rayon supermarché active simultanément caisse directe + commandes + production.

## 4. Cycle commercial unifié (Ventes & Achats)

Une **seule table** `commercial_documents` (+ `document_lines`) porte Ventes (`flow_type = SALE`) et Achats
(`flow_type = PURCHASE`). Chaînage par `parent_doc_id` (auto-référence) et `source_line_id` sur les lignes.

### 4.1 Ventes
1. **Devis `QUOTE`** — sans impact stock/compta, convertible en 1 clic.
2. **Commande `ORDER`** — engagement ferme, réservation virtuelle du stock, acompte possible, peut déclencher un OF.
3. **Bon de livraison `DELIVERY`** — **mouvement physique de stock** ; livraisons partielles (qty commandée / livrée / reliquat) ; refus de pièces défectueuses (`qty_rejected`).
4. **Facture `INVOICE`** — document comptable définitif, **numéro séquentiel continu par agence/caisse** (ex. `FAC-C1-2026-0001`), **verrouillée** (non modifiable, non supprimable). Toute correction/annulation ⇒ **Avoir `CREDIT_NOTE`**.

- **Vente directe / Fast-Track POS** : "Encaisser" crée directement une `INVOICE` avec `is_delivered = true` et `PAID`, stock déduit immédiatement, sans étapes intermédiaires. Objectif : vente complète **< 15 s**.
- **Vente libre** : ligne avec `item_id = NULL`, `item_name` obligatoire (+ unité, qté, prix) ; option "Enregistrer au catalogue".
- **Commandes internes** : l'entreprise se crée comme client interne ; commande arrêtée au stade `DELIVERY` (mise en rayon) **sans facturation** (ne doit pas fausser le CA).

### 4.2 Achats — `purchase_workflow_mode`
| Mode | Cible | Fonctionnement |
|---|---|---|
| `NONE` | Boutique vente libre pure | Menu Achats masqué ; achats = simples dépenses de caisse |
| `DIRECT` | Supermarché, alimentation, pharmacie | Saisie directe du bordereau/facture fournisseur ⇒ stock +qty immédiat, **PMP (prix moyen pondéré)** recalculé, dette/règlement fournisseur enregistré. Option `require_supplier_invoice_ref` |
| `FULL_B2B` | Grossistes, quincailleries, grandes entreprises | **RFQ** (demande de prix, multi-fournisseurs) → **Commande fournisseur** (`PURCHASE_ORDER`, stock en transit, avances) → **Bon de réception `RECEIPT`** (entrée en stock réelle, réceptions partielles, rejet des articles endommagés) → **Facture fournisseur `BILL`** (rapprochement 3 voies, TVA déductible, précompte, échéancier) |

### 4.3 Valeurs finales de `doc_stage`
`QUOTE, RFQ, ORDER, DELIVERY, RECEIPT, INVOICE, BILL, CREDIT_NOTE` (la commande fournisseur = `ORDER` + `flow_type = PURCHASE`).

## 5. Logistique de livraison & transport (`enable_delivery_transport`)
- Sur le BL : `delivery_mode` = `CLIENT_PICKUP` (aucun frais) ou `COMPANY_DELIVERY` (flotte interne ou transporteur affrété).
- **Double suivi financier** :
  - `transport_cost` = coût réel supporté (carburant, chauffeur, péage, prestataire) → **déduit de la marge nette**.
  - `transport_fee_charged` = frais refacturés (0 = franco de port, sinon **saisie manuelle** du montant — pas de forfaits par zone) → ligne "Frais de livraison" **reportée automatiquement sur la facture**, TVA selon `default_transport_taxable`.
- `delivery_details` (JSONB) : zone/adresse, chauffeur, immatriculation, téléphone du réceptionnaire ; statut `PREPARING → IN_TRANSIT → DELIVERED`.

## 6. Production
- **Nomenclatures** `item_recipes` (BOM / fiches recettes) : produit fini ↔ matières premières + quantités.
- `production_mode` : `NONE` | `AUTO_DEDUCT` (restaurant : déstockage silencieux des ingrédients au service) | `WORKSHOP_ORDER` (menu "Atelier", OF).
- `recipe_consumption_mode` :
  - **`FIXED_RECIPE`** (recette par lot) : `yield_quantity` (ex. 1 sac farine + 0,5 kg levure = 250 baguettes ; plat resto yield = 1). À la clôture d'un OF de 1000 : `factor = qty_produced / yield_quantity = 4` ⇒ `PRODUCTION_OUT` = `quantity_required × factor` sur chaque ingrédient, `PRODUCTION_IN` +1000 ; coût théorique calculé.
  - **`ACTUAL_DECLARATION`** (fournée à rendement variable) : pas de recette obligatoire ; en fin de lot, saisie des matières réellement consommées (`PRODUCTION_OUT` liées à `production_order_id`, avec `unit_cost`), de la quantité bonne (`PRODUCTION_IN`) et des ratés (`qty_scrapped`). `coût unitaire réel = Σ coût matières de l'OF / qty_produced`.
- **Production partielle & rebuts** : suivi `qty_target`/`qty_ordered`, `qty_produced`, `qty_scrapped` (raté atelier), `qty_delivered`/`qty_rejected` (refusé par le client) ; mouvement `SCRAP` ; le reliquat reste ouvert. Le vendeur choisit de ne facturer que les quantités acceptées.
- **Sur-mesure** (couture, menuiserie, ferronnerie, imprimerie) : `specifications` JSONB (mesures, matière, couleur, notes, photo de référence) sur la ligne de commande et l'OF ; gabarits de champs dans `config_json.custom_production.default_spec_fields` ; pour `item_id = NULL`, matières rattachées à l'OF ⇒ `unit_cost_price` calculé et reporté sur la ligne.

## 7. Stocks, catalogue, codes-barres
- `items.item_type` : `PRODUCT`, `SERVICE`, `RAW_MATERIAL` (anciennes versions : `MENU`/`DISH`, `RAW`).
- Chaque article : `purchase_price`, `sale_price`, `unit` (Pièce, Kg, Litre, Carton, Sac, Mètre), `tax_rate`, `min_stock_alert` (stock par agence dans `item_stocks`, cf. §20), `track_stock`, `metadata` JSONB (attributs libres).
- `stock_movements` = **grand livre immuable par deltas** : `SALE_OUT, PURCHASE_IN, PRODUCTION_IN, PRODUCTION_OUT, SCRAP, ADJUSTMENT`, avec `unit_cost`, `document_id`, `production_order_id`.
- `stock_tracking` : `NONE | SIMPLE | SERIAL_NUMBER` — **la gestion des lots et dates de péremption est retirée du périmètre** (décision du 2026-11-23).
- **Codes-barres** (module activable `barcodes.enabled`) : plusieurs codes par article avec `unit_multiplier` (bouteille = 1, carton = 12, casier = 24) ; codes internes générés **préfixe `200`** (EAN-13) ou Code 128 ; étiquettes (nom boutique, article, code, prix FCFA) sur rouleau thermique **50×30 mm** ou planche A4 ; lecture caméra ou douchette USB/Bluetooth.
- Multi-agences/entrepôts : stocks cloisonnés par `branch`, vue consolidée direction.

## 8. Tiers, dettes clients ("les bons"), encaissements
- **Anti-doublon par téléphone** : format normalisé `+2376XXXXXXXX`, **unique partiel** (`WHERE phone IS NOT NULL`) — obligatoire pour tout client à crédit ; clients de passage sans téléphone autorisés.
- `aliases` : surnoms de quartier / repères géographiques, recherchables à la caisse.
- `credit_limit` : blocage automatique en cas de dépassement, déblocable par **PIN d'un responsable** (permission `credit.override`). Remboursements partiels/échelonnés, relevé partageable WhatsApp/SMS/e-mail.
- Paiements : `CASH` (calcul du rendu monnaie), `MTN_MOMO`, `ORANGE_MONEY`, `BANK_TRANSFER`, `CHEQUE`, `CLIENT_CREDIT` ; acomptes, règlements partiels ; `payment_status` `UNPAID | PARTIAL | PAID`.
- **Dépenses de caisse** quotidiennes → solde net réel du tiroir ; **clôture de caisse** avec ventilation par mode.

## 9. Remises, Rabais, Ristournes (RRR — SYSCOHADA) — module `discounts`
- Ligne : remise/rabais en % ou montant FCFA (`discount_category` REMISE|RABAIS, `discount_type` PERCENT|FIXED_AMOUNT, `discount_value`, `discount_amount`).
- Pied de document : remise/rabais/ristourne globale (`global_discount_*`).
- **Ristourne différée de fin de période** : sur le total HT des factures `INVOICE` **PAID** du partenaire, × `partners.rebate_rate` (ou barème par palier) ⇒ **Avoir automatique** `CREDIT_NOTE` avec `metadata = {"credit_reason":"PERIODIC_REBATE","period":"2026-11"}` ; restitution soit en crédit client (`current_balance -=`), soit en remboursement direct (cash/MoMo/OM) — `rebate_payout_modes: CLIENT_CREDIT | DIRECT_REFUND`.
- Plafond `max_discount_pct` par utilisateur + journalisation audit.
- **Formules (cascade avant TVA)** :
  - `Net Ligne HT = Qté × PU HT − Remise/Rabais ligne`
  - `Net Commercial HT = Σ Net Ligne HT − Réduction globale`
  - `Total TTC = Net Commercial HT + TVA 19,25 % + Frais transport refacturés + Droit de timbre`

## 10. Statistiques & marges
- À chaque vente catalogue, `items.purchase_price` (et `unit`) est **figé** dans `document_lines.unit_cost_price` ⇒ marge historique exacte.
- **Valorisation groupée des ventes libres** (`item_id IS NULL`, `unit_cost_price` NULL à la vente pour ne pas ralentir la caisse) : regroupement par `LOWER(TRIM(item_name))` sur la période, le gérant saisit **une fois** le prix d'achat par groupe ⇒ `UPDATE` en masse + mémorisation pour pré-remplir les jours suivants (`remember_last_free_sale_cost`).
- Formules :
  - `CA = Σ ventes (HT/TTC) + Σ frais de transport refacturés`
  - `COGS = Σ (qté vendue × coût unitaire [catalogue, saisi par groupe ou coût réel OF])`
  - `Marge brute / Valeur ajoutée = CA − COGS − Σ coûts de transport supportés`
  - `Bénéfice net = Marge brute − Σ dépenses & charges de caisse`
- Suivi jour / semaine / mois / plage : CA, encaissements, dépenses, créances, marges (p-chart, p-table éditable).

## 11. Sécurité, RBAC, multi-agences, audit
- `branches` (agences, boutiques, dépôts, ateliers ; `code` UQ ex. `DLA-01`, `is_main`).
- RBAC : `roles` (`is_system`, scope ALL/BRANCH), `permissions` (`code` UQ, `module`), `role_permissions` (N:N), `tenant_users` (agence, rôle, `pin_code_hash`, `max_discount_pct`, `is_active`).
- Rôles prédéfinis : Directeur Général (`*`, ALL), Chef d'Agence, Caissier, Commercial B2B, Acheteur, Magasinier, Livreur/Logistique, Chef d'Atelier, Comptable/Auditeur (ALL).
- Exemples de permissions : `pos.create_sale`, `payment.receive`, `receipt.print`, `customer.create`, `quote.create`, `order.create`, `invoice.create`, `invoice.validate`, `invoice.cancel`, `invoice.credit_note`, `partner.view_balance`, `delivery.validate`, `purchase.order`, `purchase.receive`, `stock.adjust`, `stock.scrap`, `barcode.print`, `inventory.count`, `production.view`, `production.declare_output`, `production.declare_scrap`, `cash.close_session`, `report.*`, `report.branch`, `tax.export_dgi`, `audit.view`, `credit.override`, `sale.discount`, `pos.discount.override`, `finance.view_margin`.
- `audit_logs` **immuable** : annulations, remises exceptionnelles, modifications de prix, ajustements/rejets de stock, suppressions de lignes, avoirs, dépassements de crédit — `user_id`, `branch_id`, `action`, `entity_type/name`, `entity_id`, `old_values`/`new_values` (JSONB), horodatage.
- **Règle d'or comptable** : on ne supprime jamais physiquement un client, produit, caissier, agence ou facture ayant eu une activité → `is_active = false` (archivage logique) ; facture validée → Avoir.

## 12. Architecture multi-tenant & modèle de données

### 12.1 Principe
- Schéma **`public`** : `tenants`, `global_users` (annuaire de connexion).
- Un schéma **par entreprise** `tenant_xyz` (ex. `tenant_0042`, `tenant_cm_0042`) créé **automatiquement à l'inscription** (`provisionSchema()`), avec tables + index.
- Middleware FastAPI : extrait le schéma du JWT puis `SET LOCAL search_path TO tenant_xyz, public;` au début de chaque transaction (compatibilité PgBouncer, cf. §19.4).

### 12.2 Tables issues des sources (v9) — à compléter par les 10 tables tenant et 3 tables public ajoutées en §20, noms canoniques en §19.3
**public.tenants** : `id` UUID PK, `schema_name` UQ, `company_name`, `niu`, `rccm`, `phone`, `email`, `business_preset`, `config_json` JSONB, `subscription_status`/`is_active`, `created_at`.
**public.global_users** : `id`, `tenant_id` FK (CASCADE), `identifier`/`login_identifier` UQ (téléphone ou e-mail, index sur `lower()`), `password_hash`, `is_owner`, `is_active`, `last_login_at`.

Schéma tenant :
- **branches** : `id`, `code` UQ, `name`, `city`, `address`, `phone`, `is_main`, `is_active`.
- **roles** : `id`, `name` UQ, `description`, `is_system`.
- **permissions** : `id`, `code` UQ, `module`, `label`.
- **role_permissions** : `role_id` FK, `permission_id` FK.
- **tenant_users** : `id`, `global_user_id` UQ, `branch_id` FK, `role_id` FK, `full_name`, `pin_code_hash`, `max_discount_pct`, `is_active`.
- **audit_logs** : `id`, `user_id` FK, `branch_id`, `action`, `entity_name`, `entity_id`, `payload`/`old_values`+`new_values` JSONB, `created_at`.
- **items** : `id`, `sku`, `name`, `item_type`, `category`, `unit`, `purchase_price`, `sale_price`, `tax_rate`, `track_stock`, `min_stock_alert`, `metadata` JSONB, `is_active`. (`current_stock` supprimé → `item_stocks`, cf. §20)
- **item_barcodes** : `id`, `item_id` FK, `barcode` UQ, `unit_label`, `unit_multiplier`, `is_internal`.
- **item_recipes** : `id`, `finished_item_id` FK, `raw_item_id` FK, `yield_quantity`, `quantity_required`, `unit`.
- **stock_movements** : `id`, `branch_id`, `item_id`, `document_id` NULL, `production_order_id` NULL, `movement_type`, `quantity_delta`, `unit_cost`, `created_by`, `created_at`.
- **production_orders** : `id`, `branch_id`, `document_line_id` NULL, `item_id` NULL, `custom_title`, `specifications` JSONB, `consumption_mode`, `qty_target`, `qty_produced`, `qty_scrapped`, `status` (`PENDING | IN_PROGRESS | PARTIAL | COMPLETED`), `created_at`.
- **partners** : `id`, `type` (`CLIENT | SUPPLIER | BOTH`), `name`, `aliases`, `phone` UQ partiel, `email`, `niu`, `credit_limit`, `current_balance`, `rebate_rate`, `is_active`.
- **commercial_documents** : `id`, `branch_id`, `partner_id` NULL, `parent_doc_id` NULL, `created_by`/`user_id`, `flow_type`, `doc_stage`, `doc_number` UQ, `is_delivered`, `is_locked`, `fulfillment_status`, `payment_status`, `global_discount_category|type|value|amount`, `delivery_mode`, `transport_cost`, `transport_fee_charged`, `delivery_details` JSONB, `total_ht`, `total_tax`, `total_ttc`, `amount_paid`, `metadata` JSONB (n° table, cintre, date de retrait, raison d'avoir…), `created_at`.
- **document_lines** : `id`, `document_id` FK, `item_id` FK NULL, `source_line_id` FK NULL, `item_name` NOT NULL, `unit`, `specifications` JSONB, `qty_ordered`, `qty_delivered`, `qty_rejected`, `unit_price`, `unit_cost_price` NULL, `discount_category|type|value|amount`, `tax_rate`, `line_total_ht`.
- **payments** : `id`, `branch_id`, `document_id` FK, `partner_id` FK NULL, `user_id`/`received_by`, `amount`, `method`, `reference`/`external_ref` (ID transaction MoMo), `paid_at`.

### 12.3 Politiques ON DELETE
- **CASCADE** : `role_permissions → roles/permissions`, `item_barcodes → items`, `item_recipes.finished_item_id → items`, `document_lines → commercial_documents` (uniquement devis brouillon ; FastAPI bloque la suppression dès `INVOICE`), `global_users → tenants` (résiliation définitive / RGPD / Apple).
- **RESTRICT** : `commercial_documents → branches/partners/tenant_users`, `payments → commercial_documents/partners`, `stock_movements → items/branches/production_orders`, `item_recipes.raw_item_id → items`, `production_orders → document_lines`, `tenant_users → roles`.
- **SET NULL** : `document_lines.item_id → items` (la ligne garde `item_name`, prix, coût), `commercial_documents.parent_doc_id`, `audit_logs.user_id`, (`tenant_users.branch_id` en v4).

### 12.4 Index (créés au provisioning de chaque schéma — 19 en v9)
`idx_global_users_identifier` (UQ) · `idx_docs_branch_stage_date (branch_id, doc_stage, created_at DESC)` · `idx_docs_unpaid (partner_id, payment_status) WHERE payment_status != 'PAID'` · `idx_docs_parent (parent_doc_id) WHERE NOT NULL` · `idx_docs_rebate_period (partner_id, created_at) WHERE doc_stage='INVOICE' AND payment_status='PAID'` · `idx_docs_delivery_active WHERE delivery_mode='COMPANY_DELIVERY'` · `idx_docs_metadata_gin` · `idx_docs_delivery_gin (delivery_details)` · `idx_doc_lines_doc_id` · `idx_doc_lines_item_id WHERE item_id IS NOT NULL` · `idx_doc_lines_free_sales (LOWER(TRIM(item_name))) WHERE item_id IS NULL` · `idx_doc_lines_specs_gin` · `idx_items_name_lower (LOWER(name))` · alerte stock bas via `item_stocks` (cf. §20) · `idx_item_barcodes_code` (UQ) · `idx_partners_phone_unique WHERE phone IS NOT NULL` · `idx_partners_debtors (current_balance DESC) WHERE > 0` · `idx_stock_mov_item_date (item_id, [branch_id,] created_at DESC)` · `idx_stock_mov_prod_order` · `idx_prod_orders_status WHERE status != 'COMPLETED'` · `idx_payments_doc_date` / `idx_payments_date_method` · `idx_audit_entity (entity_name, entity_id, created_at DESC)`.
Objectif : < 10 ms par requête, scan code-barres < 2 ms.

## 13. Configuration tenant (`public.tenants.config_json`) & UI dynamique

Exemple de référence (fusion des versions v6–v9) :
```json
{
  "tenant_id": "cm-dla-0085",
  "business_preset": "GROSSISTE_ET_BOULANGERIE",
  "localization": { "currency": "FCFA", "country_code": "+237", "default_tax_rate": 19.25,
                    "apply_tax_by_default": true, "stamp_duty_enabled": true,
                    "receipt_format": "THERMAL_80MM", "niu": "M0126...", "rccm": "RC/DLA/2026/B/1042" },
  "modules": {
    "enable_pos_quick_sale": true, "enable_quotes": true, "enable_orders": true,
    "enable_partial_delivery": true, "allow_free_text_items": true,
    "purchase_workflow_mode": "FULL_B2B",
    "enable_delivery_transport": true, "default_transport_taxable": true,
    "stock_tracking": "SIMPLE", "enable_credit_management": true,
    "enable_multi_branch": true, "enable_table_map": false
  },
  "ui": { "home_screen": "SALES_PIPELINE" },
  "production": { "enabled": true, "mode": "WORKSHOP_ORDER",
                  "recipe_consumption_mode": "ACTUAL_DECLARATION",
                  "custom_production": { "enabled": true, "allow_reference_photo": true,
                                         "default_spec_fields": ["Largeur", "Hauteur", "Matériau"] } },
  "discounts": { "enabled": true, "allow_line_discount": true, "allow_global_discount": true,
                 "enable_monthly_rebates": true, "rebate_payout_modes": ["CLIENT_CREDIT", "DIRECT_REFUND"] },
  "barcodes": { "enabled": true, "auto_generate_internal": true, "barcode_prefix": "200",
                "label_format": "THERMAL_50x30", "show_price_on_label": true },
  "statistics": { "enable_grouped_free_sale_margin": true, "remember_last_free_sale_cost": true },
  "notifications": { "email_enabled": true, "send_invoice_email": true, "send_low_stock_alert": true,
                     "send_debt_reminder_email": true, "send_order_ready_alert": true,
                     "send_rfq_email_to_suppliers": false },
  "ui_labels": { "menu_pos": "Vente Comptoir", "quote": "Devis Chantier", "order": "Commande Client",
                 "delivery": "Bon de Livraison", "invoice": "Facture Normalisée", "rfq": "Demande de Prix",
                 "receipt": "Bon de Réception", "transport_fee": "Frais de Livraison",
                 "partner_client": "Client / Chantier", "metadata_field_label": "Réf. Chantier" },
  "workflow_steps": []
}
```
- Valeurs : `receipt_format` = `THERMAL_58MM | THERMAL_80MM | A4_PDF` ; `label_format` = `THERMAL_50x30 | A4_GRID_40 | A4_SHEET_24` ; `workflow_steps` pour pressing/resto (ex. `["Reçu","Lavé","Repassé","Prêt"]`).
- **Frontend** : `TenantConfigService` charge `config_json` à la connexion ; menus `p-menubar`/`p-panelMenu` avec `visible: config.modules.xxx` ; **aucun terme métier en dur** → pipe `{{ 'order' | tenantLabel }}` / `config.labels.xxx` ; sections optionnelles via `*ngIf`.
- **Écran d'accueil par secteur** : Boutique → Caisse express (pavé + saisie libre + rendu monnaie) ; Supermarché → POS scan auto-focus ; Pressing → tableau des dépôts par statut (Kanban/p-tabView) ; Restaurant → plan de tables ; B2B → pipeline commercial (p-steps 4 étapes) ; Atelier → tableau de bord des OF.
- Libellés types : Pressing ORDER="Fiche de Dépôt", DELIVERY="Retrait du Linge", INVOICE="Reçu de Retrait" ; Restaurant ORDER="Commande Table", DELIVERY="Service à Table/Plat servi", INVOICE="Addition" ; Boutique INVOICE="Ticket de Caisse", action "Encaisser (F2)".

## 14. Notifications e-mail asynchrones (RabbitMQ)
- Activable par tenant (`notifications.email_enabled`) ; si désactivé, **rien n'est publié**.
- À la validation d'une facture/devis/livraison, FastAPI publie un événement JSON dans l'échange `notifications.email` (file par ex. `tenant_emails_queue`) et répond au caissier en **< 50 ms**.
- Worker Python : génère le contenu (+ PDF), envoie via SMTP global du SaaS **ou** SMTP propre au tenant, **retries** en cas d'erreur réseau.
- Cas : factures/devis/BL PDF aux clients B2B, demandes de prix fournisseurs, alertes stock bas, relances de dettes, linge prêt, avis de ristourne, rapport quotidien de clôture de caisse (CA, encaissements par mode, dépenses) au propriétaire, alertes d'audit.

## 15. Contraintes App Store / Play Store
- **iOS** : aucun bouton de paiement d'abonnement SaaS (MoMo/OM) dans l'app ; souscription/renouvellement via portail Web uniquement.
- Fonction **demande de suppression de compte** obligatoire (Apple).
- Impression : imprimantes thermiques Bluetooth Low Energy (BLE) ou Wi-Fi/LAN, + reçus PDF partageables (WhatsApp, AirPrint). Android : Bluetooth classique OK.

## 16. Déploiement On-Premise (Docker Desktop) & matériel
- Conteneurs (alpine, < 900 Mo RAM au total) : `saas-frontend` (Nginx + build Angular, reverse-proxy API, port 80, ~30 Mo), `saas-backend` (FastAPI/Uvicorn, port 8000, ~200 Mo), `saas-db` (PostgreSQL 16, volume persistant, ~300 Mo), `saas-broker` (RabbitMQ 3 management, ~150 Mo), `saas-worker` (e-mails, ~100 Mo). Broker + worker désactivables.
- LAN : seul le PC serveur exécute Docker, IP fixe (ex. `http://192.168.1.50`) ; les autres postes/tablettes/smartphones y accèdent par le Wi-Fi sans installation.
- `.wslconfig` : plafonner WSL 2 à 3–4 Go de RAM.
- Sauvegarde quotidienne planifiée : `pg_dump` compressé **et chiffré** vers disque externe / clé USB / dossier synchronisé.

| Composant | Minimum (1–2 postes) | Recommandé (multi-caisses) |
|---|---|---|
| RAM | 8 Go (WSL 2 plafonné à 3 Go) | 16 Go DDR4/DDR5 |
| Stockage | SSD 256 Go (**HDD interdit**) | SSD NVMe 512 Go – 1 To |
| CPU | Core i5 8e gén. / Ryzen 5 4 cœurs, VT-x/AMD-V | Core i5/i7 10e gén.+ / Ryzen 5/7 |
| OS | Windows 10/11 Pro 64 bits (WSL 2) ou Ubuntu 22.04+ | Windows 11 Pro ou Ubuntu 24.04 LTS |
| Énergie | Onduleur 650 VA obligatoire | Onduleur 1000–1500 VA (coupures ENEO) |

## 17. CI/CD (Guide CI/CD Docker)

> **Implémentation réelle (2026-11-24)** : l'arborescence et le pipeline suivent le projet Eclair-school et non le guide
> source ci-dessous — voir `CLAUDE.md` (section « Architecture du code »), `.github/workflows/ci.yml`,
> `backend/Dockerfile` (python:3.12-slim, utilisateur non-root, `start.sh` : attente DB → `alembic upgrade head` → Uvicorn)
> et `frontend/Dockerfile` (node:24-alpine → nginx-unprivileged :8080, `nginx.conf` SPA + proxy `/api/`).
> Images : `eclair-commercial-backend` / `eclair-commercial-frontend`. Le texte ci-dessous reste la référence du guide d'origine.

Arborescence cible :
```
saas-gestion-commerciale/
├── .github/workflows/ci-cd.yml
├── backend/   (app/, tests/, requirements.txt, requirements-dev.txt, pyproject.toml, .dockerignore, Dockerfile)
└── frontend/  (src/, angular.json, package.json, nginx.conf, .dockerignore, Dockerfile)
```
- **Backend Dockerfile** : multi-stage `python:3.12-slim` (builder : build-essential + libpq-dev, `pip wheel`) → image finale (libpq5 + curl), utilisateur non-root `appuser`, `EXPOSE 8000`, `HEALTHCHECK curl -f http://localhost:8000/api/v1/health`, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`. Image ~160 Mo.
- **Frontend Dockerfile** : `node:20-alpine` (`npm ci --legacy-peer-deps`, `npm run build -- --configuration=production`) → `nginx:1.27-alpine`, copie `dist/saas-gestion-frontend/browser`. `nginx.conf` : gzip, `try_files $uri $uri/ /index.html`, cache 1 an `immutable` pour les assets.
- **Tests** : `requirements-dev.txt` = `pytest==8.3.3`, `pytest-asyncio==0.24.0`, `pytest-cov==5.0.0`, `httpx==0.27.2` ; `pyproject.toml` : `asyncio_mode = "auto"`, `testpaths = ["tests"]`, `--cov=app --cov-fail-under=75`, omit `app/__init__.py`, `app/core/config.py`, `*/migrations/*`.
- **Priorités de tests** : isolation multi-schémas (`search_path`), cycle Devis→Commande→Livraison partielle→Facture, vente libre `item_id = NULL`, verrouillage des factures, déstockage en production partielle & SCRAP, unicité téléphone, plafond de crédit, permissions RBAC.
- **Workflow** (`push`/`pull_request` sur `main`) : job `ci-backend-tests` (services `postgres:16-alpine` [ci_user/ci_password/saas_ci_test] + `rabbitmq:3.13-alpine`, Python 3.12, env `DATABASE_URL=postgresql+asyncpg://…`, `RABBITMQ_URL`, `JWT_SECRET_KEY`, `APP_ENV=testing`) → job `cd-dockerhub-push` (seulement `push` sur `main`, après CI) : buildx, login, push `saas-gestion-backend` et `saas-gestion-frontend` en tags `:latest` et `:<sha>`, cache GHA.
- Secrets GitHub : `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`. Protection de `main` : status check obligatoire. Le CD s'arrête volontairement au push Docker Hub (déploiement ultérieur par `docker pull`).

## 18. Feuille de route (consolidée, dernière version)
1. **Phase 1 — Socle & MVP** : FastAPI, provisioning auto des schémas, middleware `search_path`, JWT + RBAC, docker-compose, CI Pytest 75 % ; Caisse express (catalogue + vente libre), paiements Cash/MoMo/OM, dettes par téléphone unique, impression tickets, suivi pressing, statistiques de base + valorisation groupée. Critère : tenant isolé + vente encaissée en < 15 s.
2. **Phase 2 — Cycles complets, Achats & Transport** : Devis/Cmd/BL partiel/Facture/Avoir, transport (coût vs refacturation), achats DIRECT & FULL_B2B, codes-barres & étiquettes, RRR, worker RabbitMQ.
3. **Phase 3 — Production & Mobile** : OF partiels/rebuts, FIXED_RECIPE / ACTUAL_DECLARATION, sur-mesure JSONB, presets pressing/restaurant, Mobile Money (Campay/CinetPay), Capacitor Android/iOS.
4. **Phase 4 — Packaging** : kit Docker Desktop clé en main, publication stores, pilote auprès des premiers commerces.


## 19. Décisions d'arbitrage (validées le 2026-11-23)

> Le porteur de projet a confirmé l'abandon du mode hors-ligne et délégué les autres arbitrages.
> **Ces décisions font foi** sur toute formulation contraire des documents sources ou des sections précédentes.

### 19.1 Périmètre
- **Mode hors-ligne : ABANDONNÉ (confirmé).** Pas de SQLite, pas de `SyncQueue`, pas d'`offline_pin_hash`, pas de synchronisation différée.

### 19.2 Configuration (`config_json`) — noms canoniques
| Retenu | Variantes à NE PAS utiliser |
|---|---|
| `public.tenants.config_json` | `settings`, `settings_json` |
| `business_preset` | `business_type`, `preset_code`, `sector_preset` |
| `modules.allow_free_text_items` | `enable_free_text_sales`, `enable_free_sale_items`, `allow_free_sale_items` |
| `modules.purchase_workflow_mode` (`NONE` / `DIRECT` / `FULL_B2B`) | `purchases.workflow_mode` |
| `modules.stock_tracking` (`NONE` / `SIMPLE` / `SERIAL_NUMBER`) | `stock_tracking_mode`, `SERIAL`, `BATCH_EXPIRY` (lots/péremption retirés) |
| objet `production` { `enabled`, `mode` (`NONE` / `AUTO_DEDUCT` / `WORKSHOP_ORDER`), `recipe_consumption_mode`, `custom_production` } | `modules.production_mode` à la racine |
| `notifications.email_enabled` | `enable_email`, `rabbitmq_email_enabled`, `enable_email_notifications`, `enable_email_rabbitmq`, `tenants.email_notif_enabled` |
| `localization.stamp_duty_enabled` | `apply_stamp_duty`, `timbre_fiscal_enabled` |
| `localization.receipt_format` | `print_format` |
| `barcodes.barcode_prefix` | `internal_prefix` |

- **`sales_workflow_mode` est supprimé.** On utilise les booléens combinables `enable_pos_quick_sale`, `enable_quotes`, `enable_orders`, `enable_partial_delivery` (entreprises mixtes).
  L'écran d'accueil devient une clé d'UI dédiée : `ui.home_screen` = `POS` / `ORDERS_BOARD` / `TABLE_MAP` / `SALES_PIPELINE` / `WORKSHOP` (valeur par défaut fixée par le preset).
- Le `config_json` est **validé par un modèle Pydantic** côté backend (valeurs par défaut + enums) et versionné (`config_version`).

### 19.3 Modèle de données — noms et enums canoniques
- `global_users.login_identifier` (UQ sur `lower()`) — pas `identifier` / `email_or_phone`.
- `tenant_users.pin_code_hash` (**toujours hashé**, argon2/bcrypt) — jamais `pin_code` en clair.
- `items.min_stock_alert` (pas `alert_threshold`), `item_recipes.quantity_required` (pas `qty_required`), `stock_movements.quantity_delta`.
- `partners.partner_type` = `CLIENT` / `SUPPLIER` / `BOTH`.
- `items.item_type` = `PRODUCT` / `SERVICE` / `RAW_MATERIAL` (un plat de restaurant = `PRODUCT` avec recette).
- `commercial_documents.created_by` (pas `user_id`) ; `payments.received_by`.
- `audit_logs` : `entity_type`, `entity_id`, `old_values`, `new_values` (JSONB).
- `doc_stage` = `QUOTE`, `RFQ`, `ORDER`, `DELIVERY`, `RECEIPT`, `INVOICE`, `BILL`, `CREDIT_NOTE`. La « commande fournisseur » = `ORDER` + `flow_type = PURCHASE` (`PURCHASE_ORDER` n'est qu'un libellé d'UI).
- Nouveau champ `commercial_documents.status` = `DRAFT` / `VALIDATED` / `CANCELLED` : le numéro définitif et le verrouillage (`is_locked`) ne sont attribués qu'à la validation ; seul un `DRAFT` peut être supprimé.
- `payments.method` = `CASH`, `MTN_MOMO`, `ORANGE_MONEY`, `BANK_TRANSFER`, `CHEQUE`, `CLIENT_CREDIT` ; nouveau champ `payments.direction` = `IN` / `OUT` (encaissement client / décaissement fournisseur, remboursement, ristourne).
- `stock_movements.movement_type` = `SALE_OUT`, `PURCHASE_IN`, `PRODUCTION_IN`, `PRODUCTION_OUT`, `SCRAP`, `ADJUSTMENT`, `TRANSFER_OUT`, `TRANSFER_IN`, `RETURN_IN`, `RETURN_OUT` (transferts inter-agences et retours ajoutés).
- Téléphones normalisés en E.164 (`+2376XXXXXXXX`) via la librairie `phonenumbers` avant écriture.
- Python **3.12** ; nombre de workers Uvicorn paramétrable par variable d'environnement (`WEB_CONCURRENCY`, défaut 2).

### 19.4 Routage multi-tenant avec PgBouncer
- `SET search_path` de session est incompatible avec PgBouncer en mode transaction ⇒ on exécute **`SET LOCAL search_path TO "<schema>", public`** au début de **chaque transaction** (événement SQLAlchemy `after_begin`).
- Le nom de schéma provient du JWT et est **validé par regex** `^tenant_[a-z0-9_]{1,50}$` avant interpolation (anti-injection).
- Migrations : **Alembic**, une branche pour `public` et une pour le modèle tenant, appliquée en boucle sur tous les schémas `tenant_*` ; le provisioning d'un nouveau tenant crée le schéma puis applique `upgrade head`.

## 20. Modèle de données final (complété)

Les documents annonçaient « 16 tables » mais en listaient 17 ; les manques identifiés ont été comblés.
**Total : 2 tables `public` + 23 tables par tenant.** (Pas de tables de gestion de la plateforme — abonnements, super-admin — ni de zones de livraison dans le périmètre actuel.)

### 20.1 Schéma `public`
| Table | Statut | Rôle |
|---|---|---|
| `tenants` | existant | Entreprises clientes, `schema_name`, `config_json` |
| `global_users` | existant | Annuaire de connexion |

### 20.2 Schéma `tenant_xyz`
**Existants (15)** : `branches`, `roles`, `permissions`, `role_permissions`, `tenant_users`, `audit_logs`, `items`, `item_barcodes`, `item_recipes`, `stock_movements`, `production_orders`, `partners`, `commercial_documents`, `document_lines`, `payments`.

**Ajouts (8)** :
| Table | Colonnes clés | Pourquoi |
|---|---|---|
| `item_stocks` | PK (`item_id`, `branch_id`), `quantity`, `reserved_qty`, `updated_at` | Stock **par agence** (exigence multi-agences). `items.current_stock` est **supprimé**. Source de vérité = `stock_movements` ; `item_stocks` est un cache mis à jour **dans la même transaction** (verrou `SELECT … FOR UPDATE`). `reserved_qty` porte la réservation virtuelle des commandes. Le **PMP** reste global sur `items.purchase_price` (recalculé à chaque `PURCHASE_IN`). |
| `item_serials` | `id`, `item_id`, `branch_id`, `serial_number` UQ, `status` (`IN_STOCK`/`SOLD`/`RETURNED`/`DEFECTIVE`), `document_line_id` NULL | N° de série / IMEI si `stock_tracking = SERIAL_NUMBER`. |
| `cash_registers` | `id`, `branch_id`, `code` UQ, `name`, `is_active` | Caisses physiques d'une agence (numérotation par agence/caisse, multi-caisses). |
| `cash_sessions` | `id`, `register_id`, `opened_by`, `opened_at`, `opening_float`, `closed_by`, `closed_at`, `expected_cash`, `counted_cash`, `difference`, `status` (`OPEN`/`CLOSED`) | Ouverture/clôture de caisse, contrôle anti-vol (écart compté vs attendu), rapport quotidien. Ajout de `payments.cash_session_id` (FK NULL). |
| `expenses` | `id`, `branch_id`, `cash_session_id` NULL, `category`, `label`, `amount`, `method`, `supplier_id` NULL, `receipt_ref`, `paid_at`, `created_by` | Dépenses de caisse ⇒ solde net du tiroir et **bénéfice net**. Sert aussi pour les achats en mode `NONE`. |
| `document_sequences` | `id`, `branch_id`, `register_id` NULL, `flow_type`, `doc_stage`, `year`, `prefix`, `last_number`, UQ(branch, register, flow, stage, year) | **Numérotation continue sans trou** (DGI) : incrément sous `SELECT … FOR UPDATE` au moment de la validation. Format `{PREFIXE}-{CODE_AGENCE}-{AAAA}-{NNNNN}` (ex. `FAC-DLA01-2026-00042`). |
| `rebate_tiers` | `id`, `partner_id` NULL (NULL = barème général), `min_amount_ht`, `rate`, `period` (`MONTHLY`/`QUARTERLY`) | Barème de ristourne par palier ; `partners.rebate_rate`, s'il est renseigné, reste prioritaire. |
| `dining_tables` | `id`, `branch_id`, `name`, `area`, `seats`, `status` (`FREE`/`OCCUPIED`/`RESERVED`), `layout` JSONB | Plan de tables restaurant (`enable_table_map`) ; référencé par `commercial_documents.metadata.table_id`. |

**Autres colonnes ajoutées** :
- `commercial_documents.workflow_status` VARCHAR NULL (indexé) : étape métier courante issue de `config_json.workflow_steps` (pressing : Reçu → Lavé → Repassé → Prêt → Livré ; cuisine : En préparation → Prêt → Servi). Chaque changement d'étape est tracé dans `audit_logs`.
- `commercial_documents.register_id` (FK NULL vers `cash_registers`).
- `is_active` sur `branches`, `items`, `partners`, `tenant_users` (archivage logique systématique).

**Index supplémentaires** : `cash_sessions (register_id) WHERE status = 'OPEN'` en UNIQUE partiel (une seule session ouverte par caisse) ; `expenses (branch_id, paid_at DESC)` ; `commercial_documents (workflow_status) WHERE workflow_status IS NOT NULL` ; `item_stocks (branch_id, item_id)`. L'alerte de stock bas (`idx_items_low_stock`) se calcule désormais par jointure `item_stocks` ↔ `items.min_stock_alert`.

### 20.3 Hors périmètre v1 (volontairement)
- Comptabilité générale complète (grand livre SYSCOHADA) : seul un **export** comptable/DGI est prévu (`tax.export_dgi`).
- eBilling DGI temps réel : préparé (numérotation, verrouillage) mais non branché tant que l'API DGI n'est pas disponible.
