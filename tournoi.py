import streamlit as st
import pandas as pd
import random

# ==============================
# PAGE DE CONFIGURATION
# ==============================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ==============================
# INITIALISATION SESSION
# ==============================
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}

# ==============================
# RESET
# ==============================
def reset_tournoi():
    st.session_state.rounds = []
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.joueurs = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    st.success("♻️ Tournoi réinitialisé !")

def reset_phases():
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    st.success("♻️ Phases finales réinitialisées !")

# ==============================
# HEADER AVEC LOGO
# ==============================
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="250">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">🎾 Tournoi de Padel - Rétro Padel</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# BARRE LATÉRALE
# ==============================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]
joueurs = hommes + femmes

st.sidebar.markdown(f"🧑 Hommes : {len(hommes)}")
st.sidebar.markdown(f"👩 Femmes : {len(femmes)}")
st.sidebar.markdown(f"🔑 Total joueurs : {len(joueurs)}")

terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

if st.sidebar.button("♻️ Reset Tournoi"):
    reset_tournoi()

if st.sidebar.button("♻️ Reset Phases Finales"):
    reset_phases()

# ==============================
# FONCTION GÉNÉRATION ROUNDS
# ==============================
def compter_matchs(joueur):
    return sum([1 for m in st.session_state.matchs for team in m if joueur in team])

def generer_round():
    dispo = [j for j in joueurs if compter_matchs(j) < max_matchs]
    if len(dispo) < 4:
        st.warning("⚠️ Pas assez de joueurs disponibles pour générer un nouveau round.")
        return

    random.shuffle(dispo)
    round_matchs, round_scores = [], {}
    for t in range(terrains):
        if len(dispo) < 4:
            break
        team1 = [dispo.pop(), dispo.pop()]
        team2 = [dispo.pop(), dispo.pop()]
        round_matchs.append((team1, team2))
        round_scores[len(st.session_state.matchs) + len(round_matchs)] = None

    st.session_state.rounds.append(round_matchs)
    st.session_state.matchs.extend(round_matchs)
    st.session_state.scores.update(round_scores)
    st.success(f"✅ Round {len(st.session_state.rounds)} généré !")

# ==============================
# CLASSEMENT
# ==============================
def maj_classement():
    classement = {j: {"Points": 0, "Jeux": 0, "Matchs": 0} for j in joueurs}
    for mid, score in st.session_state.scores.items():
        if score:
            (t1, t2) = st.session_state.matchs[mid-1]
            s1, s2 = map(int, score.split("-"))

            for j in t1: 
                classement[j]["Jeux"] += s1
                classement[j]["Matchs"] += 1
            for j in t2: 
                classement[j]["Jeux"] += s2
                classement[j]["Matchs"] += 1

            if s1 > s2:
                for j in t1: classement[j]["Points"] += 3
            elif s2 > s1:
                for j in t2: classement[j]["Points"] += 3
            else:
                for j in t1+t2: classement[j]["Points"] += 1

    df = pd.DataFrame([
        {"Joueur": j, 
         "Points": round(v["Points"] + v["Jeux"]*0.1, 1), 
         "Jeux": v["Jeux"], 
         "Matchs": v["Matchs"]} 
        for j,v in classement.items()
    ])
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.insert(0, "Rang", df.index)
    return df

# ==============================
# AFFICHAGE ROUNDS
# ==============================
st.header("🏆 Rounds")
if st.button("🎲 Générer un nouveau round", disabled=all(compter_matchs(j) >= max_matchs for j in joueurs)):
    generer_round()

for ridx, matchs in enumerate(st.session_state.rounds, start=1):
    st.subheader(f"🏅 Round {ridx}")
    for midx, (team1, team2) in enumerate(matchs, start=1):
        key = len([m for r in st.session_state.rounds[:ridx-1] for m in r]) + midx
        score = st.text_input(f"{' + '.join(team1)} vs {' + '.join(team2)} (Score Round {ridx} Terrain {midx})",
                              value=st.session_state.scores.get(key, ""), key=f"score_{key}")
        st.session_state.scores[key] = score if score else None

if st.button("📊 Calculer le classement"):
    st.subheader("🥇 Classement Général")
    st.dataframe(maj_classement(), use_container_width=True)

# ==============================
# PHASES FINALES
# ==============================
st.header("🏆 Phases Finales")

if st.button("⚡ Générer Quarts de finale"):
    classement = maj_classement()
    top8 = classement.head(8)["Joueur"].tolist()
    random.shuffle(top8)
    st.session_state.phases_finales["quarts"] = [
        (top8[0], top8[7]),
        (top8[1], top8[6]),
        (top8[2], top8[5]),
        (top8[3], top8[4]),
    ]
    st.success("✅ Quarts générés !")

if st.session_state.phases_finales["quarts"]:
    st.subheader("Quarts de finale")
    for i, (j1, j2) in enumerate(st.session_state.phases_finales["quarts"], 1):
        st.text_input(f"{j1} vs {j2} (Score Quarts Match {i})", key=f"quart_{i}")
