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

# Zones de texte avec callback pour mise à jour en temps réel
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

# Mise à jour des listes
st.session_state.hommes_list = hommes_input
st.session_state.femmes_list = femmes_input

# Nettoyage des noms
hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

# Compteurs en temps réel avec style
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color: #1f77b4;'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #ff69b4;'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #2ca02c;'>🎯 Total : {len(hommes) + len(femmes)}</h3>", unsafe_allow_html=True)

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

# --- Initialisation et mise à jour des joueurs ---
joueurs_actuels = set(st.session_state.joueurs.keys())
nouveaux_joueurs = set(hommes + femmes)

# Suppression des joueurs qui ne sont plus dans les listes
for j in list(st.session_state.joueurs.keys()):
    if j not in nouveaux_joueurs:
        del st.session_state.joueurs[j]

# Ajout des nouveaux joueurs
for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# --- Génération d'un round ---
def generer_round():
    nb_terrains_dispo = st.session_state.get("nb_terrains", 2)
    max_matchs_joueur = st.session_state.get("max_matchs", 2)
    
    # joueurs éligibles (< max_matchs)
    joueurs_dispo = [j for j in st.session_state.joueurs if st.session_state.joueurs[j]["Matchs"] < max_matchs_joueur]

    hommes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matchs = []
    terrains_possibles = min(nb_terrains_dispo, len(hommes_dispo) // 2, len(femmes_dispo) // 2)
    
    for _ in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1 = hommes_dispo.pop()
            h2 = hommes_dispo.pop()
            f1 = femmes_dispo.pop()
            f2 = femmes_dispo.pop()
            equipe1 = [h1, f1]
            equipe2 = [h2, f2]
            matchs.append((equipe1, equipe2))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

# --- Mise à jour classement ---
def maj_classement():
    # Reset complet
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0
    
    # Recalcul depuis tous les rounds
    for round_idx, matchs in enumerate(st.session_state.matchs):
        for match_idx, (equipe1, equipe2) in enumerate(matchs):
            score_key = f"score_{round_idx+1}_{match_idx}"
            score = st.session_state.scores.get(score_key, "")
            
            if not score or "-" not in score:
                continue
            
            try:
                parts = score.split("-")
                if len(parts) != 2:
                    continue
                s1 = int(parts[0].strip()); s2 = int(parts[1].strip())
            except:
                continue

            if s1 > s2:
                gagnants, perdants, js_gagnants, js_perdants = equipe1, equipe2, s1, s2
            else:
                gagnants, perdants, js_gagnants, js_perdants = equipe2, equipe1, s2, s1

            for j in gagnants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 3.0 + js_gagnants * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_gagnants
                    st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += js_perdants * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_perdants
                    st.session_state.joueurs[j]["Matchs"] += 1

# --- Affichage du classement ---
def afficher_classement():
    if not st.session_state.joueurs:
        st.warning("Aucun joueur enregistré")
        return
    
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index")
    df = df.reset_index().rename(columns={"index": "Joueur"})
    df["Points"] = df["Points"].round(1)
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rang", df.index + 1)
    df = df[["Rang", "Joueur", "Sexe", "Points", "Jeux", "Matchs"]]
    st.table(df)

# ---------- NOUVEAU : Quarts Top 8 Hommes + Top 8 Femmes ----------
def generer_quarts_top8_hf():
    """Top 8 hommes + Top 8 femmes -> 8 équipes mixtes -> 4 quarts (T1-T8, T2-T7, T3-T6, T4-T5)."""
    # Met à jour le classement d'abord
    maj_classement()

    # Top8 hommes
    hommes_tries = sorted(
        [ (j, st.session_state.joueurs[j]) for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "H" ],
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]),
        reverse=True
    )
    femmes_tries = sorted(
        [ (j, st.session_state.joueurs[j]) for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "F" ],
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]),
        reverse=True
    )

    if len(hommes_tries) < 8:
        st.error(f"❌ Il faut au moins 8 hommes (actuellement : {len(hommes_tries)}).")
        return False
    if len(femmes_tries) < 8:
        st.error(f"❌ Il faut au moins 8 femmes (actuellement : {len(femmes_tries)}).")
        return False

    top8H = [j for j, _ in hommes_tries[:8]]
    top8F = [j for j, _ in femmes_tries[:8]]

    # On forme 8 équipes mixtes par rang : (H1+F1), (H2+F2), ... (H8+F8)
    equipes = [[top8H[i], top8F[i]] for i in range(8)]

    # Tableau (têtes de série) : 1-8, 2-7, 3-6, 4-5
    quarts = [
        (equipes[0], equipes[7]),
        (equipes[1], equipes[6]),
        (equipes[2], equipes[5]),
        (equipes[3], equipes[4]),
    ]

    st.session_state.phases_finales["quarts"] = quarts
    st.session_state.phases_finales["demis"] = []
    st.session_state.phases_finales["finale"] = []
    st.session_state.phases_finales["vainqueur"] = None
    st.success("✅ Quarts (Top 8 H & Top 8 F) générés.")
    return True

# (conservées) anciennes options au cas où
def generer_demis_aleatoires():
    tous_joueurs = list(st.session_state.joueurs.keys())
    hommes_dispo = [j for j in tous_joueurs if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in tous_joueurs if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    if len(hommes_dispo) < 4 or len(femmes_dispo) < 4:
        st.error("❌ Il faut au moins 4 hommes et 4 femmes pour les demi-finales")
        return False
    
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)
    
    demis = [
        ([hommes_dispo[0], femmes_dispo[0]], [hommes_dispo[1], femmes_dispo[1]]),
        ([hommes_dispo[2], femmes_dispo[2]], [hommes_dispo[3], femmes_dispo[3]])
    ]
    
    st.session_state.phases_finales["demis"] = demis
    st.session_state.phases_finales["quarts"] = []
    return True

def generer_finale_aleatoire():
    tous_joueurs = list(st.session_state.joueurs.keys())
    hommes_dispo = [j for j in tous_joueurs if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in tous_joueurs if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    if len(hommes_dispo) < 2 or len(femmes_dispo) < 2:
        st.error("❌ Il faut au moins 2 hommes et 2 femmes pour la finale")
        return False
    
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)
    
    finale = [([hommes_dispo[0], femmes_dispo[0]], [hommes_dispo[1], femmes_dispo[1]])]
    
    st.session_state.phases_finales["finale"] = finale
    st.session_state.phases_finales["quarts"] = []
    st.session_state.phases_finales["demis"] = []
    return True

# --- UI ---
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Bloc Round : empêcher si quota atteint
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
else:
    hommes_disponibles = sum(1 for _, info in st.session_state.joueurs.items() if info["Sexe"] == "H" and info["Matchs"] < max_matchs)
    femmes_disponibles = sum(1 for _, info in st.session_state.joueurs.items() if info["Sexe"] == "F" and info["Matchs"] < max_matchs)
    
    terrains_theoriques = min(nb_terrains, hommes_disponibles // 2, femmes_disponibles // 2)
    
    if hommes_disponibles >= 2 and femmes_disponibles >= 2 and terrains_theoriques > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"ℹ️ Vous pouvez générer **{terrains_theoriques}** match(s) avec **{nb_terrains}** terrain(s) disponible(s)")
        with col2:
            if st.button("⚡ Générer un nouveau round", type="primary"):
                success, nb_matchs = generer_round()
                if success:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré avec {nb_matchs} match(s)!")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un nouveau round")
    else:
        st.info(f"ℹ️ Tous les joueurs éligibles ont atteint le nombre maximum de matchs (**{max_matchs}**) ou pas assez pour former un match.")

# Affichage des rounds & saisie des scores
if st.session_state.matchs:
    st.header("📋 Matchs du tournoi")
    for r, matchs in enumerate(st.session_state.matchs, 1):
        st.subheader(f"🏆 Round {r}")
        for idx, (e1, e2) in enumerate(matchs):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Terrain {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
            with col2:
                score_key = f"score_{r}_{idx}"
                score = st.text_input("Score (ex: 6-4)", key=score_key, label_visibility="collapsed")
                if score:
                    st.session_state.scores[score_key] = score

    st.markdown("---")
    if st.button("📊 Calculer le classement", type="primary"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# Affichage du classement
if st.session_state.classement_calcule or any(st.session_state.joueurs[j]["Matchs"] > 0 for j in st.session_state.joueurs):
    st.header("📊 Classement général")
    maj_classement()
    afficher_classement()

# --- Phases finales ---
st.markdown("---")
st.header("🏆 Phases Finales")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⚡ Quarts Top 8 (Hommes & Femmes)", type="primary"):
        if generer_quarts_top8_hf():
            st.rerun()

with col2:
    if st.button("🎲 Demi-finales aléatoires", type="secondary"):
        if generer_demis_aleatoires():
            st.success("✅ Demi-finales aléatoires générées!")
            st.rerun()

with col3:
    if st.button("🎲 Finale aléatoire", type="secondary"):
        if generer_finale_aleatoire():
            st.success("✅ Finale aléatoire générée!")
            st.rerun()

if st.button("♻️ Reset Phases Finales"):
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.success("✅ Phases finales réinitialisées")
    st.rerun()

# Quarts de finale
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Match {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
        with col2:
            score = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if score and "-" in score:
                try:
                    s1, s2 = map(int, score.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except:
                    pass
    
    if len(gagnants_quarts) == 4 and st.button("➡️ Valider et passer aux Demi-finales"):
        st.session_state.phases_finales["demis"] = [
            (gagnants_quarts[0], gagnants_quarts[1]),
            (gagnants_quarts[2], gagnants_quarts[3])
        ]
        st.session_state.phases_finales["quarts"] = []
        st.rerun()

# Demi-finales
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Demi-finale {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
        with col2:
            score = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if score and "-" in score:
                try:
                    s1, s2 = map(int, score.split("-"))
                    gagnants_demis.append(e1 if s1 > s2 else e2)
                except:
                    pass
    
    if len(gagnants_demis) == 2 and st.button("➡️ Valider et passer à la Finale"):
        st.session_state.phases_finales["finale"] = [(gagnants_demis[0], gagnants_demis[1])]
        st.session_state.phases_finales["demis"] = []
        st.rerun()

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)**")
    with col2:
        score = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if score and "-" in score:
            try:
                s1, s2 = map(int, score.split("-"))
                vainqueur = e1 if s1 > s2 else e2
                if st.button("🏆 Déclarer le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainqueur
                    st.session_state.phases_finales["finale"] = []
                    st.rerun()
            except:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🏆🎉")
