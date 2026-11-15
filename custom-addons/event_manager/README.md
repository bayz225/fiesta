# Event Manager — Odoo Addon

Application Odoo de gestion d’événements et d’invitations, intégrée aux contacts. Elle permet aux utilisateurs internes de créer des événements, d’inviter des contacts et de suivre les informations de participation.

> Documentation du dépôt Fiesta : [`README.md`](../../README.md)

## Informations du module

| Propriété | Valeur |
|---|---|
| Nom technique | `event_manager` |
| Version du module | `19.0.1` |
| Version Odoo ciblée | Odoo 19 |
| Type | Application |
| Dépendances Odoo | `base`, `contacts`, `mail`, `web` |
| Auteur déclaré | Bayz225 |

Les métadonnées et les dépendances sont définies dans [`__manifest__.py`](__manifest__.py).

## Fonctionnalités

### Événements

- Création d’événements avec organisateur, description, date, heure, lieu, thème/couleur et capacité maximale.
- Calcul du nombre de participants (invités et accompagnants) et des places restantes.
- Validation d’une date qui ne soit pas passée et d’une capacité minimale de quatre personnes.
- Consultation des événements et de leur liste d’invités.

### Invitations et participation

- Ajout de contacts à un événement avec un assistant depuis la fiche de l’organisateur.
- Exclusion de l’organisateur, des contacts déjà invités et des entreprises dans le sélecteur d’invités.
- Prévention des invitations en double par contrainte en base et validation applicative.
- Saisie ou mise à jour de l’heure d’arrivée et du nombre d’accompagnants.
- Vérification de la capacité disponible et refus d’un nombre négatif d’accompagnants.

### Intégration Contacts et tableau de bord

- Bouton **Créer un événement** depuis une fiche contact.
- Onglets **Mes événements** et **Invitations reçues**, avec actions contextuelles pour inviter ou confirmer sa participation.
- Tableau de bord accessible depuis le menu Contacts.
- Vue pivot sur les contacts avec des mesures liées aux événements et aux invités.

### Paramètres

Les paramètres sont disponibles dans **Contacts → Configuration → Paramètres Événements** :

| Paramètre | Valeur par défaut | Description |
|---|---:|---|
| Délai limite de confirmation | 5 jours | Nombre de jours avant l’événement utilisé pour calculer l’expiration de la confirmation. |
| Marge horaire d’arrivée | 2 heures | Écart autorisé autour de l’heure de l’événement pour l’heure d’arrivée. |

## Modèles et assistants

| Modèle | Rôle |
|---|---|
| `fiesta.event` | Événement, organisateur, capacité et compteurs calculés. |
| `fiesta.event.invitation` | Relation événement-contact, heure d’arrivée et accompagnants. |
| `res.partner` (hérité) | Liens vers les événements organisés et invitations reçues, ainsi que données statistiques. |
| `add.event.wizard` | Création rapide d’un événement depuis un contact. |
| `add.contact.to.event.wizard` | Ajout de plusieurs contacts à un événement. |
| `add.guest.info.to.event.wizard` | Saisie des détails de participation d’un invité. |

## Installation

1. Copiez le dossier `event_manager` dans un répertoire d’addons personnalisé présent dans `addons_path`.
2. Assurez-vous que les dépendances `base`, `contacts`, `mail` et `web` sont installées.
3. Redémarrez Odoo et mettez à jour la liste des applications en mode développeur.
4. Recherchez **Event Manager** ou `event_manager`, puis installez l’application.

Dans l’environnement Docker du dépôt, le dossier `custom-addons` est monté dans `/mnt/extra-addons`. Depuis la racine du dépôt, remplacez `ma_base_odoo` par le nom de votre base :

```powershell
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d ma_base_odoo -u event_manager --stop-after-init
docker compose restart odoo
```

Pour les instructions complètes de démarrage et la configuration des identifiants PostgreSQL, consultez le [README principal](../../README.md).

## Structure

```text
event_manager/
├── controllers/       # Contrôleurs du module
├── demo/              # Données de démonstration
├── i18n/              # Fichiers de traduction
├── models/            # Événements, invitations et extension des contacts
├── security/          # Droits d’accès aux modèles
├── static/src/        # Assets backend JavaScript, XML et SCSS
├── views/             # Vues, actions, menus et réglages
├── wizard/            # Assistants de création et de participation
└── __manifest__.py    # Métadonnées, dépendances, données et assets
```

## Notes techniques et sécurité

- L’accès aux modèles métier et assistants est accordé au groupe Odoo `base.group_user` par [`security/ir.model.access.csv`](security/ir.model.access.csv). Les droits CRUD sont activés ; le module ne déclare pas de règles d’enregistrement dédiées.
- Le module inclut une contrainte unique sur le couple événement/contact invité.
- Les données XML de démonstration sont chargées uniquement en mode démonstration.
- Le dossier `i18n` contient actuellement `en_US.po`. N’affichez pas de support de traduction supplémentaire comme disponible sans ajouter et vérifier les fichiers correspondants.
- Aucune suite de tests automatisés propre au module n’est présente dans le dépôt.

Avant d’utiliser le module dans une instance partagée ou en production, évaluez les droits accordés aux utilisateurs internes et ajoutez les règles d’accès adaptées à votre organisation.
