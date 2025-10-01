import streamlit as st
import pandas as pd
import random

# ==========================
# CONFIGURATION DE LA PAGE
# ==========================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ==========================
# LOGO + TITRE
# ==========================
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="250">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">🎾 Tournoi de Padel - Retro Padel</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================
# PARAMÈTRES
# ==========================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")
    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    st.markdown(f"👨 Hommes : {len(hommes)}")
    st.markdown(f"👩 Femmes : {len(femmes)}")
    st.markdown(f"📊 Total joueurs : {len(hommes) + len(femmes)}")

    nb_terrains = st.number_input("Nombre de terrains disponibles", 1, 10, 2)
    max_matchs = st.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

    if st.button("♻️ Reset Tournoi"):
        st.session_state.clear()
        st.rerun()

# ==========================
# INITIALISATION
# ==========================
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
    for j in hommes + femmes:
        st.session_state.joueurs[j] = {"points": 0, "jeux": 0, "matchs": 0}

if "rounds" not in st.session_state:
    st.session_state.rounds = []

if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueurs_quarts": [], "vainqueurs_demis": []}


# ==========================
# GÉNÉRATION DES MATCHS
# ==========================
def generer_round():
    joueurs_dispo = [j for j, stats in st.session_state.joueurs.items() if stats["matchs"] < max_matchs]
    hommes_dispo = [j for j in joueurs_dispo if j in hommes]
    femmes_dispo = [j for j in joueurs_dispo if j in femmes]

    if len(hommes_dispo) < 2 or len(femmes_dispo) < 2:
        st.warning("⚠️ Pas assez de joueurs disponibles pour générer un nouveau round.")
        return

    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matches = []
    terrains = 0

    while len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2 and terrains < nb_terrains:
        h1, h2 = hommes_dispo.pop(), hommes_dispo.pop()
        f1, f2 = femmes_dispo.pop(), femmes_dispo.pop()
        matches.append([h1, f1, h2, f2])
        for j in [h1, h2, f1, f2]:
            st.session_state.joueurs[j]["matchs"] += 1
        terrains += 1

    st.session_state.rounds.append(matches)


# ==========================
# MISE À JOUR SCORES
# ==========================
def mettre_a_jour_scores(round_index, terrain_index, score_str):
    if not score_str or "-" not in score_str:
        return
    try:
        score_A, score_B = map(int, score_str.split("-"))
    except:
        return

    match = st.session_state.rounds[round_index][terrain_index]
    equipe_A, equipe_B = match[:2], match[2:]

    # Ajout des jeux
    for j in equipe_A:
        st.session_state.joueurs[j]["jeux"] += score_A
    for j in equipe_B:
        st.session_state.joueurs[j]["jeux"] += score_B

    # Points gagnants
    if score_A > score_B:
        for j in equipe_A:
            st.session_state.joueurs[j]["points"] += 3
    elif score_B > score_A:
        for j in equipe_B:
            st.session_state.joueurs[j]["points"] += 3
    else:
        for j in equipe_A + equipe_B:
            st.session_state.joueurs[j]["points"] += 1


# ==========================
# CLASSEMENT
# ==========================
def classement_general():
    df = pd.DataFrame([
        {"Joueur": j, "Points": s["points"], "Jeux": s["jeux"], "Matchs": s["matchs"]}
        for j, s in st.session_state.joueurs.items()
    ])
    return df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)


# ==========================
# PHASES FINALES
# ==========================
def generer_phases_finales():
    df = classement_general()
    hommes_top = [j for j in df["Joueur"] if j in hommes][:4]
    femmes_top = [j for j in df["Joueur"] if j in femmes][:4]

    if len(hommes_top) < 4 or len(femmes_top) < 4:
        st.warning("⚠️ Pas assez de joueurs pour générer les phases finales.")
        return

    st.session_state.phases_finales["quarts"] = [
        [hommes_top[0], femmes_top[0], hommes_top[3], femmes_top[3]],
        [hommes_top[1], femmes_top[1], hommes_top[2], femmes_top[2]],
    ]
    st.success("✅ Quarts de finale générés !")


def jouer_demis():
    winners = st.session_state.phases_finales["vainqueurs_quarts"]
    if len(winners) < 2:
        st.warning("⚠️ Il faut d'abord entrer les scores des quarts.")
        return
    st.session_state.phases_finales["demis"] = [
        [winners[0][0], winners[0][1], winners[1][0], winners[1][1]]
    ]


def jouer_finale():
    winners = st.session_state.phases_finales["vainqueurs_demis"]
    if len(winners) < 1:
        st.warning("⚠️ Il faut d'abord entrer les scores des 1/2.")
        return
    st.session_state.phases_finales["finale"] = [
        [winners[0][0], winners[0][1], winners[0][2], winners[0][3]]
    ]


# ==========================
# INTERFACE PRINCIPALE
# ==========================
st.header("🎲 Gestion des matchs")

if st.button("➕ Générer un nouveau round"):
    generer_round()
    st.success(f"Round {len(st.session_state.rounds)} généré !")

# Affichage des rounds
for i, matches in enumerate(st.session_state.rounds):
    st.subheader(f"🏆 Round {i+1}")
    for t, match in enumerate(matches):
        equipe_A = f"{match[0]} + {match[1]}"
        equipe_B = f"{match[2]} + {match[3]}"
        score = st.text_input(f"{equipe_A} vs {equipe_B} (Score Round {i+1} Terrain {t+1})", key=f"score_{i}_{t}")
        if score:
            mettre_a_jour_scores(i, t, score)

# Classement
if st.button("📊 Calculer le classement"):
    st.subheader("🥇 Classement Général")
    st.dataframe(classement_general(), use_container_width=True)

# Phases finales
st.subheader("🏆 Phases Finales")
if st.button("⚡ Générer Quarts de finale"):
    generer_phases_finales()

if st.session_state.phases_finales["quarts"]:
    st.write("### Quarts de finale")
    for i, match in enumerate(st.session_state.phases_finales["quarts"]):
        equipe_A = f"{match[0]} + {match[1]}"
        equipe_B = f"{match[2]} + {match[3]}"
        score = st.text_input(f"{equipe_A} vs {equipe_B} (Score Quarts Match {i+1})", key=f"score_quart_{i}")
        if score and "-" in score:
            sA, sB = map(int, score.split("-"))
            if sA > sB:
                st.session_state.phases_finales["vainqueurs_quarts"].append([match[0], match[1]])
            else:
                st.session_state.phases_finales["vainqueurs_quarts"].append([match[2], match[3]])

if st.button("🔥 Jouer les 1/2 finales"):
    jouer_demis()

if st.session_state.phases_finales["demis"]:
    st.write("### Demi-finales")
    for i, match in enumerate(st.session_state.phases_finales["demis"]):
        st.write(f"{match[0]} + {match[1]} vs {match[2]} + {match[3]}")
        score = st.text_input(f"Score 1/2 finale {i+1}", key=f"score_demi_{i}")
        if score and "-" in score:
            sA, sB = map(int, score.split("-"))
            if sA > sB:
                st.session_state.phases_finales["vainqueurs_demis"].append(match[:2])
            else:
                st.session_state.phases_finales["vainqueurs_demis"].append(match[2:])

if st.button("🏆 Jouer la Finale"):
    jouer_finale()

if st.session_state.phases_finales["finale"]:
    st.write("### Finale")
    match = st.session_state.phases_finales["finale"][0]
    st.write(f"{match[0]} + {match[1]} vs {match[2]} + {match[3]}")
    score = st.text_input("Score Finale", key="score_finale")
    if score and "-" in score:
        sA, sB = map(int, score.split("-"))
        if sA > sB:
            st.success(f"🏆 Champions : {match[0]} + {match[1]}")
        else:
            st.success(f"🏆 Champions : {match[2]} + {match[3]}")

if st.button("♻️ Reset Phases Finales"):
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueurs_quarts": [], "vainqueurs_demis": []}
    st.success("Phases finales réinitialisées ✅")
