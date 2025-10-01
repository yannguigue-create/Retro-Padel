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

hommes = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150).splitlines()
femmes = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150).splitlines()
nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

# Nettoyage des noms
hommes = [h.strip() for h in hommes if h.strip()]
femmes = [f.strip() for f in femmes if f.strip()]

st.sidebar.markdown(f"👨 Hommes : {len(hommes)}")
st.sidebar.markdown(f"👩 Femmes : {len(femmes)}")
st.sidebar.markdown(f"🔑 Total joueurs : {len(hommes)+len(femmes)}")

if st.sidebar.button("🔄 Reset Tournoi"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.rerun()

# --- Initialisation joueurs ---
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
    joueurs_dispo = [j for j in st.session_state.joueurs.keys()
                     if st.session_state.joueurs[j]["Matchs"] < max_matchs]

    hommes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matchs = []
    terrains_possibles = min(nb_terrains, len(hommes_dispo) // 2, len(femmes_dispo) // 2)
    
    for _ in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1, h2 = hommes_dispo.pop(), hommes_dispo.pop()
            f1, f2 = femmes_dispo.pop(), femmes_dispo.pop()
            equipe1 = [h1, f1]
            equipe2 = [h2, f2]
            matchs.append((equipe1, equipe2))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True
    return False

# --- Mise à jour classement ---
def maj_classement():
    # Reset des stats
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
                s1, s2 = map(int, score.split("-"))
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

# --- PHASES FINALES ---
def generer_quarts():
    joueurs_trie = sorted(st.session_state.joueurs.items(),
                          key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True)
    
    if len(joueurs_trie) < 8:
        st.error("Il faut au moins 8 joueurs pour les phases finales")
        return False
    
    qualifies = [j[0] for j in joueurs_trie[:8]]
    hommes_qualifies = [j for j in qualifies if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_qualifies = [j for j in qualifies if st.session_state.joueurs[j]["Sexe"] == "F"]
    
    if len(hommes_qualifies) < 4 or len(femmes_qualifies) < 4:
        st.error("Il faut au moins 4 hommes et 4 femmes dans le top 8")
        return False
    
    random.shuffle(hommes_qualifies)
    random.shuffle(femmes_qualifies)
    
    quarts = []
    for i in range(4):
        h1, h2 = hommes_qualifies[i*2], hommes_qualifies[i*2+1] if i*2+1 < len(hommes_qualifies) else hommes_qualifies[0]
        f1, f2 = femmes_qualifies[i*2], femmes_qualifies[i*2+1] if i*2+1 < len(femmes_qualifies) else femmes_qualifies[0]
        quarts.append(([h1, f1], [h2, f2]))
    
    st.session_state.phases_finales["quarts"] = quarts
    return True

# --- UI ---
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Vérification avant de pouvoir générer un round
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
elif st.button("⚡ Générer un nouveau round"):
    if generer_round():
        st.success(f"✅ Round {len(st.session_state.matchs)} généré avec succès!")
        st.rerun()
    else:
        st.warning("Impossible de générer un nouveau round. Vérifiez le nombre de joueurs disponibles et le nombre max de matchs.")

# Affichage des rounds
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

col1, col2 = st.columns(2)
with col1:
    if st.button("⚡ Générer Quarts de finale", type="primary"):
        if generer_quarts():
            st.success("Quarts de finale générés!")
            st.rerun()

with col2:
    if st.button("♻️ Reset Phases Finales"):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("Phases finales réinitialisées")
        st.rerun()

# Quarts de finale
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Match {idx+1}:** {e1[0]} + {e1[1]}  🆚  {e2[0]} + {e2[1]}")
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
        st.rerun()

# Demi-finales
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Demi-finale {idx+1}:** {e1[0]} + {e1[1]}  🆚  {e2[0]} + {e2[1]}")
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
        st.rerun()

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{e1[0]} + {e1[1]}  🆚  {e2[0]} + {e2[1]}**")
    with col2:
        score = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if score and "-" in score:
            try:
                s1, s2 = map(int, score.split("-"))
                vainqueur = e1 if s1 > s2 else e2
                if st.button("🏆 Déclarer le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainqueur
                    st.rerun()
            except:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🏆🎉")
