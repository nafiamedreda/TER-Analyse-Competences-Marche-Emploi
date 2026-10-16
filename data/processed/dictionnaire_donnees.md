# Dictionnaire de données — offres France Travail

## 1. Variables de l'offre

| colonne            | type         | obligatoire | règle                                          | source API |
|--------------------|--------------|-------------|------------------------------------------------|------------|
| job_id             | texte        | oui         | unique (si doublon : garder le + récent)       |            |
| date_creation      | date-heure   | oui         | format AAAA-MM-JJ HH:MM:SS                     |            |
| titre              | texte        | oui         |                                                |            |
| description        | texte        | oui         | conserver intégralement                        |            |
| code_rome          | texte        | non         | lettre + 4 chiffres (ex. M1805)                |            |
| intitule_rome      | texte        | non         |                                                |            |
| entreprise         | texte        | non         | souvent absente (offres anonymes)              |            |
| commune            | texte        | non         | code INSEE (ex. 75056)                         |            |
| departement        | texte        | non         | code, déduit de la commune (ex. 75, 2A, 974)   |            |
| region             | texte        | non         | nom, déduit de la commune (ex. Île-de-France)  |            |
| type_contrat       | texte        | oui         | CDI, CDD, alternance (si alternance = vrai)    |            |
| experience         | texte        | non         | valeurs : débutant, souhaitée, exigée          |            |
| formation          | texte (JSON) | non         | plusieurs valeurs possibles                    |            |
| competences        | texte (JSON) | non         | plusieurs valeurs possibles                    |            |
| date_actualisation | date-heure   | non         | sert à garder le plus récent en cas de doublon |            |
| alternance         | booléen      | non         | vrai / faux                                    |            |
| salaire            | texte        | non         | texte brut, non transformé                     |            |


## 2. Métadonnées de collecte

| colonne       | type       | obligatoire | règle                             | source API |
|---------------|------------|-------------|-----------------------------------|------------|
| date_collecte | date-heure | oui         | ajoutée par le script de collecte | —          |
| source        | texte      | oui         | ex. « API France Travail v2 »     | —          |


## 3. Colonne ajoutée par le nettoyage

| colonne         | type    | obligatoire | règle                                                            | source API |
|-----------------|---------|-------------|------------------------------------------------------------------|------------|
| doublon_suspect | booléen | oui         | vrai si même titre + entreprise + description qu'une autre offre | —          |


## 4. Règles générales

- **Valeurs manquantes** : case vide = manquante, on n'invente jamais de valeur.
- **Champ obligatoire manquant** : l'offre est supprimée.
- **Doublons exacts** : même `job_id` → on n'en garde qu'un (le plus récent).
- **Doublons probables** : même titre + entreprise + description → on signale, on ne supprime pas.
- **Hors périmètre** : ni CDI, ni CDD, ni alternance → offre retirée.
- **Texte original** : la description brute n'est jamais modifiée.
