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

# --- Sidebar Paramètres ---
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150)
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150)

# Nettoyage des noms
hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

# Compteurs en temps réel
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color: #1f77b4;'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #ff69b4;'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #2ca02c;'>🎯 Total : {len(hommes) + len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Reset Tournoi Complet"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
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

# --- Mise à jour classement ---
def maj_classement():
    # Reset complet des stats
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
                s1 = int(parts[0].strip())
                s2 = int(parts[1].strip())
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

# --- Génération d'un round avec répartition équitable ---
def generer_round():
    # Mettre à jour les stats
    maj_classement()
    
    # Trouver le minimum de matchs joués
    if st.session_state.joueurs:
        min_matchs = min(j["Matchs"] for j in st.session_state.joueurs.values())
    else:
        return False, 0
    
    # PRIORITÉ AUX JOUEURS AVEC LE MOINS DE MATCHS
    joueurs_prioritaires = []
    for j_name, j_data in st.session_state.joueurs.items():
        if j_data["Matchs"] == min_matchs and j_data["Matchs"] < max_matchs:
            joueurs_prioritaires.append(j_name)
    
    # Si pas assez de joueurs avec le minimum, prendre aussi ceux avec min+1
    hommes_dispo = [j for j in joueurs_prioritaires if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_prioritaires if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    if len(hommes_dispo) < 2 or len(femmes_dispo) < 2:
        # Prendre tous les joueurs disponibles
        joueurs_prioritaires = [j for j, d in st.session_state.joueurs.items() if d["Matchs"] < max_matchs]
        hommes_dispo = [j for j in joueurs_prioritaires if st.session_state.joueurs[j]["Sexe"] == "H"]
        femmes_dispo = [j for j in joueurs_prioritaires if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    # Trier par nombre de matchs
    hommes_dispo.sort(key=lambda x: st.session_state.joueurs[x]["Matchs"])
    femmes_dispo.sort(key=lambda x: st.session_state.joueurs[x]["Matchs"])
    
    # Mélanger aléatoirement
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matchs = []
    terrains_possibles = min(nb_terrains, len(hommes_dispo) // 2, len(femmes_dispo) // 2)
    
    for i in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1 = hommes_dispo.pop(0)
            h2 = hommes_dispo.pop(0)
            f1 = femmes_dispo.pop(0)
            f2 = femmes_dispo.pop(0)
            equipe1 = [h1, f1]
            equipe2 = [h2, f2]
            matchs.append((equipe1, equipe2))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

# --- Génération automatique de tous les rounds ---
def generer_tous_rounds():
    rounds_generes = 0
    max_iterations = 100  # Sécurité pour éviter boucle infinie
    
    for _ in range(max_iterations):
        success, nb_matchs = generer_round()
        if success:
            rounds_generes += 1
        else:
            break
    
    return rounds_generes

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

# --- PHASES FINALES ---
def generer_quarts():
    maj_classement()
    
    joueurs_trie = sorted(
        st.session_state.joueurs.items(),
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]), 
        reverse=True
    )
    
    if len(joueurs_trie) < 8:
        st.error(f"❌ Il faut au moins 8 joueurs pour les phases finales (actuellement : {len(joueurs_trie)})")
        return False
    
    top8 = [j[0] for j in joueurs_trie[:8]]
    
    hommes_qualifies = [j for j in top8 if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_qualifies = [j for j in top8 if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    if len(hommes_qualifies) < 4:
        st.error(f"❌ Il faut au moins 4 hommes dans le top 8 (actuellement : {len(hommes_qualifies)})")
        return False
    
    if len(femmes_qualifies) < 4:
        st.error(f"❌ Il faut au moins 4 femmes dans le top 8 (actuellement : {len(femmes_qualifies)})")
        return False
    
    random.shuffle(hommes_qualifies)
    random.shuffle(femmes_qualifies)
    
    quarts = []
    for i in range(4):
        h1 = hommes_qualifies[i]
        f1 = femmes_qualifies[i]
        h2_idx = (i + 4) % len(hommes_qualifies)
        f2_idx = (i + 4) % len(femmes_qualifies)
        h2 = hommes_qualifies[h2_idx]
        f2 = femmes_qualifies[f2_idx]
        quarts.append(([h1, f1], [h2, f2]))
    
    st.session_state.phases_finales["quarts"] = quarts[:4]
    return True

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

# Vérification avant de pouvoir générer un round
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
else:
    maj_classement()
    
    hommes_disponibles = sum(1 for j in st.session_state.joueurs.items() if j[1]["Sexe"] == "H" and j[1]["Matchs"] < max_matchs)
    femmes_disponibles = sum(1 for j in st.session_state.joueurs.items() if j[1]["Sexe"] == "F" and j[1]["Matchs"] < max_matchs)
    
    terrains_theoriques = min(nb_terrains, hommes_disponibles // 2, femmes_disponibles // 2)
    
    # Afficher les statistiques
    if st.session_state.joueurs:
        matchs_counts = [j["Matchs"] for j in st.session_state.joueurs.values()]
        min_matchs = min(matchs_counts) if matchs_counts else 0
        max_matchs_joues = max(matchs_counts) if matchs_counts else 0
        st.info(f"📊 Matchs par joueur : Min = {min_matchs}, Max = {max_matchs_joues}, Limite = {max_matchs}")
    
    if hommes_disponibles >= 2 and femmes_disponibles >= 2:
        st.info(f"ℹ️ Vous pouvez générer jusqu'à {terrains_theoriques} match(s) par round avec {nb_terrains} terrain(s)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Générer 1 round", type="primary", use_container_width=True):
                success, nb_matchs = generer_round()
                if success:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré avec {nb_matchs} match(s)!")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un round")
        
        with col2:
            if st.button("🚀 Générer TOUS les rounds", type="secondary", use_container_width=True):
                nb_rounds = generer_tous_rounds()
                if nb_rounds > 0:
                    st.success(f"✅ {nb_rounds} round(s) générés automatiquement!")
                    st.rerun()
                else:
                    st.warning("⚠️ Aucun round supplémentaire possible")
    else:
        st.info(f"ℹ️ Tous les joueurs ont atteint le nombre maximum de matchs ({max_matchs})")

# Affichage des rounds
if st.session_state.matchs:
    st.markdown("---")
    st.header("📋 Matchs du tournoi")
    
    for r, matchs in enumerate(st.session_state.matchs, 1):
        with st.expander(f"🏆 Round {r} - {len(matchs)} match(s)", expanded=(r == len(st.session_state.matchs))):
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

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("⚡ Quarts (Top 8)", use_container_width=True):
        if generer_quarts():
            st.success("✅ Quarts générés!")
            st.rerun()

with col2:
    if st.button("🎲 Demis aléatoires", use_container_width=True):
        if generer_demis_aleatoires():
            st.success("✅ Demis générées!")
            st.rerun()

with col3:
    if st.button("🎲 Finale aléatoire", use_container_width=True):
        if generer_finale_aleatoire():
            st.success("✅ Finale générée!")
            st.rerun()

with col4:
    if st.button("♻️ Reset Phases", use_container_width=True):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("✅ Reset!")
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
