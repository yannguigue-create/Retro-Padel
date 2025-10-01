import streamlit as st
import pandas as pd
import random

# ===================================
# PAGE CONFIGURATION
# ===================================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ===================================
# SESSION STATE INIT
# ===================================
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame()
if "quarts" not in st.session_state:
    st.session_state.quarts = []
if "demis" not in st.session_state:
    st.session_state.demis = []
if "finale" not in st.session_state:
    st.session_state.finale = []

# ===================================
# FONCTIONS
# ===================================
def generer_equipes(hommes, femmes):
    """ Génère des équipes homme+femme mélangées """
    random.shuffle(hommes)
    random.shuffle(femmes)
    equipes = list(zip(hommes, femmes))
    return equipes

def generer_round(hommes, femmes, nb_terrains):
    """ Génère un round complet """
    equipes = generer_equipes(hommes, femmes)
    random.shuffle(equipes)
    matchs = []
    for i in range(0, len(equipes), 2):
        if i+1 < len(equipes):
            matchs.append((equipes[i], equipes[i+1]))
    return matchs

def maj_classement(scores, classement):
    """ Met à jour le classement avec les scores """
    for match, score in scores.items():
        if "-" not in score:
            continue
        try:
            s1, s2 = map(int, score.split("-"))
        except:
            continue

        eq1, eq2 = match
        for joueur in eq1:
            if joueur not in classement:
                classement[joueur] = {"Points": 0, "Jeux": 0, "Matchs": 0}
            classement[joueur]["Jeux"] += s1
            classement[joueur]["Matchs"] += 1
        for joueur in eq2:
            if joueur not in classement:
                classement[joueur] = {"Points": 0, "Jeux": 0, "Matchs": 0}
            classement[joueur]["Jeux"] += s2
            classement[joueur]["Matchs"] += 1

        # Attribution des points
        if s1 > s2:
            for joueur in eq1:
                classement[joueur]["Points"] += 3 + s1 * 0.1
            for joueur in eq2:
                classement[joueur]["Points"] += 1 + s2 * 0.1
        elif s2 > s1:
            for joueur in eq2:
                classement[joueur]["Points"] += 3 + s2 * 0.1
            for joueur in eq1:
                classement[joueur]["Points"] += 1 + s1 * 0.1

    # Création DataFrame triée
    df = pd.DataFrame.from_dict(classement, orient="index").reset_index()
    df.rename(columns={"index": "Joueur"}, inplace=True)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Classement", range(1, len(df) + 1))
    return df

def get_winner(score, equipes):
    """ Retourne l’équipe gagnante en fonction du score """
    if "-" not in score:
        return None
    s1, s2 = map(int, score.split("-"))
    return equipes[0] if s1 > s2 else equipes[1]

# ===================================
# SIDEBAR
# ===================================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl").splitlines()
femmes = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica").splitlines()

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
nb_max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

if st.sidebar.button("♻️ Reset Tournoi"):
    st.session_state.rounds = []
    st.session_state.scores = {}
    st.session_state.classement = pd.DataFrame()
    st.session_state.quarts = []
    st.session_state.demis = []
    st.session_state.finale = []
    st.experimental_rerun()

# ===================================
# ROUNDS
# ===================================
st.header("🏆 Rounds")

if st.button("➕ Générer un nouveau round"):
    # Vérifier nombre de matchs joués par joueur
    all_matchs = [m for r in st.session_state.rounds for m in r]
    counts = {}
    for match in all_matchs:
        for eq in match:
            for joueur in eq:
                counts[joueur] = counts.get(joueur, 0) + 1
    if any(c >= nb_max_matchs for c in counts.values()):
        st.warning("⚠️ Certains joueurs ont atteint le maximum de matchs")
    else:
        round_matchs = generer_round(hommes, femmes, nb_terrains)
        st.session_state.rounds.append(round_matchs)
        st.success(f"✅ Round {len(st.session_state.rounds)} généré !")

# Affichage des rounds
for i, matchs in enumerate(st.session_state.rounds, 1):
    st.subheader(f"🏅 Round {i}")
    for j, match in enumerate(matchs, 1):
        equipe1 = " + ".join(match[0])
        equipe2 = " + ".join(match[1])
        key = (match[0], match[1])
        score = st.text_input(f"{equipe1} vs {equipe2} (Score Round {i} Match {j})", 
                              value=st.session_state.scores.get(key, ""), key=f"score_{i}_{j}")
        st.session_state.scores[key] = score

# ===================================
# CLASSEMENT
# ===================================
if st.button("📊 Calculer le classement"):
    classement = {}
    st.session_state.classement = maj_classement(st.session_state.scores, classement)

if not st.session_state.classement.empty:
    st.subheader("🥇 Classement Général")
    st.dataframe(st.session_state.classement)

# ===================================
# PHASES FINALES
# ===================================
st.header("🏆 Phases Finales")

if st.button("⚡ Générer Quarts de finale"):
    df = st.session_state.classement
    if not df.empty and len(df) >= 8:
        joueurs = df["Joueur"].tolist()
        st.session_state.quarts = [
            ((joueurs[0],), (joueurs[7],)),
            ((joueurs[1],), (joueurs[6],)),
            ((joueurs[2],), (joueurs[5],)),
            ((joueurs[3],), (joueurs[4],)),
        ]
        st.success("✅ Quarts générés !")

# Affichage des quarts
if st.session_state.quarts:
    st.subheader("Quarts de finale")
    quarts_winners = []
    for i, match in enumerate(st.session_state.quarts, 1):
        equipe1 = " + ".join(match[0])
        equipe2 = " + ".join(match[1])
        score = st.text_input(f"{equipe1} vs {equipe2} (Score Quarts Match {i})", key=f"quarts_{i}")
        if score:
            winner = get_winner(score, match)
            if winner:
                quarts_winners.append(winner)
    if len(quarts_winners) == 4:
        st.session_state.demis = [(quarts_winners[0], quarts_winners[1]), (quarts_winners[2], quarts_winners[3])]
        st.success("✅ Demi-finales prêtes !")

# Affichage des demis
if st.session_state.demis:
    st.subheader("Demi-finales")
    demi_winners = []
    for i, match in enumerate(st.session_state.demis, 1):
        equipe1 = " + ".join(match[0])
        equipe2 = " + ".join(match[1])
        score = st.text_input(f"{equipe1} vs {equipe2} (Score Demi {i})", key=f"demi_{i}")
        if score:
            winner = get_winner(score, match)
            if winner:
                demi_winners.append(winner)
    if len(demi_winners) == 2:
        st.session_state.finale = [(demi_winners[0], demi_winners[1])]
        st.success("✅ Finale prête !")

# Affichage de la finale
if st.session_state.finale:
    st.subheader("Finale")
    finale = st.session_state.finale[0]
    equipe1 = " + ".join(finale[0])
    equipe2 = " + ".join(finale[1])
    score = st.text_input(f"{equipe1} vs {equipe2} (Score Finale)", key="finale")
    if score:
        winner = get_winner(score, finale)
        if winner:
            st.success(f"🏆 Vainqueur du tournoi : {' + '.join(winner)}")
