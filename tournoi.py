import streamlit as st
import pandas as pd
import random

# ========================
# CONFIGURATION PAGE
# ========================
st.set_page_config(
    page_title="Tournoi de Padel - Retro Padel",
    page_icon="🎾",
    layout="wide"
)

# ========================
# LOGO + TITRE
# ========================
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="300">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">
            🎾 Tournoi de Padel - Retro Padel
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ========================
# PARAMÈTRES
# ========================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")

    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    st.markdown(f"👨 Hommes : **{len(hommes)}**")
    st.markdown(f"👩 Femmes : **{len(femmes)}**")
    st.markdown(f"📊 Total joueurs : **{len(hommes) + len(femmes)}**")

    terrains = st.number_input("Nombre de terrains disponibles", 1, 10, 4)
    matchs_max = st.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

    if st.button("♻️ Reset Tournoi"):
        for key in ["matches", "rounds", "classement", "phases_finales"]:
            st.session_state[key] = []
        st.success("Le tournoi a été réinitialisé.")

# ========================
# INIT SESSION STATE
# ========================
if "matches" not in st.session_state:
    st.session_state.matches = []
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame()
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {}

# ========================
# GÉNÉRATION DES MATCHS
# ========================
def generer_round(hommes, femmes, terrains):
    joueurs_dispo = hommes + femmes
    random.shuffle(joueurs_dispo)

    matches_round = []
    for i in range(0, min(len(joueurs_dispo), terrains * 4), 4):
        equipeA = [joueurs_dispo[i], joueurs_dispo[i+1]]
        equipeB = [joueurs_dispo[i+2], joueurs_dispo[i+3]]
        matches_round.append((equipeA, equipeB))
    return matches_round

# ========================
# CLASSEMENT
# ========================
def maj_classement(matches):
    data = {}
    for match in matches:
        score = match.get("score")
        if not score:
            continue
        try:
            sA, sB = map(int, score.split("-"))
        except:
            continue

        equipeA, equipeB = match["A"], match["B"]

        # Victoire = 3 points, défaite = 1 point
        if sA > sB:
            ptsA, ptsB = 3, 1
        elif sB > sA:
            ptsA, ptsB = 1, 3
        else:
            ptsA, ptsB = 2, 2

        for j in equipeA:
            if j not in data:
                data[j] = {"Points": 0, "Jeux": 0, "Matchs": 0}
            data[j]["Points"] += ptsA
            data[j]["Jeux"] += sA
            data[j]["Matchs"] += 1

        for j in equipeB:
            if j not in data:
                data[j] = {"Points": 0, "Jeux": 0, "Matchs": 0}
            data[j]["Points"] += ptsB
            data[j]["Jeux"] += sB
            data[j]["Matchs"] += 1

    classement = pd.DataFrame.from_dict(data, orient="index").reset_index()
    classement = classement.rename(columns={"index": "Joueur"})
    # Correction → index 1,2,3… et pas 0
    classement = classement.sort_values(by=["Points", "Jeux"], ascending=[False, False]).reset_index(drop=True)
    classement.index += 1
    return classement

# ========================
# INTERFACE MATCHS
# ========================
st.subheader("🎲 Gestion des matchs")

def joueur_a_atteint_max(matches, max_matchs):
    compteur = {}
    for m in matches:
        if m.get("score"):  # on compte que les matchs joués
            for j in m["A"] + m["B"]:
                compteur[j] = compteur.get(j, 0) + 1
    return any(nb >= max_matchs for nb in compteur.values())

bloque = joueur_a_atteint_max(st.session_state.matches, matchs_max)

if st.button("➕ Générer un nouveau round", disabled=bloque):
    nouveau_round = generer_round(hommes, femmes, terrains)
    st.session_state.rounds.append(nouveau_round)
    for terrain, match in enumerate(nouveau_round, 1):
        st.session_state.matches.append({"A": match[0], "B": match[1], "score": "", "round": len(st.session_state.rounds), "terrain": terrain})

# Affichage des rounds
for r, round_matches in enumerate(st.session_state.rounds, 1):
    st.markdown(f"## 🏆 Round {r}")
    for terrain, match in enumerate(round_matches, 1):
        equipeA, equipeB = match
        key = f"score_round{r}_terrain{terrain}"
        score = st.text_input(f"{' + '.join(equipeA)} vs {' + '.join(equipeB)} (Score Round {r} Terrain {terrain})", key=key)
        for m in st.session_state.matches:
            if m["A"] == equipeA and m["B"] == equipeB and m["round"] == r and m["terrain"] == terrain:
                m["score"] = score

# ========================
# CLASSEMENT GÉNÉRAL
# ========================
if st.button("📊 Calculer le classement"):
    st.session_state.classement = maj_classement(st.session_state.matches)

if not st.session_state.classement.empty:
    st.subheader("🏅 Classement Général")
    st.dataframe(st.session_state.classement)

    # Top 8
    top_hommes = st.session_state.classement[st.session_state.classement["Joueur"].isin(hommes)].head(8)
    top_femmes = st.session_state.classement[st.session_state.classement["Joueur"].isin(femmes)].head(8)

    st.markdown("### 👨 Top 8 Hommes")
    st.dataframe(top_hommes)
    st.markdown("### 👩 Top 8 Femmes")
    st.dataframe(top_femmes)

    # Génération phases finales
    if st.button("⚡ Générer phases finales"):
        st.session_state.phases_finales["quarts"] = [
            (["1H", "8F"], ["4H", "5F"]),
            (["2H", "7F"], ["3H", "6F"]),
            (["1F", "8H"], ["4F", "5H"]),
            (["2F", "7H"], ["3F", "6H"])
        ]
        st.success("✅ Phases finales générées !")

# ========================
# PHASES FINALES AUTOMATISÉES
# ========================

def generer_matchs_elimination(df, phase):
    """Retourne la liste des matchs pour la phase donnée"""
    matchs = []
    if phase == "quarts":
        for i in range(4):
            j1 = df.iloc[i]["Joueur"]
            j2 = df.iloc[7-i]["Joueur"]
            matchs.append((j1, j2))
    elif phase == "demis":
        for i in range(2):
            j1 = st.session_state.phases_finales["quarts_gagnants"][i]
            j2 = st.session_state.phases_finales["quarts_gagnants"][3-i]
            matchs.append((j1, j2))
    elif phase == "finale":
        j1 = st.session_state.phases_finales["demis_gagnants"][0]
        j2 = st.session_state.phases_finales["demis_gagnants"][1]
        matchs.append((j1, j2))
    return matchs


def afficher_matchs_phase(phase):
    """Affiche les matchs d'une phase et saisie des scores"""
    st.markdown(f"### {phase.capitalize()}")

    matchs = st.session_state.phases_finales[phase]
    gagnants = []

    for idx, (j1, j2) in enumerate(matchs, 1):
        score = st.text_input(f"{j1} vs {j2} (Score {phase} Match {idx})", key=f"{phase}_match{idx}")
        if score:
            try:
                s1, s2 = map(int, score.split("-"))
                if s1 > s2:
                    gagnants.append(j1)
                else:
                    gagnants.append(j2)
            except:
                st.warning("Format invalide, utilisez X-Y (ex: 6-4).")

    return gagnants


# === Génération automatique des 1/4 ===
if st.button("⚡ Générer les 1/4 de finale"):
    df = st.session_state.classement
    if not df.empty and len(df) >= 8:
        st.session_state.phases_finales["quarts"] = generer_matchs_elimination(df, "quarts")
        st.success("✅ 1/4 de finale générés !")

# === Jouer les 1/4 ===
if "quarts" in st.session_state.phases_finales:
    st.session_state.phases_finales["quarts_gagnants"] = afficher_matchs_phase("quarts")

# === Jouer les 1/2 ===
if "quarts_gagnants" in st.session_state.phases_finales and len(st.session_state.phases_finales["quarts_gagnants"]) == 4:
    if st.button("⚡ Générer les 1/2 finales"):
        st.session_state.phases_finales["demis"] = generer_matchs_elimination(None, "demis")
        st.success("✅ 1/2 finales générées !")

if "demis" in st.session_state.phases_finales:
    st.session_state.phases_finales["demis_gagnants"] = afficher_matchs_phase("demis")

# === Jouer la finale ===
if "demis_gagnants" in st.session_state.phases_finales and len(st.session_state.phases_finales["demis_gagnants"]) == 2:
    if st.button("⚡ Générer la Finale"):
        st.session_state.phases_finales["finale"] = generer_matchs_elimination(None, "finale")
        st.success("🏆 Finale générée !")

if "finale" in st.session_state.phases_finales:
    vainqueur = afficher_matchs_phase("finale")
    if vainqueur:
        st.success(f"🏆 Le grand vainqueur du tournoi est **{vainqueur[0]}** !")

# === Reset uniquement phases finales ===
if st.button("♻️ Reset Phases Finales"):
    st.session_state.phases_finales = {}
    st.warning("Phases finales réinitialisées.")


