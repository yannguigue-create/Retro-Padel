import streamlit as st
import pandas as pd
import random

# ==========================
# CONFIGURATION PAGE
# ==========================
st.set_page_config(
    page_title="Tournoi de Padel - Retro Padel",
    page_icon="🎾",
    layout="wide"
)

# ==========================
# TITRE + LOGO
# ==========================
st.image("https://raw.githubusercontent.com/ton-repo/logo/main/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Tournoi de Padel - Retro Padel</h1>", unsafe_allow_html=True)
st.markdown("---")

# ==========================
# PARAMÈTRES DU TOURNOI
# ==========================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")
    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl\nJean Pierre\nBruce\nFranck\nRomain\nJules")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica\nCharlotte\nCelia\nRose\nSophie\nCaroline")

    nb_terrains = st.number_input("Nombre de terrains disponibles", min_value=1, max_value=10, value=4)

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

# ==========================
# SESSION STATE
# ==========================
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Sexe", "Points", "Jeux"])

# ==========================
# GÉNÉRATION D'UN ROUND
# ==========================
def generer_round(round_num, nb_terrains):
    random.shuffle(hommes)
    random.shuffle(femmes)
    equipes = list(zip(hommes, femmes))
    random.shuffle(equipes)

    matchs = []
    for i in range(0, len(equipes), 2):
        if i+1 < len(equipes):
            teamA = equipes[i][0] + " + " + equipes[i][1]
            teamB = equipes[i+1][0] + " + " + equipes[i+1][1]
            matchs.append((teamA, teamB))

    planning = []
    for i, (teamA, teamB) in enumerate(matchs, start=1):
        terrain = ((i - 1) % nb_terrains) + 1
        rotation = ((i - 1) // nb_terrains) + 1
        planning.append({
            "Round": round_num,
            "Match": i,
            "Terrain": terrain,
            "Rotation": rotation,
            "Équipe A": teamA,
            "Équipe B": teamB,
            "Score": ""
        })
    return planning

# ==========================
# MISE À JOUR CLASSEMENT
# ==========================
def maj_classement():
    data = []
    for r in st.session_state.rounds:
        for m in r:
            score = m["Score"]
            if score:
                try:
                    scA, scB = map(int, score.split("-"))
                except:
                    continue
                joueursA = m["Équipe A"].split(" + ")
                joueursB = m["Équipe B"].split(" + ")

                if scA > scB:
                    ptsA, ptsB = 3, 0.5
                elif scB > scA:
                    ptsA, ptsB = 0.5, 3
                else:
                    ptsA, ptsB = 1, 1

                for j in joueursA:
                    data.append([j, "H" if j in hommes else "F", ptsA, scA])
                for j in joueursB:
                    data.append([j, "H" if j in hommes else "F", ptsB, scB])

    df = pd.DataFrame(data, columns=["Joueur", "Sexe", "Points", "Jeux"])
    classement = df.groupby(["Joueur", "Sexe"]).sum().reset_index()
    classement = classement.sort_values(by=["Points", "Jeux"], ascending=False)
    st.session_state.classement = classement

# ==========================
# INTERFACE
# ==========================
st.subheader("🎲 Gestion des matchs")

if st.button("➕ Générer un nouveau round"):
    round_num = len(st.session_state.rounds) + 1
    new_round = generer_round(round_num, nb_terrains)
    st.session_state.rounds.append(new_round)

# AFFICHAGE DES ROUNDS
for r in st.session_state.rounds:
    st.markdown(f"## 🏟 Round {r[0]['Round']}")
    for rot in sorted(set([m["Rotation"] for m in r])):
        st.markdown(f"### 🔄 Rotation {rot}")
        cols = st.columns(nb_terrains)
        for t in range(1, nb_terrains+1):
            matchs_terrain = [m for m in r if m["Rotation"]==rot and m["Terrain"]==t]
            if matchs_terrain:
                match = matchs_terrain[0]
                with cols[t-1]:
                    st.write(f"**Terrain {t}**")
                    st.write(f"{match['Équipe A']} vs {match['Équipe B']}")
                    score = st.text_input(f"Score Round {match['Round']} Match {match['Match']}", match["Score"])
                    match["Score"] = score

# ==========================
# CLASSEMENT
# ==========================
if st.button("📊 Calculer le classement"):
    maj_classement()
    st.write("### Classement général")
    st.dataframe(st.session_state.classement)

# ==========================
# PHASES FINALES
# ==========================
def generer_phases_finales():
    if st.session_state.classement.empty:
        st.warning("⚠️ Calcule d'abord le classement avant de lancer les phases finales.")
        return
    qualifiés = list(st.session_state.classement.head(8)["Joueur"])

    st.write("## 🏆 Phases finales")
    st.write("### 1/4 de finale")
    quarts = [(qualifiés[i], qualifiés[-i-1]) for i in range(4)]
    for q in quarts:
        st.write(f"{q[0]} + {q[1]}")

    st.write("### 1/2 finales")
    st.write("🔜 Automatisation à compléter selon les vainqueurs des 1/4")

    st.write("### Finale")
    st.write("🔜 Automatisation à compléter selon les vainqueurs des 1/2")

if st.button("🏆 Lancer les phases finales"):
    generer_phases_finales()
