"""
Nettoyage des offres France Travail.

Lit un fichier d'offres, applique les règles du dictionnaire de données
(data/processed/dictionnaire_donnees.md) et écrit :
- un fichier d'offres propres ;
- un fichier des offres retirées, avec le motif de chaque retrait.

Utilisation (depuis la racine du dépôt) :
    python src/france_travail/nettoyage.py
"""

from pathlib import Path

import pandas as pd

# --- Chemins ---------------------------------------------------------------
DOSSIER = Path(__file__).resolve().parents[2]
FICHIER_ENTREE = DOSSIER / "data" / "raw" / "offres_fictives.csv"
FICHIER_SORTIE = DOSSIER / "data" / "processed" / "offres_propres.csv"
FICHIER_RETIREES = DOSSIER / "data" / "processed" / "offres_retirees.csv"
DOSSIER_INSEE = DOSSIER / "data" / "raw" / "insee"

# --- Règles du dictionnaire ------------------------------------------------
# Doit correspondre exactement aux colonnes « obligatoire = oui »
# des sections 1 et 2 du dictionnaire de données.
COLONNES_OBLIGATOIRES = ["job_id", "date_creation", "titre", "description",
                         "type_contrat", "date_collecte", "source"]
CONTRATS_GARDES = ["CDI", "CDD"]
COLONNES_DATES = ["date_creation", "date_actualisation", "date_collecte"]
COLONNES_DOUBLON_PROBABLE = ["titre", "entreprise", "description"]

# Fenêtre temporelle : on garde les offres créées dans l'année qui précède
# la date de référence. Si DATE_REFERENCE vaut None, on prend la date de
# collecte la plus récente du fichier.
DATE_REFERENCE = None
DUREE_FENETRE = pd.DateOffset(years=1)

# Filtre métiers : codes ROME du périmètre Data/IA. Le filtre principal est
# fait à la collecte (P1) ; ici c'est un contrôle de sécurité. Liste vide =
# pas de filtre, en attendant la liste validée par l'équipe.
CODES_ROME_PERIMETRE = []


def charger(chemin):
    """1. Lire le fichier. Tout est lu en texte pour ne pas perdre
    les zéros au début des codes (ex. commune 01001)."""
    return pd.read_csv(chemin, dtype=str, keep_default_na=False, na_values=[""])


def typer(df):
    """2. Donner le bon type aux colonnes : dates et booléen."""
    for col in COLONNES_DATES:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["alternance"] = df["alternance"].str.lower().map({"true": True, "false": False})
    return df


def retirer(df, a_retirer, motif, retirees):
    """Retire les lignes indiquées et les ajoute aux offres retirées avec leur motif."""
    sortie = df[a_retirer].assign(motif=motif)
    retirees.append(sortie)
    return df[~a_retirer].copy()


def motif_incomplet(ligne):
    manquants = [c for c in COLONNES_OBLIGATOIRES if pd.isna(ligne[c])]
    return "champ obligatoire manquant : " + ", ".join(manquants)


def retirer_incompletes(df, retirees):
    """3. Une offre à laquelle il manque un champ obligatoire est retirée.
    Fait avant le dédoublonnage, pour ne jamais garder une version
    incomplète à la place d'une version complète."""
    incomplete = df[COLONNES_OBLIGATOIRES].isna().any(axis=1)
    sortie = df[incomplete].copy()
    sortie["motif"] = sortie.apply(motif_incomplet, axis=1)
    retirees.append(sortie)
    return df[~incomplete].copy()


def appliquer_perimetre(df, retirees):
    """4. Type de contrat : alternance si alternance = vrai,
    CDI / CDD gardés, tout le reste exclu (ex. intérim)."""
    df.loc[df["alternance"] == True, "type_contrat"] = "alternance"
    hors_contrat = ~df["type_contrat"].isin(CONTRATS_GARDES + ["alternance"])
    df = retirer(df, hors_contrat, "contrat hors périmètre", retirees)

    if CODES_ROME_PERIMETRE:
        hors_metier = ~df["code_rome"].isin(CODES_ROME_PERIMETRE)
        df = retirer(df, hors_metier, "métier hors périmètre", retirees)
    return df


def appliquer_fenetre(df, retirees):
    """5. Fenêtre d'un an avant la date de référence (sur date_creation)."""
    reference = pd.Timestamp(DATE_REFERENCE) if DATE_REFERENCE else df["date_collecte"].max()
    debut = reference - DUREE_FENETRE
    hors_fenetre = (df["date_creation"] < debut) | (df["date_creation"] > reference)
    return retirer(df, hors_fenetre, "hors fenêtre d'un an", retirees), debut, reference


def ajouter_geographie(df):
    """6. Déduire département et région à partir du code commune (table INSEE)."""
    communes = pd.read_csv(DOSSIER_INSEE / "v_commune_2026.csv", dtype=str)
    regions = pd.read_csv(DOSSIER_INSEE / "v_region_2026.csv", dtype=str)

    # Les communes déléguées / associées n'ont pas de département :
    # on reprend celui de leur commune de rattachement (COMPARENT).
    infos = communes.set_index("COM")[["DEP", "REG"]]
    infos = infos[~infos.index.duplicated()]
    sans_dep = communes["DEP"].isna() & communes["COMPARENT"].notna()
    for _, ligne in communes[sans_dep].iterrows():
        if ligne["COMPARENT"] in infos.index:
            infos.loc[ligne["COM"]] = infos.loc[ligne["COMPARENT"]]

    nom_region = regions.set_index("REG")["LIBELLE"]
    df["departement"] = df["commune"].map(infos["DEP"])
    df["region"] = df["commune"].map(infos["REG"]).map(nom_region)
    return df


def retirer_doublons_exacts(df, retirees):
    """7. Même job_id : on garde la version la plus récente.
    Date utilisée : date_actualisation, ou date_creation si elle manque,
    puis date_collecte pour départager deux versions de même date."""
    df["_date_version"] = df["date_actualisation"].fillna(df["date_creation"])
    df = df.sort_values(["job_id", "_date_version", "date_collecte"])
    doublon = df.duplicated("job_id", keep="last")
    df = retirer(df, doublon, "doublon exact (version plus ancienne)", retirees)
    for r in retirees:
        r.drop(columns="_date_version", errors="ignore", inplace=True)
    return df.drop(columns="_date_version")


def signaler_doublons_probables(df):
    """8. Même titre + entreprise + description : on signale, on ne supprime pas."""
    df["doublon_suspect"] = df.duplicated(COLONNES_DOUBLON_PROBABLE, keep=False)
    return df


def main():
    df = charger(FICHIER_ENTREE)
    nb_initial = len(df)
    retirees = []

    df = typer(df)
    df = retirer_incompletes(df, retirees)
    df = appliquer_perimetre(df, retirees)
    df, debut, reference = appliquer_fenetre(df, retirees)
    df = ajouter_geographie(df)
    df = retirer_doublons_exacts(df, retirees)
    df = signaler_doublons_probables(df)

    retirees = pd.concat(retirees)
    df.to_csv(FICHIER_SORTIE, index=False)
    retirees.to_csv(FICHIER_RETIREES, index=False)

    # --- 9. Petit rapport ---------------------------------------------------
    print(f"Offres lues      : {nb_initial}")
    print(f"Fenêtre retenue  : du {debut:%Y-%m-%d} au {reference:%Y-%m-%d} (date de référence)")
    if not CODES_ROME_PERIMETRE:
        print("Filtre métiers   : non appliqué ici (liste de codes ROME vide)")
    print(f"Offres retirées  : {len(retirees)}")
    for _, l in retirees.iterrows():
        print(f"  - {l['job_id']} : {l['motif']}")
    print(f"Offres finales   : {len(df)}")
    print(f"Doublons suspects: {list(df.loc[df['doublon_suspect'], 'job_id'])}")
    print("\nValeurs manquantes par colonne :")
    print(df.isna().sum()[lambda s: s > 0].to_string())
    print(f"\nFichiers écrits : {FICHIER_SORTIE.name}, {FICHIER_RETIREES.name}")


if __name__ == "__main__":
    main()
