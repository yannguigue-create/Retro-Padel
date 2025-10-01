import streamlit as st
import pandas as pd
import random

# ==========================
# CONFIG PAGE
# ==========================
st.set_page_config(
    page_title="Tournoi de Padel - Retro Padel",
    page_icon="🎾",
    layout="wide"
)

# ==========================
# LOGO + TITRE
# ==========================
# Mets ton logo sur GitHub (ex: repo/images/logo.png) et mets le bon lien RAW ci-dessous
st.image("https://raw.githubusercontent.com/yannguigue-creer/Retro-Padel/main/logo.png", width=300)

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Tournoi de Padel - Retro Padel</h1>", unsafe_allow_html=True)
st.markdown("---")

# ==========================
# PARAMÈTRES TOURNOI
# ==========================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")

    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    # Transformation en liste
    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    # Compteurs
    nb_h = len(hommes)
    nb_f = len(femmes)
    nb_total = nb_h + nb_f

    st.markdown(f"👨 Hommes : **{nb_h}**")
    st.markdown(f"👩 Femmes : **{nb_f}**")
    st.markdown(f"🔢 Total joueurs : **{nb_total}**")

    nb_terrains = st.number_input("Nombre de terrains disponibles", min_value=1, max_value=10, value=4)
    nb_min_matchs = st.number_input("Nombre minimum de matchs par joueur", min_value=1, max_value=10, value=4)

    reset = st.button("♻️ Reset Tournoi")



    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

# ==========================
# SESSION STATE
# ==========================
if "rounds" not in st.session_state or reset:
    st.session_state.rounds = []
if "classement" not in st.session_state or reset:
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Sexe", "Points", "Jeux"])
if "match_count" not in st.session_state or reset:
    st.session_state.match_count = {j: 0 for j in hommes + femmes}

# ==========================
# GÉNÉRATION D'UN ROUND
# ==========================
def generer_round(round_num, nb_terrains):
    joueurs_dispo = [(h, "H") for h in hommes] + [(f, "F") for f in femmes]
    random.shuffle(joueurs_dispo)
    joueurs_dispo.sort(key=lambda x: st.session_state.match_count[x[0]])

    equipes = []
    while len(joueurs_dispo) >= 2:
        h = next((j for j in joueurs_dispo if j[1] == "H"), None)
        f = next((j for j in joueurs_dispo if j[1] == "F"), None)
        if not h or not f:
            break
        equipes.append((h[0], f[0]))
        joueurs_dispo.remove(h)
        joueurs_dispo.remove(f)

    random.shuffle(equipes)

    matchs = []
    for i in range(0, len(equipes), 2):
        if i+1 < len(equipes):
            teamA = equipes[i][0] + " + " + equipes[i][1]
            teamB = equipes[i+1][0] + " + " + equipes[i+1][1]
            matchs.append((teamA, teamB))
            for j in [equipes[i][0], equipes[i][1], equipes[i+1][0], equipes[i+1][1]]:
                st.session_state.match_count[j] += 1

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
# CLASSEMENT
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
# CLASSEMENT + TOP 8
# ==========================
if st.button("📊 Calculer le classement"):
    maj_classement()
    st.write("### Classement général")
    st.dataframe(st.session_state.classement)

    top_h = st.session_state.classement[st.session_state.classement["Sexe"]=="H"].head(8)
    top_f = st.session_state.classement[st.session_state.classement["Sexe"]=="F"].head(8)

    col1, col2 = st.columns(2)
    with col1:
        st.write("🏅 Top 8 Hommes")
        st.dataframe(top_h)
    with col2:
        st.write("🏅 Top 8 Femmes")
        st.dataframe(top_f)


