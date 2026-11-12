# Nettoyage des offres France Travail

## Objectif dans le TER

Transformer les offres d'emploi collectées depuis France Travail en une base propre et structurée, conforme au dictionnaire de données (`data/processed/dictionnaire_donnees.md`). Cette base servira à l'analyse des données (phase 3) et à l'extraction des compétences (phase 4).

Le script travaille sur le JSON produit par `collect_offres.py` (collecte du 31/10/2026) : **615 offres lues, 597 offres finales**.

## Fichiers

```text
data/
  raw/
    offres_france_travail_public_2026-10-31_13-43.json   # offres collectées, sans contacts (branche amina-france-travail)
    offres_fictives.csv                           # offres de test, avec cas pièges
    insee/                                        # tables géographiques (à télécharger, voir ci-dessous)
      v_commune_2026.csv
      v_departement_2026.csv
      v_region_2026.csv
  processed/
    dictionnaire_donnees.md                       # schéma de la base et règles de nettoyage
    mcd_mod.md                                    # MCD / MOD et script SQL de la base relationnelle
    offres_propres.csv                            # généré par le script
    offres_retirees.csv                           # généré : offres retirées + motif
src/
  france_travail/
    nettoyage.py
    README.md
```

Tant que la branche `amina-france-travail` n'est pas intégrée, le JSON n'est pas présent sur cette branche. Pour le récupérer sans le modifier :

```bash
git fetch origin
git show "origin/amina-france-travail:data/raw/offres_france_travail_public_2026-10-31_13-43.json" > data/raw/offres_france_travail_public_2026-10-31_13-43.json
```

## Récupérer les tables INSEE

Le script déduit le département et la région de chaque offre grâce au **Code officiel géographique (COG) 2026** de l'INSEE. Ces fichiers ne sont pas dans le dépôt.

1. Ouvrir la [page de téléchargement du COG 2026](https://www.insee.fr/fr/information/8740222).
2. Télécharger les trois fichiers CSV : `v_commune_2026.csv`, `v_departement_2026.csv`, `v_region_2026.csv`.
3. Les placer dans `data/raw/insee/` en conservant exactement leurs noms.

## Lancer le script

Il faut Python avec **pandas**. Depuis la racine du dépôt :

```bash
python -m pip install pandas
python src/france_travail/nettoyage.py                                # vraies offres
python src/france_travail/nettoyage.py data/raw/offres_fictives.csv   # fichier de test
```

Les deux commandes écrivent dans les mêmes fichiers de sortie : relancer la première après un test.

## Ce que fait le script

Les règles détaillées et leur justification sont dans le dictionnaire de données. Dans l'ordre :

1. **Lecture** : conversion du JSON au format du dictionnaire (partie `offres_uniques`, plus `date_collecte` et `source` lues dans `metadata`). Seules les colonnes du dictionnaire sont gardées : les champs de contact ne sont pas repris.
2. **Typage** des dates (en UTC) et du booléen `alternance`.
3. **Offres incomplètes** : un champ obligatoire manquant → offre retirée. Fait avant le dédoublonnage pour ne jamais garder une version incomplète à la place d'une version complète.
4. **Périmètre contrat** : `type_contrat` devient « alternance » si `alternance` = vrai ; CDI et CDD sont gardés ; le reste est retiré (ex. intérim). Les **stages** sont retirés d'après le titre, car l'API les classe en CDI ou CDD.
5. **Fenêtre d'un an** : seules les offres créées dans l'année précédant la date de référence sont gardées.
6. **Géographie** : département (code) et région (nom) déduits du code commune, sinon du libellé du lieu (ex. « 75 - Paris »).
7. **Doublons exacts** : même `job_id` → on garde la version la plus récente (`date_actualisation`, ou `date_creation` si elle manque, puis `date_collecte`).
8. **Doublons probables** : même titre + entreprise + description → signalés dans `doublon_suspect`, non supprimés.
9. **Métiers à vérifier** : code ROME hors du cœur du périmètre → signalé dans `metier_a_verifier`, non supprimé.
10. **Écriture** des offres propres, des offres retirées (avec leur motif) et affichage d'un rapport.

## Où sont appliqués les filtres du périmètre

| Filtre | Où | Détail |
| --- | --- | --- |
| Métiers Data/IA | **Collecte** (mots-clés de la requête API) puis **nettoyage** (étape 9) | Le nettoyage signale sans retirer, avec la liste `CODES_ROME_PERIMETRE` de `nettoyage.py`. Cette liste reste à valider par l'équipe. |
| Contrats CDI / CDD / alternance | **Collecte** puis **nettoyage** (étape 4) | Stages retirés d'après le titre. |
| Fenêtre d'un an | **Collecte** (`minCreationDate`, `maxCreationDate`) puis **nettoyage** (étape 5), sur `date_creation` | **Date de référence** = `date_collecte` la plus récente du fichier, ou une date fixe dans `DATE_REFERENCE`. Fenêtre = [référence − 1 an ; référence]. |

## Résultat sur les vraies offres

Date de référence : 2026-10-31, fenêtre du 2025-10-31 au 2026-10-31.

| Étape | Résultat |
| --- | --- |
| Offres lues | 615 |
| Stages retirés | 18 |
| Autres offres retirées (champ manquant, contrat, fenêtre, doublon exact) | 0 |
| **Offres finales** | **597** (525 CDI, 38 CDD, 34 alternance) |
| Doublons probables signalés | 30 offres |
| Métiers à vérifier signalés | 103 offres |

Colonnes facultatives les moins renseignées dans les 597 offres :

| Colonne | Offres renseignées |
| --- | --- |
| `formation` | 60 |
| `competences` | 114 |
| `salaire` | 235 |
| `entreprise` | 397 |
| `commune` | 537 |
| `departement`, `region` | 578 |

## Limites à connaître

- **Période réelle :** les offres vont du 07/05/2026 au 31/10/2026. L'API ne renvoie que les offres encore en ligne : la fenêtre d'un an ne garantit pas une année complète de données.
- **`metier_a_verifier` reste approximatif :** le code ROME signale aussi de bonnes offres (ex. « IA - ML Engineer ») et ne garantit pas que les 494 autres sont dans le périmètre.
- **Compétences :** le champ structuré est rempli pour seulement 114 offres. La phase 4 devra s'appuyer sur `description`.
- **`experience` :** la valeur vient de l'API et peut contredire le titre (ex. « Consultant Senior » en « débutant »). Elle n'est pas corrigée.
- **19 offres sans département ni région :** 9 n'indiquent qu'une région, 9 sont à l'étranger (Luxembourg, Belgique) et 1 est à Nouméa, absente des tables INSEE utilisées.

## Vérification sur le fichier fictif

Le fichier `data/raw/offres_fictives.csv` contient un cas par règle. Résultat attendu : **18 offres lues, 11 offres finales**.

| Motif de retrait | Offres |
| --- | --- |
| Champ obligatoire manquant | FT011 (titre), FT014 (date_collecte) |
| Contrat hors périmètre | FT005 (intérim) |
| Stage hors périmètre | FT016 |
| Hors fenêtre d'un an | FT013 |
| Doublon exact | FT002, FT012 (ancienne version sans date d'actualisation) |

Doublons probables signalés : FT009, FT010. Cas de géographie : Corse (`2A004` → 2A), outre-mer (`97411` → 974), département lu dans le libellé (FT004 → 92), libellé sans code (FT015 → vide).

## Reste à faire

- Valider avec l'équipe la liste `CODES_ROME_PERIMETRE` et le sort des offres signalées dans `metier_a_verifier`.
- Décider du sort des offres à l'étranger.
