import streamlit as st
import random
import pandas as pd

# ----------------------------
# VARIABLES GLOBALES
# ----------------------------
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = []
if "round" not in st.session_state:
    st.session_state.round = 0
if "finales" not in st.session_state:
    st.session_state.finales = {"quarts": [], "demis": [], "finale": []}

# ----------------------------
# AJOUT STATS
# ----------------------------
def ajouter_stats(joueur, jeux_gagnes, jeux_perdus):
    if joueur not in st.session_state.joueurs:
        st.session_state.joueurs[joueur] = {"Points": 0, "Jeux": 0, "Matchs": 0}

    st.session_state.joueurs[joueur]["Jeux"] += jeux_gagnes
    st.session_state.joueurs[joueur]["Matchs"] += 1

    # Victoire ou défaite
    if jeux_gagnes > jeux_perdus:
        st.session_state.joueurs[joueur]["Points"] += 3
    else:
        st.session_state.joueurs[joueur]["Points"] += 1

    # Bonus : 0.1 pt par jeu gagné
    st.session_state.joueurs[joueur]["Points"] += jeux_gagnes * 0.1


# ----------------------------
# MISE À JOUR CLASSEMENT
# ----------------------------
def maj_classement(matchs, scores):
    for (team1, team2), score in zip(matchs, scores):
        if not score or "-" not in score:
            continue
        try:
            s1, s2 = map(int, score.split("-"))
        except:
            continue

        for joueur in team1:
            ajouter_stats(joueur, s1, s2)
        for joueur in team2:
            ajouter_stats(joueur, s2, s1)


# ----------------------------
# AFFICHAGE CLASSEMENT
# ----------------------------
def afficher_classement():
    if not st.session_state.joueurs:
        return
    df = pd.DataFrame(st.session_state.joueurs).T
    df.index.name = "Joueur"
    df = df.reset_index()
    df = df.sort_values(by=["Points", "Jeux"], ascending=[False, False])
    df.insert(0, "Rang", range(1, len(df) + 1))
    st.subheader("🏅 Classement Général")
    st.table(df)


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

    return matchs


# ----------------------------
# PHASES FINALES
# ----------------------------
def generer_quarts():
    classement = sorted(st.session_state.joueurs.items(), key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True)
    joueurs_tries = [j[0] for j in classement]

    quarts = [
        (joueurs_tries[0:2], joueurs_tries[6:8]),
        (joueurs_tries[2:4], joueurs_tries[4:6])
    ]
    st.session_state.finales["quarts"] = quarts
    return quarts


def generer_demis():
    winners = []
    for (team1, team2), score in zip(st.session_state.finales["quarts"], st.session_state.scores[-2:]):
        if not score or "-" not in score:
            continue
        s1, s2 = map(int, score.split("-"))
        winners.append(team1 if s1 > s2 else team2)

    if len(winners) == 2:
        st.session_state.finales["demis"] = [(winners[0], winners[1])]
    return st.session_state.finales["demis"]


def generer_finale():
    winners = []
    for (team1, team2), score in zip(st.session_state.finales["demis"], st.session_state.scores[-1:]):
        if not score or "-" not in score:
            continue
        s1, s2 = map(int, score.split("-"))
        winners.append(team1 if s1 > s2 else team2)

    if len(winners) == 1:
        st.session_state.finales["finale"] = [winners[0]]
    return st.session_state.finales["finale"]


# ----------------------------
# UI STREAMLIT
# ----------------------------
st.title("🎾 Tournoi de Padel - Rétro Padel")

st.sidebar.header("⚙️ Paramètres du tournoi")
hommes = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl").split("\n")
femmes = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica").split("\n")

terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 2)

if st.sidebar.button("🔄 Reset Tournoi"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = []
    st.session_state.round = 0
    st.session_state.finales = {"quarts": [], "demis": [], "finale": []}
    st.success("Tournoi réinitialisé !")

# ----------------------------
# ROUNDS
# ----------------------------
if st.button("🏆 Générer un nouveau round"):
    st.session_state.round += 1
    matchs = generer_round(hommes, femmes, terrains, max_matchs)
    st.session_state.matchs.extend(matchs)
    st.session_state.scores.extend([""] * len(matchs))
    st.success(f"Round {st.session_state.round} généré !")

for idx, (team1, team2) in enumerate(st.session_state.matchs, 1):
    score = st.text_input(f"{team1} vs {team2} (Score Round {st.session_state.round} Terrain {idx})", key=f"score_{idx}")
    if score:
        st.session_state.scores[idx - 1] = score

# ----------------------------
# CLASSEMENT
# ----------------------------
if st.button("📊 Calculer le classement"):
    st.session_state.joueurs = {}
    maj_classement(st.session_state.matchs, st.session_state.scores)
    afficher_classement()

# ----------------------------
# PHASES FINALES
# ----------------------------
st.subheader("🏆 Phases Finales")

if st.button("⚡ Générer Quarts de finale"):
    quarts = generer_quarts()
    for i, (team1, team2) in enumerate(quarts, 1):
        st.text_input(f"{team1} vs {team2} (Score Quarts Match {i})", key=f"quart_{i}")

if st.button("🔥 Jouer les 1/2 finales"):
    demis = generer_demis()
    for i, (team1, team2) in enumerate(demis, 1):
        st.text_input(f"{team1} vs {team2} (Score 1/2 finale {i})", key=f"demi_{i}")

if st.button("🏅 Jouer la Finale"):
    finale = generer_finale()
    if finale:
        st.success(f"🏆 Le grand vainqueur est : {finale[0]} 🎉")

if st.button("♻️ Reset Phases Finales"):
    st.session_state.finales = {"quarts": [], "demis": [], "finale": []}
    st.success("Phases finales réinitialisées !")
