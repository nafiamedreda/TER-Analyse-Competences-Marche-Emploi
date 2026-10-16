"""
Nettoyage des offres France Travail.

Lit un fichier d'offres, applique les règles du dictionnaire de données
(data/processed/dictionnaire_donnees.md) et écrit un fichier propre.

Utilisation (depuis le dossier projetTER) :
    python src/france_travail/nettoyage.py
"""

from pathlib import Path

import pandas as pd

# --- Chemins ---------------------------------------------------------------
DOSSIER = Path(__file__).resolve().parents[2]
FICHIER_ENTREE = DOSSIER / "data" / "raw" / "offres_fictives.csv"
FICHIER_SORTIE = DOSSIER / "data" / "processed" / "offres_propres.csv"
DOSSIER_INSEE = DOSSIER / "data" / "raw" / "insee"

# --- Règles du dictionnaire ------------------------------------------------
COLONNES_OBLIGATOIRES = ["job_id", "date_creation", "titre", "description", "type_contrat"]
CONTRATS_GARDES = ["CDI", "CDD"]
COLONNES_DATES = ["date_creation", "date_actualisation", "date_collecte"]
COLONNES_DOUBLON_PROBABLE = ["titre", "entreprise", "description"]


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


def appliquer_perimetre(df):
    """3. Type de contrat : alternance si alternance = vrai,
    CDI / CDD gardés, tout le reste exclu (ex. intérim)."""
    df.loc[df["alternance"] == True, "type_contrat"] = "alternance"
    dans_perimetre = df["type_contrat"].isin(CONTRATS_GARDES + ["alternance"])
    exclues = df[~dans_perimetre]
    return df[dans_perimetre].copy(), exclues


def ajouter_geographie(df):
    """4. Déduire département et région à partir du code commune (table INSEE)."""
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


def supprimer_doublons_exacts(df):
    """5. Même job_id : on garde la version la plus récente."""
    avant = len(df)
    df = df.sort_values("date_actualisation").drop_duplicates("job_id", keep="last")
    return df.sort_values("job_id"), avant - len(df)


def supprimer_incompletes(df):
    """6. Une offre à laquelle il manque un champ obligatoire est supprimée."""
    complete = df[COLONNES_OBLIGATOIRES].notna().all(axis=1)
    return df[complete].copy(), df[~complete]


def signaler_doublons_probables(df):
    """7. Même titre + entreprise + description : on signale, on ne supprime pas."""
    df["doublon_suspect"] = df.duplicated(COLONNES_DOUBLON_PROBABLE, keep=False)
    return df


def main():
    df = charger(FICHIER_ENTREE)
    nb_initial = len(df)

    df = typer(df)
    df, exclues = appliquer_perimetre(df)
    df = ajouter_geographie(df)
    df, nb_doublons = supprimer_doublons_exacts(df)
    df, incompletes = supprimer_incompletes(df)
    df = signaler_doublons_probables(df)

    df.to_csv(FICHIER_SORTIE, index=False)

    # --- 8. Petit rapport ---------------------------------------------------
    print(f"Offres lues            : {nb_initial}")
    print(f"Hors périmètre exclues : {len(exclues)} {list(exclues['job_id'])}")
    print(f"Doublons exacts retirés: {nb_doublons}")
    print(f"Incomplètes supprimées : {len(incompletes)} {list(incompletes['job_id'])}")
    print(f"Offres finales         : {len(df)}")
    print(f"Doublons suspects      : {list(df.loc[df['doublon_suspect'], 'job_id'])}")
    print("\nValeurs manquantes par colonne :")
    print(df.isna().sum()[lambda s: s > 0].to_string())
    print(f"\nFichier écrit : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
