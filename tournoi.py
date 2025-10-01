import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Tournoi de Padel - Rétro Padel", layout="wide")

# --------------------------
# Initialisation des variables
# --------------------------
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}

# --------------------------
# Paramètres du tournoi
# --------------------------
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl").splitlines()
femmes = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica").splitlines()

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", min_value=1, max_value=10, value=2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", min_value=1, max_value=10, value=2)

# Initialisation joueurs
def init_joueurs():
    st.session_state.joueurs = {j: {"Points": 0, "Jeux": 0, "Matchs": 0} for j in hommes + femmes}
init_joueurs()

if st.sidebar.button("🔄 Reset Tournoi"):
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    init_joueurs()
    st.experimental_rerun()

# --------------------------
# Génération des rounds
# --------------------------
st.header("🏆 Rounds")

def peut_jouer(joueur):
    return st.session_state.joueurs[joueur]["Matchs"] < max_matchs

def generer_round():
    joueurs_dispo = [j for j in st.session_state.joueurs.keys() if peut_jouer(j)]
    random.shuffle(joueurs_dispo)
    matchs = []
    while len(joueurs_dispo) >= 4 and len(matchs) < nb_terrains:
        equipe1 = random.sample(joueurs_dispo, 2)
        for j in equipe1: joueurs_dispo.remove(j)
        equipe2 = random.sample(joueurs_dispo, 2)
        for j in equipe2: joueurs_dispo.remove(j)
        matchs.append((equipe1, equipe2))
    return matchs

if st.button("🎲 Générer un nouveau round"):
    nouveau_round = generer_round()
    if nouveau_round:
        st.session_state.matchs.append(nouveau_round)
        for i, (eq1, eq2) in enumerate(nouveau_round, 1):
            st.session_state.scores[f"Round {len(st.session_state.matchs)} Match {i}"] = ""

# Affichage rounds
for r, round_matchs in enumerate(st.session_state.matchs, 1):
    st.subheader(f"🏆 Round {r}")
    for i, (eq1, eq2) in enumerate(round_matchs, 1):
        score_key = f"Round {r} Match {i}"
        score = st.text_input(f"{' + '.join(eq1)} vs {' + '.join(eq2)} (Score {score_key})", key=score_key)
        st.session_state.scores[score_key] = score

# --------------------------
# Mise à jour classement
# --------------------------
def maj_classement():
    init_joueurs()
    for score_key, score in st.session_state.scores.items():
        if not score or "-" not in score: 
            continue
        try:
            jeux1, jeux2 = map(int, score.split("-"))
        except:
            continue
        # Retrouver les équipes
        r, m = map(int, [s for s in score_key.split() if s.isdigit()])
        eq1, eq2 = st.session_state.matchs[r-1][m-1]

        # Victoire = 3 pts + 0.1/jeu
        if jeux1 > jeux2:
            for j in eq1:
                st.session_state.joueurs[j]["Points"] += 3 + jeux1 * 0.1
            for j in eq2:
                st.session_state.joueurs[j]["Points"] += jeux2 * 0.1
        else:
            for j in eq2:
                st.session_state.joueurs[j]["Points"] += 3 + jeux2 * 0.1
            for j in eq1:
                st.session_state.joueurs[j]["Points"] += jeux1 * 0.1

        # Ajouter jeux + matchs
        for j in eq1:
            st.session_state.joueurs[j]["Jeux"] += jeux1
            st.session_state.joueurs[j]["Matchs"] += 1
        for j in eq2:
            st.session_state.joueurs[j]["Jeux"] += jeux2
            st.session_state.joueurs[j]["Matchs"] += 1

if st.button("📊 Calculer le classement"):
    maj_classement()

    classement = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index")
    classement = classement.sort_values(by=["Points","Jeux"], ascending=False).reset_index()
    classement.index += 1
    classement.rename(columns={"index": "Joueur"}, inplace=True)
    classement["Points"] = classement["Points"].round(1)
    st.subheader("🥇 Classement Général")
    st.dataframe(classement)

# --------------------------
# Phases Finales
# --------------------------
st.header("🏆 Phases Finales")

def generer_equipes_mixtes(joueurs):
    hommes_dispo = [h for h in joueurs if h in hommes]
    femmes_dispo = [f for f in joueurs if f in femmes]
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)
    equipes = []
    while hommes_dispo and femmes_dispo:
        equipes.append([hommes_dispo.pop(), femmes_dispo.pop()])
    return equipes

if st.button("⚡ Générer Quarts de finale"):
    maj_classement()
    classement = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index")
    classement = classement.sort_values(by=["Points","Jeux"], ascending=False).reset_index()
    top8 = classement["index"].tolist()[:8]

    equipes = generer_equipes_mixtes(top8)
    random.shuffle(equipes)
    st.session_state.phases_finales["quarts"] = [(equipes[i], equipes[i+1]) for i in range(0, len(equipes)-1, 2)]

if st.button("♻️ Reset Phases Finales"):
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    st.experimental_rerun()

# Affichage des quarts
if st.session_state.phases_finales["quarts"]:
    st.subheader("Quarts de finale")
    for i, (eq1, eq2) in enumerate(st.session_state.phases_finales["quarts"], 1):
        st.text_input(f"{' + '.join(eq1)} vs {' + '.join(eq2)} (Score Quarts Match {i})", key=f"Quarts {i}")

