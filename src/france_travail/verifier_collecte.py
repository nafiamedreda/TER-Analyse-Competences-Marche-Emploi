import json


# Fichier à vérifier
FICHIER = "data/raw/offres_france_travail_2026-10-31_13-43.json"


# Champs importants pour le TER
CHAMPS_ATTENDUS = [
    "id",
    "intitule",
    "description",
    "dateCreation",
    "dateActualisation",
    "romeCode",
    "romeLibelle",
    "entreprise",
    "lieuTravail",
    "typeContrat",
    "experienceLibelle",
    "formations",
    "competences",
    "alternance"
]


# Lecture du JSON
with open(FICHIER, "r", encoding="utf-8") as f:
    data = json.load(f)


# On récupère la liste dédoublonnée
offres = data["offres_uniques"]


print("Nombre d'offres :", len(offres))
print()


# Vérification des champs
for champ in CHAMPS_ATTENDUS:

    nombre_present = sum(
        1
        for offre in offres
        if champ in offre and offre.get(champ) not in [None, "", []]
    )

    pourcentage = (
        nombre_present / len(offres)
    ) * 100

    print(
        f"{champ} : "
        f"{nombre_present}/{len(offres)} "
        f"({pourcentage:.1f} %)"
    )