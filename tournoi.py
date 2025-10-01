import streamlit as st
import pandas as pd
import random

# ================================
# PAGE CONFIGURATION
# ================================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ================================
# LOGO + TITRE
# ================================
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="350">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">
            🎾 Tournoi de Padel - Retro Padel
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ================================
# SIDEBAR PARAMÈTRES
# ================================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")

    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    st.markdown(f"👨 Hommes : **{len(hommes)}**")
    st.markdown(f"👩 Femmes : **{len(femmes)}**")
    st.markdown(f"🔢 Total joueurs : **{len(hommes) + len(femmes)}**")

    terrains = st.number_input("Nombre de terrains disponibles", 1, 10, 4)
    matchs_min = st.number_input("Nombre minimum de matchs par joueur", 1, 10, 4)

    if st.button("♻️ Reset Tournoi"):
        for key in ["rounds", "classement", "phases_finales"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Tournoi réinitialisé.")

# ================================
# INITIALISATION
# ================================
if "rounds" not in st.session_state:
    st.session_state.rounds = []

if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Points", "Jeux"])

if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = None

# ================================
# GÉNÉRATION D'UN ROUND
# ================================
def generer_round(hommes, femmes, terrains):
    random.shuffle(hommes)
    random.shuffle(femmes)

    matchs = []
    for i in range(min(terrains, len(hommes), len(femmes))):
        h1, h2 = random.sample(hommes, 2)
        f1, f2 = random.sample(femmes, 2)
        matchs.append(((h1, f1), (h2, f2)))
    return matchs

# ================================
# GESTION DES MATCHS
# ================================
st.subheader("🎲 Gestion des matchs")

if st.button("➕ Générer un nouveau round"):
    round_num = len(st.session_state.rounds) + 1
    new_round = generer_round(hommes, femmes, terrains)
    st.session_state.rounds.append(new_round)

# Affichage des rounds
for r, round_matchs in enumerate(st.session_state.rounds, 1):
    st.markdown(f"## 🏟️ Round {r}")
    for t, match in enumerate(round_matchs, 1):
        equipeA, equipeB = match
        score = st.text_input(f"Score Round {r} Terrain {t} ({equipeA[0]}+{equipeA[1]} vs {equipeB[0]}+{equipeB[1]})", key=f"R{r}T{t}")

# ================================
# CLASSEMENT GÉNÉRAL
# ================================
st.subheader("📊 Classement général")

if st.button("📑 Calculer le classement"):
    data = []
    for r, round_matchs in enumerate(st.session_state.rounds, 1):
        for t, match in enumerate(round_matchs, 1):
            score_key = f"R{r}T{t}"
            score = st.session_state.get(score_key, "")
            if not score or "-" not in score:
                continue

            equipeA, equipeB = match
            try:
                a, b = map(int, score.split("-"))
            except:
                continue

            if a > b:
                gagnants, perdants = equipeA, equipeB
            else:
                gagnants, perdants = equipeB, equipeA

            for joueur in gagnants:
                data.append([joueur, 3, a if gagnants == equipeA else b])
            for joueur in perdants:
                data.append([joueur, 1, b if perdants == equipeB else a])

    df = pd.DataFrame(data, columns=["Joueur", "Points", "Jeux"])
    st.session_state.classement = df.groupby("Joueur").sum().reset_index()
    st.session_state.classement = st.session_state.classement.sort_values(
        by=["Points", "Jeux"], ascending=[False, False]
    ).reset_index(drop=True)

st.dataframe(st.session_state.classement)

# ================================
# TOP 8 & PHASES FINALES
# ================================
if not st.session_state.classement.empty:
    st.subheader("🏅 Top 8 Hommes")
    top8_hommes = st.session_state.classement[st.session_state.classement["Joueur"].isin(hommes)].head(8)
    st.table(top8_hommes)

    st.subheader("🏅 Top 8 Femmes")
    top8_femmes = st.session_state.classement[st.session_state.classement["Joueur"].isin(femmes)].head(8)
    st.table(top8_femmes)

    if st.button("⚡ Générer phases finales"):
        st.session_state.phases_finales = {
            "round": "quarts",
            "matchs": {
                "quarts": [
                    (top8_hommes.iloc[0]["Joueur"], top8_hommes.iloc[7]["Joueur"]),
                    (top8_hommes.iloc[3]["Joueur"], top8_hommes.iloc[4]["Joueur"]),
                    (top8_hommes.iloc[1]["Joueur"], top8_hommes.iloc[6]["Joueur"]),
                    (top8_hommes.iloc[2]["Joueur"], top8_hommes.iloc[5]["Joueur"]),
                    (top8_femmes.iloc[0]["Joueur"], top8_femmes.iloc[7]["Joueur"]),
                    (top8_femmes.iloc[3]["Joueur"], top8_femmes.iloc[4]["Joueur"]),
                    (top8_femmes.iloc[1]["Joueur"], top8_femmes.iloc[6]["Joueur"]),
                    (top8_femmes.iloc[2]["Joueur"], top8_femmes.iloc[5]["Joueur"])
                ],
                "demis": [],
                "finale": []
            },
            "scores": {}
        }

# ================================
# AFFICHAGE PHASES FINALES
# ================================
if st.session_state.phases_finales:
    round_actuel = st.session_state.phases_finales["round"]
    matchs = st.session_state.phases_finales["matchs"][round_actuel]
    scores = st.session_state.phases_finales["scores"]

    st.subheader(f"🏆 {round_actuel.capitalize()} de finale")

    for i, match in enumerate(matchs, 1):
        joueurA, joueurB = match
        scores[f"{round_actuel}_{i}"] = st.text_input(
            f"{joueurA} vs {joueurB}", key=f"{round_actuel}_{i}"
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Revenir en arrière"):
            if round_actuel == "demis":
                st.session_state.phases_finales["round"] = "quarts"
            elif round_actuel == "finale":
                st.session_state.phases_finales["round"] = "demis"

    with col2:
        if st.button("➡️ Valider et passer à la suite"):
            if round_actuel == "quarts":
                st.session_state.phases_finales["round"] = "demis"
            elif round_actuel == "demis":
                st.session_state.phases_finales["round"] = "finale"
