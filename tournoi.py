import streamlit as st
import random
import pandas as pd

# --- Initialisation de l'état de la session ---
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

# --- Configuration de la page et Style ---
st.set_page_config(layout="wide")

# Style CSS pour rendre les tableaux plus compacts
st.markdown("""
<style>
.small-table {
    width: auto;
    margin-left: auto;
    margin-right: auto;
}
.small-table thead th {
    text-align: center !important;
    padding: 4px 6px !important;
    font-size: 0.9rem !important;
}
.small-table tbody td {
    padding: 2px 4px !important;
    font-size: 0.85rem !important;
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

# --- Barre latérale des paramètres ---
st.sidebar.header("⚙️ Paramètres du tournoi")

# Zones de texte pour la liste des joueurs
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

# Mise à jour des listes dans l'état de la session
st.session_state.hommes_list = hommes_input
st.session_state.femmes_list = femmes_input

# Nettoyage des noms et création des listes
hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

# Affichage des compteurs de joueurs
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color: #1f77b4;'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #ff69b4;'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #2ca02c;'>🎯 Total : {len(hommes) + len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Paramètres du tournoi
nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2, key="nb_terrains")
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 2, key="max_matchs")

st.sidebar.markdown("---")

# Bouton de réinitialisation
if st.sidebar.button("🔄 Reset Tournoi Complet", type="primary"):
    # Réinitialise toutes les variables de la session
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("✅ Tournoi réinitialisé")
    st.rerun()

# --- Initialisation et mise à jour des joueurs ---
# Crée des ensembles pour comparer les joueurs actuels et les nouveaux
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

# --- Génération d'un round de poule ---
def generer_round():
    nb_terrains_dispo = st.session_state.get("nb_terrains", 2)
    max_matchs_joueur = st.session_state.get("max_matchs", 2)

    # Filtre les joueurs n'ayant pas atteint le nombre maximum de matchs
    joueurs_dispo = [
        j for j, data in st.session_state.joueurs.items()
        if data["Matchs"] < max_matchs_joueur
    ]

    hommes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "F"]

    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matchs = []
    # Calcule le nombre de matchs possibles en fonction des joueurs et terrains disponibles
    terrains_a_utiliser = min(
        nb_terrains_dispo,
        len(hommes_dispo) // 2,
        len(femmes_dispo) // 2
    )

    # Crée les matchs
    for _ in range(terrains_a_utiliser):
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

# --- Mise à jour du classement ---
def maj_classement():
    # Réinitialise les stats de tous les joueurs
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    # Recalcule les stats en parcourant tous les scores enregistrés
    for round_idx, matchs_round in enumerate(st.session_state.matchs):
        for match_idx, (equipe1, equipe2) in enumerate(matchs_round):
            score_key = f"score_{round_idx+1}_{match_idx}"
            score = st.session_state.scores.get(score_key, "")

            if not score or "-" not in score:
                continue

            try:
                s1, s2 = map(int, score.split("-"))
            except (ValueError, TypeError):
                continue

            gagnants, perdants = (equipe1, equipe2) if s1 > s2 else (equipe2, equipe1)
            js_g, js_p = max(s1, s2), min(s1, s2)

            # Met à jour les stats pour chaque joueur
            for j in gagnants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 3.0 + js_g * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_g
                    st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 0.5
                    st.session_state.joueurs[j]["Jeux"] += js_p
                    st.session_state.joueurs[j]["Matchs"] += 1

# --- Affichage du classement ---
def afficher_classement():
    if not st.session_state.joueurs:
        st.warning("Aucun joueur enregistré")
        return

    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index")
    df = df.reset_index().rename(columns={"index": "Joueur"})
    
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rang", df.index + 1)
    
    df_display = df[["Rang", "Joueur", "Sexe", "Points", "Jeux", "Matchs"]].copy()
    
    # Format Points to one decimal place
    df_display.loc[:, "Points"] = df_display["Points"].map('{:.1f}'.format)
    
    styler = df_display.style.set_table_attributes('class="small-table"').hide(axis="index")
    st.write(styler.to_html(), unsafe_allow_html=True)

def afficher_top8():
    """Affiche les Top 8 par sexe dans des tableaux compacts"""
    if not st.session_state.joueurs:
        return

    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index": "Joueur"}, inplace=True)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False)
    
    topH = df[df["Sexe"] == "H"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].copy()
    topF = df[df["Sexe"] == "F"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].copy()

    # Format Points to one decimal place
    topH.loc[:, "Points"] = topH["Points"].map('{:.1f}'.format)
    topF.loc[:, "Points"] = topF["Points"].map('{:.1f}'.format)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        stylerH = topH.style.set_table_attributes('class="small-table"').hide(axis="index")
        st.write(stylerH.to_html(), unsafe_allow_html=True)
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        stylerF = topF.style.set_table_attributes('class="small-table"').hide(axis="index")
        st.write(stylerF.to_html(), unsafe_allow_html=True)

# --- PHASES FINALES ---
def generer_quarts():
    """
    Génère les quarts de finale en se basant sur les 8 meilleurs hommes
    et les 8 meilleures femmes, puis en formant des équipes têtes de série.
    """
    # 1. S'assurer que le classement est à jour
    maj_classement()

    # 2. Séparer les joueurs par sexe
    hommes = {j: data for j, data in st.session_state.joueurs.items() if data["Sexe"] == "H"}
    femmes = {j: data for j, data in st.session_state.joueurs.items() if data["Sexe"] == "F"}

    # 3. Vérifier qu'il y a assez de joueurs qualifiés
    if len(hommes) < 8 or len(femmes) < 8:
        st.error(f"❌ Il faut au moins 8 hommes et 8 femmes pour les phases finales (actuellement : {len(hommes)} H / {len(femmes)} F)")
        return False

    # 4. Trier chaque liste par Points, puis par Jeux (décroissant)
    hommes_tries = sorted(hommes.items(), key=lambda item: (item[1]["Points"], item[1]["Jeux"]), reverse=True)
    femmes_triees = sorted(femmes.items(), key=lambda item: (item[1]["Points"], item[1]["Jeux"]), reverse=True)

    # 5. Sélectionner les 8 meilleurs de chaque sexe
    top_8_hommes = [joueur[0] for joueur in hommes_tries[:8]]
    top_8_femmes = [joueur[0] for joueur in femmes_triees[:8]]

    # 6. Former les 8 équipes têtes de série (T1 = meilleur H + meilleure F, etc.)
    equipes = [[top_8_hommes[i], top_8_femmes[i]] for i in range(8)]
    st.write("Équipes têtes de série qualifiées :")
    for i, equipe in enumerate(equipes, 1):
        st.write(f"T{i}: {equipe[0]} & {equipe[1]}")

    # 7. Créer les matchs des quarts de finale selon le tableau T1-T8, T2-T7, etc.
    quarts = [
        (equipes[0], equipes[7]),  # T1 vs T8
        (equipes[1], equipes[6]),  # T2 vs T7
        (equipes[2], equipes[5]),  # T3 vs T6
        (equipes[3], equipes[4]),  # T4 vs T5
    ]

    st.session_state.phases_finales["quarts"] = quarts
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

# --- INTERFACE UTILISATEUR PRINCIPALE ---
st.title("🎾 Tournoi de Padel")

# Section pour générer les rounds de poule
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
else:
    hommes_disponibles = sum(1 for j in st.session_state.joueurs.values() if j["Sexe"] == "H" and j["Matchs"] < max_matchs)
    femmes_disponibles = sum(1 for j in st.session_state.joueurs.values() if j["Sexe"] == "F" and j["Matchs"] < max_matchs)

    terrains_theoriques = min(nb_terrains, hommes_disponibles // 2, femmes_disponibles // 2)

    if terrains_theoriques > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"ℹ️ Vous pouvez générer {terrains_theoriques} match(s) avec les joueurs disponibles.")
        with col2:
            if st.button("⚡ Générer un nouveau round", type="primary"):
                success, nb_matchs_crees = generer_round()
                if success:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré avec {nb_matchs_crees} match(s)!")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un nouveau round. Vérifiez le nombre de joueurs disponibles.")
    else:
        st.info(f"ℹ️ Tous les joueurs ont atteint le nombre maximum de matchs ({max_matchs}) ou il n'y a pas assez de paires H/F disponibles.")

# Affichage des rounds et saisie des scores
if st.session_state.matchs:
    st.header("📋 Matchs du tournoi")
    for r, matchs_round in enumerate(st.session_state.matchs, 1):
        st.subheader(f"🔄 Round {r}")
        for idx, (e1, e2) in enumerate(matchs_round):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Terrain {idx+1}:** {e1[0]} & {e1[1]} 🆚 {e2[0]} & {e2[1]}")
            with col2:
                score_key = f"score_{r}_{idx}"
                st.text_input("Score (ex: 6-4)", key=score_key, label_visibility="collapsed")

    st.markdown("---")
    if st.button("📊 Calculer le classement", type="primary"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# Affichage du classement général
if st.session_state.classement_calcule or any(j["Matchs"] > 0 for j in st.session_state.joueurs.values()):
    st.header("📊 Classement général")
    maj_classement() # Toujours recalculer pour avoir les données à jour
    afficher_classement()
    st.markdown("---")
    st.header("🏆 Top 8 Qualifiés pour les phases finales")
    afficher_top8()

# --- Section des phases finales ---
st.markdown("---")
st.header("🏆 Phases Finales")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⚡ Générer Quarts (Top 8 H/F)", type="primary"):
        if generer_quarts():
            st.success("✅ Quarts de finale générés!")
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

# Logique d'affichage et de progression des phases finales
def afficher_phase(nom_phase, cle_session, etape_suivante):
    if st.session_state.phases_finales[cle_session]:
        st.subheader(f"⚔️ {nom_phase}")
        gagnants = []
        for idx, (e1, e2) in enumerate(st.session_state.phases_finales[cle_session]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Match {idx+1}:** {e1[0]} & {e1[1]} 🆚 {e2[0]} & {e2[1]}")
            with col2:
                score = st.text_input("Score", key=f"{cle_session}_{idx}", label_visibility="collapsed")
                if score and "-" in score:
                    try:
                        s1, s2 = map(int, score.split("-"))
                        gagnants.append(e1 if s1 > s2 else e2)
                    except ValueError:
                        pass # Ignore les scores mal formatés

        if len(gagnants) == len(st.session_state.phases_finales[cle_session]):
            if st.button(f"➡️ Valider et passer aux {etape_suivante}"):
                if etape_suivante == "Demi-finales":
                    st.session_state.phases_finales["demis"] = [(gagnants[0], gagnants[1]), (gagnants[2], gagnants[3])]
                elif etape_suivante == "Finale":
                    st.session_state.phases_finales["finale"] = [(gagnants[0], gagnants[1])]
                
                st.session_state.phases_finales[cle_session] = [] # Vide la phase actuelle
                st.rerun()

afficher_phase("Quarts de finale", "quarts", "Demi-finales")
afficher_phase("Demi-finales", "demis", "Finale")

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### **{e1[0]} & {e1[1]} 🆚 {e2[0]} & {e2[1]}**")
    with col2:
        score = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if score and "-" in score:
            try:
                s1, s2 = map(int, score.split("-"))
                vainqueur = e1 if s1 > s2 else e2
                if st.button("🏆 Déclarer les vainqueurs"):
                    st.session_state.phases_finales["vainqueur"] = vainqueur
                    st.session_state.phases_finales["finale"] = []
                    st.rerun()
            except ValueError:
                pass

# Affichage du vainqueur
if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🏆🎉")
