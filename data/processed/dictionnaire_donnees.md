# Dictionnaire de données — offres France Travail

## 1. Variables de l'offre

| colonne            | type         | obligatoire | règle                                                                  | source API                                               |
|--------------------|--------------|-------------|------------------------------------------------------------------------|----------------------------------------------------------|
| job_id             | texte        | oui         | unique (si doublon : garder le + récent)                               | `id`                                                     |
| date_creation      | date-heure   | oui         | format AAAA-MM-JJ HH:MM:SS (UTC)                                       | `dateCreation`                                           |
| titre              | texte        | oui         |                                                                        | `intitule`                                               |
| description        | texte        | oui         | conserver intégralement                                                | `description`                                            |
| code_rome          | texte        | non         | lettre + 4 chiffres (ex. M1805)                                        | `romeCode`                                               |
| intitule_rome      | texte        | non         |                                                                        | `romeLibelle`                                            |
| entreprise         | texte        | non         | souvent absente (offres anonymes)                                      | `entreprise.nom`                                         |
| commune            | texte        | non         | code INSEE (ex. 75056)                                                 | `lieuTravail.commune`                                    |
| lieu_libelle       | texte        | non         | libellé du lieu (ex. 75 - Paris) ; sert si la commune manque           | `lieuTravail.libelle`                                    |
| departement        | texte        | non         | code, déduit de la commune, sinon du libellé du lieu (ex. 75, 2A, 974) | dérivé de `lieuTravail.commune` ou `lieuTravail.libelle` |
| region             | texte        | non         | nom, déduit de la commune ou du département (ex. Île-de-France)        | dérivé de `lieuTravail.commune` ou `lieuTravail.libelle` |
| type_contrat       | texte        | oui         | CDI, CDD, alternance (si alternance = vrai)                            | `typeContrat` + `alternance`                             |
| experience         | texte        | non         | débutant, exigée, souhaitée (absente de la collecte du 31/10)          | `experienceExige`                                        |
| formation          | texte (JSON) | non         | plusieurs valeurs possibles                                            | `formations`                                             |
| competences        | texte (JSON) | non         | plusieurs valeurs possibles                                            | `competences`                                            |
| date_actualisation | date-heure   | non         | sert à garder le plus récent en cas de doublon                         | `dateActualisation`                                      |
| alternance         | booléen      | non         | vrai / faux                                                            | `alternance`                                             |
| salaire            | texte        | non         | texte brut, non transformé                                             | `salaire.libelle`                                        |


## 2. Métadonnées de collecte

| colonne       | type       | obligatoire | règle                                                | source API                         |
|---------------|------------|-------------|------------------------------------------------------|------------------------------------|
| date_collecte | date-heure | oui         | date de la collecte, commune à tout le fichier (UTC) | `metadata.date_collecte`           |
| source        | texte      | oui         | ex. « France Travail - API Offres d'emploi v2 »      | `metadata.source` + `metadata.api` |


## 3. Colonnes ajoutées par le nettoyage

| colonne           | type    | obligatoire | règle                                                                          | source API |
|-------------------|---------|-------------|--------------------------------------------------------------------------------|------------|
| doublon_suspect   | booléen | oui         | vrai si même titre + entreprise + description qu'une autre offre               | —          |
| metier_a_verifier | booléen | oui         | vrai si le code ROME est hors du cœur du périmètre Data/IA (offre non retirée) | —          |


## 4. Règles générales

- **Valeurs manquantes** : case vide = manquante, on n'invente jamais de valeur.
- **Champ obligatoire manquant** : l'offre est retirée (voir justification ci-dessous). Les colonnes concernées sont toutes celles marquées « oui » dans les sections 1 et 2.
- **Doublons exacts** : même `job_id` → on garde la version la plus récente. Date utilisée : `date_actualisation`, ou `date_creation` si elle manque ; à égalité, la `date_collecte` la plus récente.
- **Doublons probables** : même titre + entreprise + description → on signale (`doublon_suspect`), on ne supprime pas.
- **Contrat hors périmètre** : ni CDI, ni CDD, ni alternance → offre retirée.
- **Stages** : un titre contenant « stage » ou « stagiaire » → offre retirée. L'API classe souvent les stages en CDI ou CDD : le type de contrat ne suffit pas à les repérer.
- **Métier à vérifier** : la recherche par mots-clés de la collecte ramène des offres hors sujet. Un code ROME hors de la liste M1811, M1419, M1405, M1889, M1873, M1423 (à valider par l'équipe) → on signale (`metier_a_verifier`), on ne supprime pas.
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
| stage hors périmètre                    | stages                     |
| hors fenêtre d'un an                    | fenêtre d'un an            |
| doublon exact (version plus ancienne)   | doublons exacts            |
