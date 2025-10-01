import streamlit as st
import random
import pandas as pd

# --- Initialisation ---
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
if "classement_calcule" not in st.session_state:
    st.session_state.classement_calcule = False
if "hommes_list" not in st.session_state:
    st.session_state.hommes_list = ""
if "femmes_list" not in st.session_state:
    st.session_state.femmes_list = ""

# --- Sidebar Paramètres ---
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area(
    "Liste des hommes (un par ligne)",
    height=150,
    key="hommes_input",
    value=st.session_state.hommes_list
)
femmes_input = st.sidebar.text_area(
    "Liste des femmes (un par ligne)",
    height=150,
    key="femmes_input",
    value=st.session_state.femmes_list
)

st.session_state.hommes_list = hommes_input
st.session_state.femmes_list = femmes_input

hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:#1f77b4;'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color:#ff69b4;'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color:#2ca02c;'>🎯 Total : {len(hommes)+len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2, key="nb_terrains")
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 2, key="max_matchs")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Reset Tournoi Complet", type="primary"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.success("✅ Tournoi réinitialisé")
    st.rerun()

# --- Mise à jour pool joueurs ---
actuels = set(st.session_state.joueurs.keys())
attendus = set(hommes + femmes)

for j in list(st.session_state.joueurs.keys()):
    if j not in attendus:
        del st.session_state.joueurs[j]

for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# --- Comptage A JOUR des matchs déjà PLANIFIÉS (respect du plafond) ---
def scheduled_counts():
    """Compte, pour chaque joueur, le nombre de matchs déjà planifiés (tous rounds confondus).
       Sert à bloquer la génération au-delà de max_matchs même si les scores ne sont pas saisis."""
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for (e1, e2) in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

# --- Génération d'un round (en respectant max_matchs via scheduled_counts) ---
def generer_round():
    nb_terrains_dispo = st.session_state.get("nb_terrains", 2)
    max_matchs_joueur = st.session_state.get("max_matchs", 2)

    counts = scheduled_counts()  # Compteurs à jour (planifiés)

    joueurs_ok = [j for j in st.session_state.joueurs if counts[j] < max_matchs_joueur]
    hommes_dispo = [j for j in joueurs_ok if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_ok if st.session_state.joueurs[j]["Sexe"] == "F"]

    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matchs = []
    terrains_possibles = min(nb_terrains_dispo, len(hommes_dispo)//2, len(femmes_dispo)//2)

    for _ in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1 = hommes_dispo.pop()
            h2 = hommes_dispo.pop()
            f1 = femmes_dispo.pop()
            f2 = femmes_dispo.pop()
            matchs.append(([h1, f1], [h2, f2]))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

# --- Classement (recalcule Points/Jeux/Matchs à partir des scores) ---
def maj_classement():
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    for r_idx, matchs in enumerate(st.session_state.matchs):
        for m_idx, (e1, e2) in enumerate(matchs):
            key = f"score_{r_idx+1}_{m_idx}"
            score = st.session_state.scores.get(key, "")
            if not score or "-" not in score:
                continue
            try:
                s1, s2 = map(int, score.split("-"))
            except:
                continue

            if s1 > s2:
                gagnants, perdants, jg, jp = e1, e2, s1, s2
            else:
                gagnants, perdants, jg, jp = e2, e1, s2, s1

            for p in gagnants:
                st.session_state.joueurs[p]["Points"] += 3.0 + jg*0.1
                st.session_state.joueurs[p]["Jeux"] += jg
                st.session_state.joueurs[p]["Matchs"] += 1
            for p in perdants:
                st.session_state.joueurs[p]["Points"] += jp*0.1
                st.session_state.joueurs[p]["Jeux"] += jp
                st.session_state.joueurs[p]["Matchs"] += 1

def afficher_classement():
    if not st.session_state.joueurs:
        st.warning("Aucun joueur")
        return
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index().rename(columns={"index":"Joueur"})
    df["Points"] = df["Points"].round(1)
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points","Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0,"Rang", df.index+1)
    st.table(df[["Rang","Joueur","Sexe","Points","Jeux","Matchs"]])

# --- Quarts = Top8 H + Top8 F -> 8 équipes H+F, puis tirage ALÉATOIRE pour les 4 quarts ---
def generer_quarts_top8_hf():
    maj_classement()
    hommes_tries = sorted(
        [(j, st.session_state.joueurs[j]) for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="H"],
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True
    )
    femmes_tries = sorted(
        [(j, st.session_state.joueurs[j]) for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="F"],
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True
    )
    if len(hommes_tries) < 8:
        st.error(f"❌ Au moins 8 hommes requis (actuellement {len(hommes_tries)})"); return False
    if len(femmes_tries) < 8:
        st.error(f"❌ Au moins 8 femmes requises (actuellement {len(femmes_tries)})"); return False

    top8H = [j for j,_ in hommes_tries[:8]]
    top8F = [j for j,_ in femmes_tries[:8]]

    equipes = [[top8H[i], top8F[i]] for i in range(8)]   # 8 équipes mixtes
    random.shuffle(equipes)                               # tirage aléatoire des équipes
    quarts = [(equipes[i], equipes[i+1]) for i in range(0, 8, 2)]  # 4 quarts : équipe0-1, 2-3, 4-5, 6-7

    st.session_state.phases_finales["quarts"] = quarts
    st.session_state.phases_finales["demis"] = []
    st.session_state.phases_finales["finale"] = []
    st.session_state.phases_finales["vainqueur"] = None
    st.success("✅ Quarts générés (Top8 H & Top8 F, tirage aléatoire) !")
    return True

# --- Demi/finale aléatoires BASÉES SUR LES GAGNANTS PRÉCÉDENTS ---
def faire_demis_depuis_gagnants(gagnants_quarts):
    """Tirage aléatoire des 4 gagnants -> 2 demis"""
    eq = gagnants_quarts[:]
    random.shuffle(eq)
    return [(eq[0], eq[1]), (eq[2], eq[3])]

def faire_finale_depuis_gagnants(gagnants_demis):
    """Tirage aléatoire des 2 gagnants -> 1 finale"""
    eq = gagnants_demis[:]
    random.shuffle(eq)
    return [(eq[0], eq[1])]

# --- UI ---
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Info génération round avec respect plafond (via scheduled_counts)
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
else:
    counts = scheduled_counts()
    hommes_ok = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="H" and counts[j] < max_matchs)
    femmes_ok = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="F" and counts[j] < max_matchs)
    terrains_theoriques = min(nb_terrains, hommes_ok//2, femmes_ok//2)

    if terrains_theoriques > 0:
        col1, col2 = st.columns([3,1])
        with col1:
            st.info(f"ℹ️ Vous pouvez générer **{terrains_theoriques}** match(s) avec **{nb_terrains}** terrain(s) (plafond = {max_matchs} matchs/joueur).")
        with col2:
            if st.button("⚡ Générer un nouveau round", type="primary"):
                ok, nbm = generer_round()
                if ok:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nbm} match(s)).")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un nouveau round (plafond atteint / pas assez de joueurs).")
    else:
        st.info(f"ℹ️ Personne d’éligible (plafond **{max_matchs}** atteint ou pas assez de joueurs H/F).")

# Rounds & Saisie des scores
if st.session_state.matchs:
    st.header("📋 Matchs du tournoi")
    for r, matchs in enumerate(st.session_state.matchs, 1):
        st.subheader(f"🏆 Round {r}")
        for idx, (e1, e2) in enumerate(matchs):
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"**Terrain {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
            with col2:
                key = f"score_{r}_{idx}"
                st.session_state.scores[key] = st.text_input("Score (ex: 6-4)", key=key, label_visibility="collapsed")

    st.markdown("---")
    if st.button("📊 Calculer le classement", type="primary"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# Classement
if st.session_state.classement_calcule or any(st.session_state.joueurs[j]["Matchs"]>0 for j in st.session_state.joueurs):
    st.header("📊 Classement général")
    maj_classement()
    afficher_classement()

# --- Phases finales ---
st.markdown("---")
st.header("🏆 Phases Finales")

c1, c2 = st.columns(2)
with c1:
    if st.button("⚡ Quarts Top 8 (H & F) – Tirage aléatoire", type="primary"):
        if generer_quarts_top8_hf():
            st.rerun()
with c2:
    if st.button("♻️ Reset Phases Finales"):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("✅ Phases finales réinitialisées")
        st.rerun()

# Quarts
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**Quart {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  🆚  {e2[0]} (H)+{e2[1]} (F)")
        with col2:
            score = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if score and "-" in score:
                try:
                    s1, s2 = map(int, score.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except:
                    pass
    if len(gagnants_quarts) == 4 and st.button("➡️ Valider & Tirage des Demi-finales"):
        st.session_state.phases_finales["demis"] = faire_demis_depuis_gagnants(gagnants_quarts)
        st.session_state.phases_finales["quarts"] = []
        st.rerun()

# Demis
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**Demi {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  🆚  {e2[0]} (H)+{e2[1]} (F)")
        with col2:
            score = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if score and "-" in score:
                try:
                    s1, s2 = map(int, score.split("-"))
                    gagnants_demis.append(e1 if s1 > s2 else e2)
                except:
                    pass
    if len(gagnants_demis) == 2 and st.button("➡️ Valider & Tirage de la Finale"):
        st.session_state.phases_finales["finale"] = faire_finale_depuis_gagnants(gagnants_demis)
        st.session_state.phases_finales["demis"] = []
        st.rerun()

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    col1, col2 = st.columns([3,1])
    with col1:
        st.write(f"**{e1[0]} (H)+{e1[1]} (F)**  🆚  **{e2[0]} (H)+{e2[1]} (F)**")
    with col2:
        score = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if score and "-" in score:
            try:
                s1, s2 = map(int, score.split("-"))
                vainqueur = e1 if s1 > s2 else e2
                if st.button("🏅 Valider le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainqueur
                    st.session_state.phases_finales["finale"] = []
                    st.rerun()
            except:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS : {v[0]} & {v[1]} !**")
