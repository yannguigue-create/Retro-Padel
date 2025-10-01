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
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
if "elimines" not in st.session_state:
    st.session_state.elimines = set()

# --- Sidebar Paramètres ---
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes = st.sidebar.text_area("Liste des hommes (un par ligne)").splitlines()
femmes = st.sidebar.text_area("Liste des femmes (un par ligne)").splitlines()
nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

st.sidebar.markdown(f"👨 Hommes : {len(hommes)}")
st.sidebar.markdown(f"👩 Femmes : {len(femmes)}")
st.sidebar.markdown(f"🔑 Total joueurs : {len(hommes)+len(femmes)}")

if st.sidebar.button("🔄 Reset Tournoi"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    st.session_state.elimines = set()
    st.rerun()

# --- Initialisation joueurs ---
for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# --- Génération d'un round ---
def generer_round():
    joueurs_dispo = [j for j in st.session_state.joueurs.keys()
                     if st.session_state.joueurs[j]["Matchs"] < max_matchs]

    random.shuffle(joueurs_dispo)
    hommes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_dispo if st.session_state.joueurs[j]["Sexe"] == "F"]

    matchs = []
    terrains = min(nb_terrains, len(hommes_dispo), len(femmes_dispo))
    for _ in range(terrains):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1, h2 = hommes_dispo.pop(), hommes_dispo.pop()
            f1, f2 = femmes_dispo.pop(), femmes_dispo.pop()
            equipe1 = [h1, f1]
            equipe2 = [h2, f2]
            matchs.append((equipe1, equipe2))

    st.session_state.matchs.append(matchs)

# --- Mise à jour classement ---
def maj_classement(matchs, scores):
    for idx, (equipe1, equipe2) in enumerate(matchs):
        score = scores.get(idx)
        if not score:
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
            st.session_state.joueurs[j]["Points"] += 3 + js_gagnants*0.1
            st.session_state.joueurs[j]["Jeux"] += js_gagnants
            st.session_state.joueurs[j]["Matchs"] += 1
        for j in perdants:
            st.session_state.joueurs[j]["Points"] += js_perdants*0.1
            st.session_state.joueurs[j]["Jeux"] += js_perdants
            st.session_state.joueurs[j]["Matchs"] += 1

# --- Affichage du classement ---
def afficher_classement():
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index")
    df = df.reset_index().rename(columns={"index": "Joueur"})
    df["Points"] = df["Points"].round(1)
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rang", df.index+1)
    st.table(df)

# --- PHASES FINALES ---
def generer_quarts():
    joueurs_trie = sorted(st.session_state.joueurs.items(),
                          key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True)
    qualifiés = [j[0] for j in joueurs_trie[:8]]
    random.shuffle(qualifiés)
    quarts = []
    while len(qualifiés) >= 4:
        h1 = next(j for j in qualifiés if st.session_state.joueurs[j]["Sexe"] == "H")
        qualifiés.remove(h1)
        f1 = next(j for j in qualifiés if st.session_state.joueurs[j]["Sexe"] == "F")
        qualifiés.remove(f1)
        h2 = next(j for j in qualifiés if st.session_state.joueurs[j]["Sexe"] == "H")
        qualifiés.remove(h2)
        f2 = next(j for j in qualifiés if st.session_state.joueurs[j]["Sexe"] == "F")
        qualifiés.remove(f2)
        quarts.append(([h1,f1],[h2,f2]))
    st.session_state.phases_finales["quarts"] = quarts

def jouer_phase(nom_phase, prochaine_phase):
    nouveaux = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales[nom_phase]):
        score = st.text_input(f"{nom_phase} Match {idx+1} : {e1} vs {e2}")
        if score:
            try:
                s1,s2 = map(int, score.split("-"))
                if s1 > s2: nouveaux.append(e1)
                else: nouveaux.append(e2)
            except:
                pass
    st.session_state.phases_finales[prochaine_phase] = []
    for i in range(0,len(nouveaux),2):
        if i+1 < len(nouveaux):
            st.session_state.phases_finales[prochaine_phase].append((nouveaux[i],nouveaux[i+1]))

# --- UI ---
st.title("🎾 Tournoi de Padel - Rétro Padel")

if st.button("⚡ Générer un nouveau round"):
    generer_round()

for r, matchs in enumerate(st.session_state.matchs,1):
    st.subheader(f"🏆 Round {r}")
    for idx,(e1,e2) in enumerate(matchs):
        st.write(f"⚔️ {e1[0]} (H) + {e1[1]} (F)  vs  {e2[0]} (H) + {e2[1]} (F)")
        st.session_state.scores[idx] = st.text_input(f"Score Round {r} Match {idx+1}",
                                                    key=f"score_{r}_{idx}")

if st.button("📊 Calculer le classement"):
    for r, matchs in enumerate(st.session_state.matchs):
        maj_classement(matchs, st.session_state.scores)
    afficher_classement()

# --- Phases finales ---
st.header("🏆 Phases Finales")
if st.button("⚡ Générer Quarts de finale"):
    generer_quarts()
if st.session_state.phases_finales["quarts"]:
    st.subheader("Quarts de finale")
    jouer_phase("quarts","demis")
if st.session_state.phases_finales["demis"]:
    st.subheader("Demi-finales")
    jouer_phase("demis","finale")
if st.session_state.phases_finales["finale"]:
    st.subheader("Finale")
    jouer_phase("finale","vainqueur")
    if "vainqueur" in st.session_state.phases_finales:
        st.success(f"🏆 Vainqueur : {st.session_state.phases_finales['vainqueur']}")

if st.button("♻️ Reset Phases Finales"):
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": []}
    st.success("Phases finales réinitialisées")
