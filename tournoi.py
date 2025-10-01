import streamlit as st
import pandas as pd
import random

# ==============================
# CONFIGURATION PAGE
# ==============================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ==============================
# LOGO + TITRE
# ==============================
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="300">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">
        🎾 Tournoi de Padel - Retro Padel
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# INIT SESSION STATE
# ==============================
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame()
if "finales" not in st.session_state:
    st.session_state.finales = []

# ==============================
# PARAMÈTRES DU TOURNOI
# ==============================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")

    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    st.markdown(f"👨 Hommes : {len(hommes)}")
    st.markdown(f"👩 Femmes : {len(femmes)}")
    st.markdown(f"🔢 Total joueurs : {len(hommes) + len(femmes)}")

    terrains = st.number_input("Nombre de terrains disponibles", 1, 10, 4)
    matchs_min = st.number_input("Nombre minimum de matchs par joueur", 1, 10, 4)

    if st.button("♻️ Reset Tournoi"):
        st.session_state.rounds = []
        st.session_state.classement = pd.DataFrame()
        st.session_state.finales = []
        st.success("Tournoi réinitialisé ✅")

# ==============================
# FONCTION GÉNÉRATION DE ROUND
# ==============================
def generer_round(hommes, femmes, terrains):
    joueurs = hommes + femmes
    random.shuffle(joueurs)
    round_matchs = []

    for t in range(terrains):
        if len(joueurs) < 4:
            break
        equipeA = [joueurs.pop(), joueurs.pop()]
        equipeB = [joueurs.pop(), joueurs.pop()]
        round_matchs.append((equipeA, equipeB))

    return round_matchs

# ==============================
# GESTION DES MATCHS
# ==============================
st.subheader("🎲 Gestion des matchs")

# Vérification quota minimum avant nouveau round
bloque = False
if not st.session_state.classement.empty:
    matchs_par_joueur = st.session_state.classement.copy()
    matchs_par_joueur["Matchs"] = (matchs_par_joueur["Points"] // 3) + (matchs_par_joueur["Points"] % 3 > 0).astype(int)
    if all(matchs_par_joueur["Matchs"] >= matchs_min):
        st.warning("✅ Tous les joueurs ont atteint le nombre minimum de matchs. Impossible de générer un nouveau round.")
        bloque = True

if not bloque and st.button("➕ Générer un nouveau round"):
    round_num = len(st.session_state.rounds) + 1
    new_round = generer_round(hommes, femmes, terrains)
    st.session_state.rounds.append(new_round)

# Affichage des matchs
for r, round_matchs in enumerate(st.session_state.rounds, 1):
    st.markdown(f"## 🏆 Round {r}")
    for t, match in enumerate(round_matchs, 1):
        equipeA, equipeB = match
        score_key = f"R{r}T{t}"
        st.text_input(
            f"{' + '.join(equipeA)} vs {' + '.join(equipeB)} (Score Round {r} Terrain {t})",
            key=score_key
        )

# ==============================
# CALCUL DU CLASSEMENT
# ==============================
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
                data.append([joueur, 3, max(a, b)])
            for joueur in perdants:
                data.append([joueur, 1, min(a, b)])

    df = pd.DataFrame(data, columns=["Joueur", "Points", "Jeux"])
    st.session_state.classement = df.groupby("Joueur").sum().reset_index()
    st.session_state.classement = st.session_state.classement.sort_values(
        by=["Points", "Jeux"], ascending=[False, False]
    ).reset_index(drop=True)

    # Ajout du rang
    st.session_state.classement.index = st.session_state.classement.index + 1
    st.session_state.classement.reset_index(inplace=True)
    st.session_state.classement.rename(columns={"index": "Rang"}, inplace=True)

# Affichage du classement
if not st.session_state.classement.empty:
    st.dataframe(st.session_state.classement)

    # Top 8 hommes
    st.subheader("👨 Top 8 Hommes")
    hommes_df = st.session_state.classement[st.session_state.classement["Joueur"].isin(hommes)]
    st.table(hommes_df.head(8))

    # Top 8 femmes
    st.subheader("👩 Top 8 Femmes")
    femmes_df = st.session_state.classement[st.session_state.classement["Joueur"].isin(femmes)]
    st.table(femmes_df.head(8))

# ==============================
# PHASES FINALES
# ==============================
st.subheader("⚡ Phases finales")

if st.button("⚡ Générer phases finales"):
    if not st.session_state.classement.empty:
        top8 = st.session_state.classement.head(8)["Joueur"].tolist()
        random.shuffle(top8)
        qf = [(top8[i], top8[i+1]) for i in range(0, 8, 2)]
        st.session_state.finales = {"Quarts": qf, "Demi": [], "Finale": []}

# Affichage des finales
if st.session_state.finales:
    if "Quarts" in st.session_state.finales:
        st.markdown("### 🏅 Quarts de finale")
        for i, match in enumerate(st.session_state.finales["Quarts"], 1):
            st.text_input(f"Quart {i} : {match[0]} vs {match[1]}", key=f"QF{i}")

    if "Demi" in st.session_state.finales and st.session_state.finales["Demi"]:
        st.markdown("### 🥈 Demi-finales")
        for i, match in enumerate(st.session_state.finales["Demi"], 1):
            st.text_input(f"Demi {i} : {match[0]} vs {match[1]}", key=f"DF{i}")

    if "Finale" in st.session_state.finales and st.session_state.finales["Finale"]:
        st.markdown("### 🥇 Finale")
        match = st.session_state.finales["Finale"][0]
        st.text_input(f"Finale : {match[0]} vs {match[1]}", key="F1")

    if st.button("↩️ Revenir en arrière"):
        st.session_state.finales = []
        st.warning("Retour en arrière effectué.")
