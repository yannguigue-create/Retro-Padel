import streamlit as st
import pandas as pd
import random

# ----------------------------
# INITIALISATION
# ----------------------------
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "matchs_joues" not in st.session_state:
    st.session_state.matchs_joues = {}

# ----------------------------
# RESET TOURNOI
# ----------------------------
def reset_tournoi():
    st.session_state.joueurs = {}
    st.session_state.rounds = []
    st.session_state.matchs_joues = {}

# ----------------------------
# MAJ CLASSEMENT
# ----------------------------
def maj_classement(matchs, scores):
    for i, ((team1, team2), score) in enumerate(zip(matchs, scores)):
        if not score:
            continue
        try:
            s1, s2 = map(int, score.split("-"))
        except:
            continue

        if s1 > s2:
            gagnants, perdants, jeux_g, jeux_p = team1, team2, s1, s2
        else:
            gagnants, perdants, jeux_g, jeux_p = team2, team1, s2, s1

        # Mise à jour des stats
        for j in gagnants:
            st.session_state.joueurs[j]["Points"] += 3
            st.session_state.joueurs[j]["Jeux"] += jeux_g
            st.session_state.joueurs[j]["Matchs"] += 1
        for j in perdants:
            st.session_state.joueurs[j]["Points"] += 1
            st.session_state.joueurs[j]["Jeux"] += jeux_p
            st.session_state.joueurs[j]["Matchs"] += 1

        # Bonus 0.1 point par jeu marqué
        for j in team1 + team2:
            if j in gagnants:
                st.session_state.joueurs[j]["Points"] += jeux_g * 0.1
            else:
                st.session_state.joueurs[j]["Points"] += jeux_p * 0.1

# ----------------------------
# GÉNÉRATION DES ROUNDS
# ----------------------------
def generer_round(hommes, femmes, terrains, max_matchs):
    joueurs = hommes + femmes
    random.shuffle(joueurs)

    matchs = []
    dispo = [j for j in joueurs if st.session_state.joueurs.get(j, {"Matchs": 0})["Matchs"] < max_matchs]

    while len(dispo) >= 4 and len(matchs) < terrains:
        team1 = [dispo.pop(), dispo.pop()]
        team2 = [dispo.pop(), dispo.pop()]
        matchs.append((team1, team2))

    # 🔹 Formatage clair pour affichage
    matchs_formates = [(f"{a} + {b}", f"{c} + {d}") for (a, b), (c, d) in matchs]
    return matchs_formates

# ----------------------------
# AFFICHAGE CLASSEMENT
# ----------------------------
def afficher_classement():
    if not st.session_state.joueurs:
        return
    df = pd.DataFrame(st.session_state.joueurs).T
    df.index.name = "Joueur"
    df = df.reset_index()
    df["Points"] = df["Points"].apply(lambda x: round(x, 1))
    df["Jeux"] = df["Jeux"].apply(lambda x: round(x, 1))
    df = df.sort_values(by=["Points", "Jeux"], ascending=[False, False])
    df.insert(0, "Rang", range(1, len(df) + 1))
    st.subheader("🏅 Classement Général")
    st.table(df)

# ----------------------------
# INTERFACE
# ----------------------------
st.image("https://github.com/yannguigue-create/Retro-Padel/blob/bd45ea0f881e79db3d14fce6ef93f7190f1a987a/logo_retro_padel.png?raw=true", width=300)
st.title("🎾 Tournoi de Padel - Rétro Padel")

st.sidebar.header("⚙️ Paramètres du tournoi")
hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

st.sidebar.markdown(f"👨 Hommes : {len(hommes)}")
st.sidebar.markdown(f"👩 Femmes : {len(femmes)}")
st.sidebar.markdown(f"🎾 Total joueurs : {len(hommes) + len(femmes)}")

terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

if st.sidebar.button("🔄 Reset Tournoi"):
    reset_tournoi()
    st.success("Tournoi réinitialisé !")

# Initialisation joueurs
for j in hommes + femmes:
    if j not in st.session_state.joueurs:
        st.session_state.joueurs[j] = {"Points": 0, "Jeux": 0, "Matchs": 0}

# ----------------------------
# GESTION DES ROUNDS
# ----------------------------
st.header("🏆 Rounds")

if st.button("🎲 Générer un nouveau round"):
    round_num = len(st.session_state.rounds) + 1
    matchs = generer_round(hommes, femmes, terrains, max_matchs)
    st.session_state.rounds.append((round_num, matchs))
    st.success(f"Round {round_num} généré !")

for round_num, matchs in st.session_state.rounds:
    st.subheader(f"🏆 Round {round_num}")
    scores = []
    for i, (t1, t2) in enumerate(matchs):
        score = st.text_input(f"{t1} vs {t2} (Score Round {round_num} Terrain {i+1})")
        scores.append(score)
    if st.button(f"📊 Calculer le classement Round {round_num}", key=f"cl_{round_num}"):
        maj_classement(matchs, scores)

# ----------------------------
# CLASSEMENT
# ----------------------------
afficher_classement()
