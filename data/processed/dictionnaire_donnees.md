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
- **Champ obligatoire manquant** : l'offre est retirée (voir justification ci-dessous). Les colonnes concernées sont toutes celles marquées « oui » dans les sections 1 et 2.
- **Doublons exacts** : même `job_id` → on garde la version la plus récente. Date utilisée : `date_actualisation`, ou `date_creation` si elle manque ; à égalité, la `date_collecte` la plus récente.
- **Doublons probables** : même titre + entreprise + description → on signale (`doublon_suspect`), on ne supprime pas.
- **Contrat hors périmètre** : ni CDI, ni CDD, ni alternance → offre retirée.
- **Métier hors périmètre** : le filtre principal est fait à la collecte (codes ROME du périmètre Data/IA). Le nettoyage peut refaire ce contrôle dès que la liste des codes ROME est validée.
- **Fenêtre d'un an** : on garde les offres dont `date_creation` est comprise entre la date de référence moins un an et la date de référence. **Date de référence** : la `date_collecte` la plus récente du fichier (modifiable dans le script).
- **Texte original** : la description brute n'est jamais modifiée.


## 5. Justification et traçabilité des retraits

Une offre à laquelle il manque un champ obligatoire est retirée car elle ne peut pas être exploitée correctement :

| champ manquant        | conséquence si on gardait l'offre                                       |
|-----------------------|-------------------------------------------------------------------------|
| job_id                | impossible de détecter les doublons ou de retrouver l'offre             |
| date_creation         | impossible de la placer dans le temps et d'appliquer la fenêtre d'un an |
| titre, description    | rien à analyser : ce sont les textes dont on extrait les compétences    |
| type_contrat          | impossible de vérifier le périmètre                                     |
| date_collecte, source | offre non traçable (on ne sait pas quand ni d'où elle vient)            |

Aucune offre n'est retirée en silence : chaque offre retirée est écrite dans `data/processed/offres_retirees.csv`, avec toutes ses colonnes et une colonne `motif` :

| motif                                   | règle appliquée            |
|-----------------------------------------|----------------------------|
| champ obligatoire manquant : <colonnes> | champ obligatoire manquant |
| contrat hors périmètre                  | contrat hors périmètre     |
| métier hors périmètre                   | métier hors périmètre      |
| hors fenêtre d'un an                    | fenêtre d'un an            |
| doublon exact (version plus ancienne)   | doublons exacts            |
