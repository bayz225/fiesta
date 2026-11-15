# Fiesta — gestion d’événements avec Odoo

Fiesta est un environnement Odoo 19 conteneurisé, accompagné du module personnalisé [`event_manager`](custom-addons/event_manager/README.md). Il permet de créer des événements depuis les contacts, de gérer les invitations et de suivre les capacités et les confirmations.

## Fonctionnalités

- Création et gestion des événements : organisateur, date, heure, lieu, thème et capacité.
- Invitations liées aux contacts Odoo, avec contrôle des doublons et des places disponibles.
- Déclaration de l’heure d’arrivée et du nombre d’accompagnants.
- Accès aux événements organisés et aux invitations reçues depuis les fiches contact.
- Tableau de bord et réglages du délai de confirmation et de la marge horaire.

## Technologies

- Odoo 19 (version déclarée par le module)
- PostgreSQL (version sélectionnée par configuration)
- Docker Compose
- Python, XML, JavaScript et SCSS pour le module Odoo

## Structure du dépôt

```text
.
├── compose.yaml
├── odooconf/
│   └── odoo.conf
├── custom-addons/
│   └── event_manager/
│       ├── models/
│       ├── views/
│       ├── wizard/
│       ├── security/
│       ├── static/
│       └── __manifest__.py
├── requirements.txt
└── README.md
```

## Prérequis

- Docker Desktop (ou Docker Engine) avec le plugin Docker Compose
- Un fichier `.env` à la racine du dépôt, configuré selon les variables utilisées dans [`compose.yaml`](compose.yaml)
- Un dossier d’addons Enterprise valide si vous utilisez le montage Enterprise défini dans Compose

## Démarrage local

1. Créez un fichier `.env` à la racine. Exemple de configuration locale à adapter :

   ```dotenv
   ODOO_VERSION=19.0
   POSTGRES_VERSION=15
   ODOO_CONTAINER_NAME=fiesta-odoo
   DB_CONTAINER_NAME=fiesta-db
   ODOO_PORT=8069
   POSTGRES_DB=postgres
   POSTGRES_USER=odoo
   POSTGRES_PASSWORD=odoo
   CONFIG_PATH=./odooconf
   ADDONS_PATH=./custom-addons
   ENTREPRISE_PATH=./enterprise-addons
   ```

   `CONFIG_PATH`, `ADDONS_PATH` et `ENTREPRISE_PATH` doivent pointer vers des dossiers accessibles à Docker. Si vous n’avez pas les addons Enterprise, créez un dossier local vide pour le montage ou adaptez `compose.yaml` pour retirer ce volume. L’exemple `POSTGRES_PASSWORD=odoo` correspond à la valeur `db_password` de `odooconf/odoo.conf` et ne convient qu’à un environnement local isolé. Si vous changez les identifiants PostgreSQL, mettez aussi à jour les paramètres `db_user` et `db_password` d’Odoo. Ne publiez jamais votre fichier `.env`.

2. Démarrez Odoo et PostgreSQL :

   ```powershell
   docker compose up -d
   docker compose ps
   ```

3. Ouvrez [http://localhost:8069](http://localhost:8069) (ou le port choisi avec `ODOO_PORT`) et créez une base de données Odoo. Notez son nom : les commandes de mise à jour ci-dessous doivent cibler cette base.

4. Dans Odoo, activez le mode développeur, mettez à jour la liste des applications, recherchez **Event Manager** et installez l’application.

Les données de PostgreSQL et les fichiers Odoo sont conservés dans les volumes Docker déclarés dans Compose. Pour arrêter les services sans supprimer les données :

```powershell
docker compose stop
```

Pour arrêter et supprimer les conteneurs :

```powershell
docker compose down
```

> `docker compose down -v` supprime également les volumes et donc les données persistantes. À utiliser uniquement si vous souhaitez réinitialiser l’environnement.

## Mettre à jour le module

Après une modification du code, remplacez `ma_base_odoo` par le nom de votre base, puis mettez à jour `event_manager` et redémarrez le service :

```powershell
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d ma_base_odoo -u event_manager --stop-after-init
docker compose restart odoo
```

Vous pouvez aussi mettre à jour le module depuis l’interface des applications Odoo.

## Documentation du module

La documentation fonctionnelle et technique du module, incluant ses modèles, ses assistants et ses règles de configuration, se trouve dans [`custom-addons/event_manager/README.md`](custom-addons/event_manager/README.md).

## Sécurité avant publication

- Le fichier `.env` contient la configuration locale et des identifiants : ne le commitez pas.
- Changez également `admin_passwd` dans [`odooconf/odoo.conf`](odooconf/odoo.conf) avant d’exposer l’instance ; coordonnez tout changement d’identifiants PostgreSQL avec la configuration Odoo.
- Évitez les identifiants par défaut en dehors d’un environnement local isolé.
- Le module accorde des droits CRUD étendus aux utilisateurs internes ; vérifiez les droits et règles d’accès nécessaires avant un déploiement partagé ou en production.
