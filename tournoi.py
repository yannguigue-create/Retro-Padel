import streamlit as st
import pandas as pd
import random

# ===============================
# PAGE DE CONFIGURATION
# ===============================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ===============================
# LOGO + TITRE
# ===============================
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="300">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">🎾 Tournoi de Padel - Rétro Padel</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ===============================
# INIT SESSION
# ===============================
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Points", "Jeux", "Matchs"])
if "quarts" not in st.session_state:
    st.session_state.quarts = []
if "demis" not in st.session_state:
    st.session_state.demis = []
if "finale" not in st.session_state:
    st.session_state.finale = []

# ===============================
# SIDEBAR PARAMETRES
# ===============================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]
joueurs = hommes + femmes

st.sidebar.markdown(f"👨 Hommes : {len(hommes)}")
st.sidebar.markdown(f"👩 Femmes : {len(femmes)}")
st.sidebar.markdown(f"🧑‍🤝‍🧑 Total joueurs : {len(joueurs)}")

terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 4)

if st.sidebar.button("♻️ Reset Tournoi"):
    st.session_state.rounds = []
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Points", "Jeux", "Matchs"])
    st.session_state.quarts = []
    st.session_state.demis = []
    st.session_state.finale = []
    st.experimental_rerun()

# ===============================
# FONCTIONS
# ===============================
def generer_matchs(hommes, femmes, terrains, max_matchs):
    """Génère des matchs aléatoires mixtes (1 homme + 1 femme par équipe)"""
    random.shuffle(hommes)
    random.shuffle(femmes)
    equipes = list(zip(hommes, femmes))

    matchs = []
    for i in range(0, len(equipes), 2):
        if i+1 < len(equipes):
            eq1 = equipes[i]
            eq2 = equipes[i+1]
            # Vérifie que personne ne dépasse le max de matchs
            if all(st.session_state.classement.loc[st.session_state.classement["Joueur"] == j, "Matchs"].sum() < max_matchs for j in eq1+eq2):
                matchs.append((eq1, eq2))
    return matchs[:terrains]

def maj_classement(matchs, scores):
    """Met à jour le classement en fonction des scores"""
    for (eq1, eq2), score in zip(matchs, scores):
        if not score or "-" not in score:
            continue
        try:
            s1, s2 = map(int, score.split("-"))
        except:
            continue

        for joueur in eq1:
            ajouter_stats(joueur, s1, s2)
        for joueur in eq2:
            ajouter_stats(joueur, s2, s1)

def ajouter_stats(joueur, jeux_gagnes, jeux_perdus):
    df = st.session_state.classement
    if joueur not in df["Joueur"].values:
        df = pd.concat([df, pd.DataFrame([[joueur, 0.0, 0, 0]], columns=["Joueur", "Points", "Jeux", "Matchs"])], ignore_index=True)

    # Points de base (3 si victoire, sinon 1)
    points = 3 if jeux_gagnes > jeux_perdus else 1

    # Bonus : 0.1 point par jeu gagné
    bonus = jeux_gagnes * 0.1

    df.loc[df["Joueur"] == joueur, "Points"] += points + bonus
    df.loc[df["Joueur"] == joueur, "Jeux"] += jeux_gagnes
    df.loc[df["Joueur"] == joueur, "Matchs"] += 1

    st.session_state.classement = df


def afficher_classement():
    if not st.session_state.classement.empty:
        df = st.session_state.classement.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
        df.index = df.index + 1  # Classement commence à 1
        st.dataframe(df, use_container_width=True)

def jouer_phase(matchs, phase):
    """Affiche les matchs d'une phase (quarts, demis, finale)"""
    vainqueurs = []
    for i, (eq1, eq2) in enumerate(matchs, 1):
        score = st.text_input(f"{eq1} vs {eq2} (Score {phase} Match {i})")
        if score and "-" in score:
            try:
                s1, s2 = map(int, score.split("-"))
                vainqueurs.append(eq1 if s1 > s2 else eq2)
            except:
                pass
    return vainqueurs

# ===============================
# GESTION DES MATCHS
# ===============================
st.header("🏆 Rounds")

if st.button("🎲 Générer un nouveau round"):
    matchs = generer_matchs(hommes, femmes, terrains, max_matchs)
    if matchs:
        st.session_state.rounds.append(matchs)
        st.success(f"✅ Round {len(st.session_state.rounds)} généré !")
    else:
        st.warning("⚠️ Tous les joueurs ont atteint leur maximum de matchs.")

for i, matchs in enumerate(st.session_state.rounds, 1):
    st.subheader(f"🏆 Round {i}")
    scores = []
    for j, (eq1, eq2) in enumerate(matchs, 1):
        score = st.text_input(f"{eq1} vs {eq2} (Score Round {i} Terrain {j})")
        scores.append(score)
    maj_classement(matchs, scores)

# ===============================
# CLASSEMENT
# ===============================
st.header("🥇 Classement Général")
afficher_classement()

# ===============================
# PHASES FINALES
# ===============================
st.header("🏆 Phases Finales")

if st.button("⚡ Générer Quarts de finale"):
    df = st.session_state.classement
    if not df.empty and len(df) >= 8:
        hommes_sorted = [j for j in df.sort_values(by=["Points","Jeux"], ascending=False)["Joueur"] if j in hommes]
        femmes_sorted = [j for j in df.sort_values(by=["Points","Jeux"], ascending=False)["Joueur"] if j in femmes]

        hommes_top = hommes_sorted[:4]
        femmes_top = femmes_sorted[:4]

        equipes = list(zip(hommes_top, femmes_top))
        random.shuffle(equipes)

        st.session_state.quarts = [
            (equipes[0], equipes[1]),
            (equipes[2], equipes[3]),
        ]
        st.success("✅ Quarts générés !")

if st.session_state.quarts:
    st.subheader("Quarts de finale")
    vainqueurs_quarts = jouer_phase(st.session_state.quarts, "Quarts")
    if len(vainqueurs_quarts) == 2:
        st.session_state.demis = [(vainqueurs_quarts[0], vainqueurs_quarts[1])]

if st.session_state.demis:
    st.subheader("Demi-finales")
    vainqueurs_demis = jouer_phase(st.session_state.demis, "Demi")
    if len(vainqueurs_demis) == 1:
        st.session_state.finale = [(vainqueurs_demis[0], ("???", "???"))]

if st.session_state.finale:
    st.subheader("Finale")
    jouer_phase(st.session_state.finale, "Finale")

