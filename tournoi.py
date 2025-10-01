import streamlit as st
import pandas as pd
import random

# ==============================
# CONFIGURATION
# ==============================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ==============================
# INITIALISATION
# ==============================
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}

# ==============================
# LOGO + TITRE
# ==============================
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="250">
        <h1 style="color:#1E3A8A;">🎾 Tournoi de Padel - Retro Padel</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# PARAMÈTRES TOURNOI
# ==============================
st.sidebar.header("⚙️ Paramètres du tournoi")
hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

st.sidebar.markdown(f"👨 Hommes : {len(hommes)}")
st.sidebar.markdown(f"👩 Femmes : {len(femmes)}")
st.sidebar.markdown(f"🧑‍🤝‍🧑 Total joueurs : {len(hommes) + len(femmes)}")

# ==============================
# RESET TOURNOI
# ==============================
if st.sidebar.button("♻️ Reset Tournoi"):
    st.session_state.joueurs = {}
    st.session_state.rounds = []
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    st.success("Tournoi réinitialisé ✅")

# ==============================
# INITIALISATION JOUEURS
# ==============================
for joueur in hommes + femmes:
    if joueur not in st.session_state.joueurs:
        st.session_state.joueurs[joueur] = {"points": 0, "jeux": 0, "matchs": 0}

# ==============================
# FONCTIONS UTILITAIRES
# ==============================
def generer_round():
    joueurs_disponibles = [j for j, stats in st.session_state.joueurs.items() if stats["matchs"] < max_matchs]
    if len(joueurs_disponibles) < 4:
        st.warning("Pas assez de joueurs disponibles pour générer un nouveau round.")
        return

    random.shuffle(joueurs_disponibles)
    matchs = []
    for i in range(0, min(len(joueurs_disponibles), nb_terrains*4), 4):
        matchs.append(joueurs_disponibles[i:i+4])
        for j in joueurs_disponibles[i:i+4]:
            st.session_state.joueurs[j]["matchs"] += 1

    st.session_state.rounds.append(matchs)
    st.success(f"Round {len(st.session_state.rounds)} généré !")

def mettre_a_jour_scores(round_index, terrain_index, score_A, score_B):
    match = st.session_state.rounds[round_index][terrain_index]
    if len(match) != 4:
        return

    equipe_A, equipe_B = match[:2], match[2:]
    jeux_A, jeux_B = score_A, score_B

    for j in equipe_A:
        st.session_state.joueurs[j]["jeux"] += jeux_A
    for j in equipe_B:
        st.session_state.joueurs[j]["jeux"] += jeux_B

    if jeux_A > jeux_B:
        for j in equipe_A:
            st.session_state.joueurs[j]["points"] += 3
    elif jeux_B > jeux_A:
        for j in equipe_B:
            st.session_state.joueurs[j]["points"] += 3
    else:
        for j in equipe_A + equipe_B:
            st.session_state.joueurs[j]["points"] += 1

def classement_general():
    df = pd.DataFrame([
        {"Joueur": j, "Points": s["points"], "Jeux": s["jeux"], "Matchs": s["matchs"]}
        for j, s in st.session_state.joueurs.items()
    ])
    return df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)

# ==============================
# MATCHS
# ==============================
st.subheader("🏆 Gestion des matchs")
if st.button("➕ Générer un nouveau round"):
    generer_round()

for i, round in enumerate(st.session_state.rounds, 1):
    st.markdown(f"### 🏅 Round {i}")
    for t, match in enumerate(round, 1):
        st.write(f"{' + '.join(match[:2])} vs {' + '.join(match[2:])} (Score Round {i} Terrain {t})")
        score = st.text_input(f"Score Round {i} Terrain {t}", key=f"score_{i}_{t}")
        if score:
            try:
                sA, sB = map(int, score.split("-"))
                mettre_a_jour_scores(i-1, t-1, sA, sB)
            except:
                st.error("Format attendu : X-Y")

# ==============================
# CLASSEMENT GÉNÉRAL
# ==============================
st.subheader("🥇 Classement Général")
st.dataframe(classement_general())

# ==============================
# PHASES FINALES
# ==============================
st.subheader("🏆 Phases Finales")

if st.button("⚡ Générer phases finales"):
    classement = classement_general()
    hommes_top = [h for h in classement["Joueur"] if h in hommes][:8]
    femmes_top = [f for f in classement["Joueur"] if f in femmes][:8]

    st.session_state.phases_finales["quarts"] = []
    random.shuffle(hommes_top)
    random.shuffle(femmes_top)
    for i in range(4):
        equipe_A = [hommes_top[i], femmes_top[i]]
        equipe_B = [hommes_top[-(i+1)], femmes_top[-(i+1)]]
        st.session_state.phases_finales["quarts"].append((equipe_A, equipe_B))

# Affichage des quarts
if st.session_state.phases_finales["quarts"]:
    st.markdown("### Quarts de finale")
    for idx, (eqA, eqB) in enumerate(st.session_state.phases_finales["quarts"], 1):
        st.write(f"Match {idx} : {' + '.join(eqA)} vs {' + '.join(eqB)}")
