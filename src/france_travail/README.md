# Nettoyage des offres France Travail

## Objectif dans le TER

Transformer les offres d'emploi récupérées depuis France Travail en une base propre et structurée, conforme au dictionnaire de données (`data/processed/dictionnaire_donnees.md`). Cette base servira à l'analyse des données (phase 3) et à l'extraction des compétences (phase 4).

**État actuel :** l'accès à l'API France Travail n'est pas encore obtenu. Le script est donc développé et testé sur un fichier d'offres fictives (`data/raw/offres_fictives.csv`). Quand les vraies offres seront disponibles, une étape de conversion du JSON de l'API sera ajoutée au début du script ; les règles de nettoyage resteront les mêmes.

## Fichiers

```text
data/
  raw/
    offres_fictives.csv          # offres de test, avec cas pièges
    insee/                       # tables géographiques (à télécharger, voir ci-dessous)
      v_commune_2026.csv
      v_departement_2026.csv
      v_region_2026.csv
  processed/
    dictionnaire_donnees.md      # schéma de la base et règles de nettoyage
    offres_propres.csv           # généré par le script
    offres_retirees.csv          # généré : offres retirées + motif
src/
  france_travail/
    nettoyage.py
    README.md
```

## Récupérer les tables INSEE

Le script déduit le département et la région de chaque offre à partir du code commune, grâce au **Code officiel géographique (COG) 2026** de l'INSEE. Ces fichiers ne sont pas dans le dépôt.

1. Ouvrir la [page de téléchargement du COG 2026](https://www.insee.fr/fr/information/8740222).
2. Télécharger les trois fichiers CSV : `v_commune_2026.csv`, `v_departement_2026.csv`, `v_region_2026.csv`.
3. Les placer dans `data/raw/insee/` en conservant exactement leurs noms.

## Lancer le script

Il faut Python avec **pandas** :

```bash
python -m pip install pandas
python src/france_travail/nettoyage.py
```

Le script retrouve ses fichiers à partir de son propre emplacement : il peut être lancé depuis n'importe quel dossier.

## Ce que fait le script

Les règles détaillées et leur justification sont dans le dictionnaire de données. Dans l'ordre :

1. **Lecture** du fichier d'offres (tout en texte, pour garder les codes comme `01001` ou `2A004`).
2. **Typage** des dates et du booléen `alternance`.
3. **Offres incomplètes** : un champ obligatoire manquant → offre retirée. Fait avant le dédoublonnage pour ne jamais garder une version incomplète à la place d'une version complète.
4. **Périmètre contrat** : `type_contrat` devient « alternance » si `alternance` = vrai ; CDI et CDD sont gardés ; le reste est retiré (ex. intérim).
5. **Fenêtre d'un an** : seules les offres créées dans l'année précédant la date de référence sont gardées.
6. **Géographie** : département (code) et région (nom) déduits du code commune.
7. **Doublons exacts** : même `job_id` → on garde la version la plus récente (`date_actualisation`, ou `date_creation` si elle manque, puis `date_collecte`).
8. **Doublons probables** : même titre + entreprise + description → signalés dans `doublon_suspect`, non supprimés.
9. **Écriture** des offres propres, des offres retirées (avec leur motif) et affichage d'un rapport.

## Où sont appliqués les filtres du périmètre

| Filtre | Où | Détail |
| --- | --- | --- |
| Métiers Data/IA | **À la collecte (P1)**, par les codes ROME / mots-clés de la requête API | Contrôle de sécurité possible dans le nettoyage : remplir `CODES_ROME_PERIMETRE` dans `nettoyage.py` avec la liste validée. Vide pour l'instant = pas de filtre. |
| Contrats CDI / CDD / alternance | **Nettoyage** (étape 4) | Peut aussi être restreint à la collecte. |
| Fenêtre d'un an | **Nettoyage** (étape 5), sur `date_creation` | **Date de référence** = `date_collecte` la plus récente du fichier, ou une date fixe dans `DATE_REFERENCE`. Fenêtre = [référence − 1 an ; référence]. |

L'API ne renvoie que les offres **actives** : pour couvrir une année complète, il faudra collecter régulièrement, puis appliquer la fenêtre sur l'ensemble des collectes.

## Résultat sur le fichier fictif

Date de référence : 2026-10-15, fenêtre du 2025-10-15 au 2026-10-15.

| Étape | Résultat |
| --- | --- |
| Offres lues | 16 |
| Champ obligatoire manquant | 2 (FT011 : titre ; FT014 : date_collecte) |
| Contrat hors périmètre | 1 (FT005, intérim) |
| Hors fenêtre d'un an | 1 (FT013, créée en juin 2025) |
| Doublons exacts | 2 (FT002 ; FT012 dont l'ancienne version n'a pas de date d'actualisation) |
| **Offres finales** | **10** |
| Doublons suspects | FT009, FT010 |

Les cas particuliers de géographie sont vérifiés : Corse (`2A004` → 2A, Corse), outre-mer (`97411` → 974, La Réunion), commune manquante (département et région laissés vides).

## Reste à faire

- Remplir la colonne « source API » du dictionnaire à partir d'une vraie réponse de l'API.
- Ajouter la conversion du JSON de l'API vers le format du dictionnaire.
- Remplir `CODES_ROME_PERIMETRE` avec la liste des métiers validée par l'équipe.
- Lancer le script sur les vraies offres collectées.
