# -*- coding: utf-8 -*-
import streamlit as st
import random
import math
import pandas as pd

# ============================================================
#  CONFIG
# ============================================================
st.set_page_config(page_title="🎾 Tournoi de Padel", page_icon="🎾", layout="wide")

# ===== CSS COMPACT (colonnes serrées) =====
COMPACT_CSS = """
<style>
[data-testid="stAppViewContainer"] .main{max-width:920px;padding:0.4rem 0.8rem;margin:0 auto;}
div.block-container{padding:0.35rem 0.8rem;}
h1,h2,h3{margin:0.35rem 0 0.25rem 0;line-height:1.15;}
section.main .element-container{margin-bottom:0.38rem;}
div[data-testid="stExpander"] details summary{padding:0.16rem 0.5rem !important;font-size:0.92rem !important;line-height:1.05 !important;}
div[data-testid="stExpander"] div[role="region"]{padding:0.30rem 0.5rem !important;font-size:0.93rem !important;}
div[data-testid="stTextInput"]{max-width:96px;}
div[data-testid="stTextInput"] input{padding:0.22rem 0.35rem !important;min-height:1.65rem !important;font-size:0.88rem !important;}
.stButton>button{padding:0.26rem 0.54rem !important;font-size:0.90rem !important;}
div[data-testid="stTable"] table{table-layout:fixed;width:100%;font-size:0.90rem !important;}
div[data-testid="stTable"] th,div[data-testid="stTable"] td{padding:0.12rem 0.28rem !important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
div[data-testid="stTable"] th:nth-child(1){width:56px;}
div[data-testid="stTable"] th:nth-child(2){width:170px;}
div[data-testid="stTable"] th:nth-child(3){width:44px;}
div[data-testid="stTable"] th:nth-child(4){width:64px;}
div[data-testid="stTable"] th:nth-child(5){width:56px;}
div[data-testid="stTable"] th:nth-child(6){width:64px;}
div[data-testid="stSidebar"] div[data-testid="stNumberInput"] input{padding:0.18rem 0.35rem !important;min-height:1.6rem !important;font-size:0.88rem !important;}
</style>
"""
st.markdown(COMPACT_CSS, unsafe_allow_html=True)

# ============================================================
#  SESSION STATE
# ============================================================
def ensure_state():
    ss = st.session_state
    ss.setdefault("joueurs", {})                 # joueurs bruts (rounds libres)
    ss.setdefault("matchs", [])                  # rounds libres : liste de rounds -> liste de matchs
    ss.setdefault("scores", {})                  # scores rounds libres
    ss.setdefault("classement_calcule", False)

    # Mode / Poules
    ss.setdefault("mode", "Rounds libres")       # "Rounds libres" | "Poules + Élimination"
    ss.setdefault("equipes", [])                 # équipes (paires) [(H,F),...]
    ss.setdefault("poules", [])                  # [[team_idx,...], ...]
    ss.setdefault("poules_matchs", [])           # par poule : [rounds] -> [matchs (team_idx, team_idx)]
    ss.setdefault("poules_scores", {})           # scores des matchs de poule
    ss.setdefault("poules_stats", {})            # stats par equipe pendant poule

    # Tableaux (élimination)
    ss.setdefault("main_bracket", {"rounds": [], "current": 0})   # rounds: list of list of (team, team)
    ss.setdefault("cons_bracket", {"rounds": [], "current": 0})
ensure_state()

# ============================================================
#  SIDEBAR PARAMS
# ============================================================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150, key="hommes_input")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150, key="femmes_input")

def clean_lines(x): 
    return [s.strip() for s in x.splitlines() if s.strip()]

hommes = clean_lines(st.session_state.hommes_input)
femmes = clean_lines(st.session_state.femmes_input)

st.sidebar.markdown("---")
st.sidebar.markdown(f"👨 **Hommes :** {len(hommes)}")
st.sidebar.markdown(f"👩 **Femmes :** {len(femmes)}")
st.sidebar.markdown(f"🎯 **Total :** {len(hommes)+len(femmes)}")
st.sidebar.markdown("---")

# Mode
st.session_state.mode = st.sidebar.radio(
    "Mode du tournoi", 
    ["Rounds libres", "Poules + Élimination"], 
    horizontal=False
)

# Paramètres communs / rounds libres
nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 12, 4)
max_matchs   = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Tournoi Complet"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    ensure_state()
    st.success("✅ Tournoi réinitialisé")
    st.experimental_rerun()

# ============================================================
#  UTILS (généraux)
# ============================================================
def pair_name(team):
    if team is None: 
        return "—"
    return f"{team[0]} (H) + {team[1]} (F)"

def score_to_tuple(txt):
    try:
        if not txt or "-" not in txt: 
            return None
        s1, s2 = txt.split("-")
        return int(s1.strip()), int(s2.strip())
    except:
        return None

def apply_points(stat, win_games, lose_games, win=True):
    """Points: gagnants = 3 + 0.1*jeux ; perdants = 0.5"""
    if win:
        stat["Points"] += 3.0 + 0.1*win_games
        stat["Jeux"]   += win_games
    else:
        stat["Points"] += 0.5
        stat["Jeux"]   += lose_games
    stat["Matchs"] += 1

def standings_df(stats, teams_idx, equipes_map):
    """Retourne un DataFrame (Rang, Equipe, Points, Jeux, Matchs) trié."""
    rows = []
    for i in teams_idx:
        key = tuple(equipes_map[i])
        s = stats.setdefault(key, {"Points":0.0,"Jeux":0,"Matchs":0})
        rows.append([pair_name(equipes_map[i]), s["Points"], s["Jeux"], s["Matchs"]])
    df = pd.DataFrame(rows, columns=["Équipe","Points","Jeux","Matchs"])
    df["Points"] = df["Points"].round(1)
    df = df.sort_values(["Points","Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rang", df.index+1)
    df["Points"] = df["Points"].map(lambda x: f"{x:.1f}")
    return df

# ============================================================
#  MODE 1 : ROUNDS LIBRES (reprend ton fonctionnement)
# ============================================================
def sync_joueurs_rounds():
    # synchro des listes texte avec dict joueurs
    joueurs = st.session_state.joueurs
    new = set(hommes + femmes)
    for j in list(joueurs.keys()):
        if j not in new: del joueurs[j]
    for h in hommes:
        if h not in joueurs: joueurs[h] = {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"H"}
    for f in femmes:
        if f not in joueurs: joueurs[f] = {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"F"}

def scheduled_counts_rounds():
    counts = {j:0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for (e1, e2) in rnd:
            for p in e1 + e2:
                if p in counts: counts[p]+=1
    return counts

def generer_round():
    counts = scheduled_counts_rounds()
    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    H = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"]=="H"]
    F = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"]=="F"]
    rnd = random.random
    H.sort(key=lambda x:(counts[x], rnd())); F.sort(key=lambda x:(counts[x], rnd()))
    matches = []
    terrains = min(nb_terrains, len(H)//2, len(F)//2)
    for _ in range(terrains):
        if len(H)>=2 and len(F)>=2:
            h1,h2 = H.pop(0), H.pop(0)
            f1,f2 = F.pop(0), F.pop(0)
            c = scheduled_counts_rounds()
            if max(c.get(h1,0),c.get(h2,0),c.get(f1,0),c.get(f2,0)) >= max_matchs:
                continue
            matches.append(([h1,f1],[h2,f2]))
    if matches:
        st.session_state.matchs.append(matches)
        return True, len(matches)
    return False, 0

def generer_tous_rounds():
    n=0
    while True:
        ok, nb = generer_round()
        if not ok or nb==0: break
        n+=1
    return n

def maj_classement_rounds():
    # reset
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"]=0.0
        st.session_state.joueurs[j]["Jeux"]=0
        st.session_state.joueurs[j]["Matchs"]=0
    # recalc
    for ridx, rnd in enumerate(st.session_state.matchs):
        for midx, (e1,e2) in enumerate(rnd):
            key = f"score_{ridx+1}_{midx}"
            sc = st.session_state.scores.get(key,"")
            tup = score_to_tuple(sc)
            if not tup: continue
            s1,s2 = tup
            if s1>s2:
                winners, losers, wg, lg = e1, e2, s1, s2
            else:
                winners, losers, wg, lg = e2, e1, s2, s1
            for p in winners:
                st.session_state.joueurs[p]["Points"]+=3.0+0.1*wg
                st.session_state.joueurs[p]["Jeux"]+=wg
                st.session_state.joueurs[p]["Matchs"]+=1
            for p in losers:
                st.session_state.joueurs[p]["Points"]+=0.5
                st.session_state.joueurs[p]["Jeux"]+=lg
                st.session_state.joueurs[p]["Matchs"]+=1

def classement_table():
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index":"Joueur"}, inplace=True)
    df["Points"] = df["Points"].round(1).map(lambda x:f"{x:.1f}")
    df["Jeux"]   = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(["Points","Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0,"Rang", df.index+1)
    st.table(df[["Rang","Joueur","Sexe","Points","Jeux","Matchs"]])

# ============================================================
#  MODE 2 : POULES + ÉLIMINATION
# ============================================================
def generer_equipes():
    """Crée des paires (H,F) au hasard."""
    H = hommes[:]; F = femmes[:]
    random.shuffle(H); random.shuffle(F)
    nb = min(len(H),len(F))
    return [(H[i],F[i]) for i in range(nb)]

def make_poules(equipes, nb_poules, equipes_par_poule):
    """Renvoie la liste de poules (indices d’équipes) et les équipes utilisées."""
    total = nb_poules*equipes_par_poule
    if total > len(equipes):
        return None, f"Il faut {total} équipes mais vous n'en avez que {len(equipes)}."
    idx = list(range(total))
    random.shuffle(idx)
    poules = []
    for p in range(nb_poules):
        poules.append(idx[p*equipes_par_poule:(p+1)*equipes_par_poule])
    return poules, None

def round_robin(indices):
    """Génère un round-robin sur une liste d'indices d'équipes.
       Retourne : [ [ (i1,i2), (i3,i4), ... ], ... ] (une liste de rounds)."""
    teams = indices[:]
    bye = None
    if len(teams)%2==1:
        teams.append(None)  # bye
    n = len(teams)
    rounds = []
    arr = teams[:]
    for r in range(n-1):
        pairs=[]
        for i in range(n//2):
            a = arr[i]; b = arr[n-1-i]
            if a is None or b is None:
                continue
            pairs.append((a,b))
        rounds.append(pairs)
        # rotation
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    return rounds

def build_bracket(teams, avoid_groups=None):
    """Construit un tableau d'élimination directe avec byes si besoin.
       teams: liste d'équipes (objets équipe [H,F]) OU tuples (H,F).
       avoid_groups: dict équipe->poule pour éviter 1er tour mêmes poules (facultatif)."""
    t = teams[:]
    random.shuffle(t)

    # Essaie de mélanger tant que des matches 1er tour ne sont pas de même poule (si avoid_groups)
    if avoid_groups:
        for _ in range(2000):
            ok=True
            for i in range(0,len(t),2):
                if i+1>=len(t): break
                a,b = t[i], t[i+1]
                if avoid_groups.get(tuple(a))==avoid_groups.get(tuple(b)):
                    ok=False; break
            if ok: break
            random.shuffle(t)

    # power-of-two padding
    n = len(t)
    next_pow = 1<<(n-1).bit_length()
    for _ in range(next_pow-n):
        t.append(None)

    # Round 1
    r1=[]
    for i in range(0,len(t),2):
        r1.append((t[i], t[i+1]))
    return {"rounds":[r1], "current":0}

def advance_bracket(bracket, score_prefix):
    """Lit les scores du round courant et crée le round suivant avec les vainqueurs."""
    cur = bracket["current"]
    rounds = bracket["rounds"]
    if cur>=len(rounds): 
        return False

    winners=[]
    for midx, (A,B) in enumerate(rounds[cur]):
        if A is None and B is None:
            winners.append(None); continue
        if A is None: winners.append(B); continue
        if B is None: winners.append(A); continue
        key = f"{score_prefix}_R{cur+1}_M{midx}"
        sc = st.session_state.get(key,"")
        tup = score_to_tuple(sc)
        if not tup: 
            st.warning("⚠️ Renseigne tous les scores de ce tour pour continuer.")
            return False
        s1,s2 = tup
        winners.append(A if s1>s2 else B)

    # Si un seul vainqueur → fin
    if len(winners)==1:
        bracket["rounds"].append([])  # garde trace d'une finale jouée
        bracket["current"] += 1
        bracket["winner"] = winners[0]
        return True

    # Compléter à puissance de 2 si byes (None)
    n = len(winners)
    next_pow = 1<<(n-1).bit_length()
    winners = winners + [None]*(next_pow-n)

    nxt=[]
    for i in range(0,len(winners),2):
        nxt.append((winners[i], winners[i+1]))
    bracket["rounds"].append(nxt)
    bracket["current"] += 1
    return True

# ============================================================
#  UI
# ============================================================
st.title("🎾 Tournoi de Padel")

# ----------------- MODE ROUNDS LIBRES -----------------
if st.session_state.mode == "Rounds libres":
    # synchro joueurs
    sync_joueurs_rounds()
    counts = scheduled_counts_rounds()
    H_elig = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="H" and counts[j]<max_matchs)
    F_elig = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="F" and counts[j]<max_matchs)
    terrains_theo = min(nb_terrains, H_elig//2, F_elig//2)

    if terrains_theo>0:
        c1,c2 = st.columns(2)
        with c1:
            if st.button("⚡ Générer 1 round", use_container_width=True):
                ok, nb = generer_round()
                if ok: st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nb} match(s))")
                else: st.error("❌ Impossible de générer un round")
        with c2:
            if st.button("🚀 Générer TOUS les rounds", use_container_width=True):
                nb = generer_tous_rounds()
                if nb>0: st.success(f"✅ {nb} round(s) générés automatiquement")
                else: st.warning("⚠️ Aucun round supplémentaire possible")
    else:
        st.info(f"ℹ️ Tous les joueurs éligibles ont atteint le maximum planifié ({max_matchs}).")

    # Affichage des rounds & saisie de scores
    if st.session_state.matchs:
        st.header("📋 Matchs du tournoi")
        for r, rnd in enumerate(st.session_state.matchs,1):
            with st.expander(f"🏆 Round {r} - {len(rnd)} match(s)", expanded=(r==len(st.session_state.matchs))):
                for m,(e1,e2) in enumerate(rnd):
                    c1,c2 = st.columns([3,1])
                    with c1: st.write(f"**Terrain {m+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
                    with c2:
                        key = f"score_{r}_{m}"
                        st.session_state.scores[key] = st.text_input("Score (ex: 6-4)", key=key, label_visibility="collapsed")

        if st.button("📊 Calculer le classement"):
            maj_classement_rounds()
            st.session_state.classement_calcule = True

    # Classement général
    if st.session_state.joueurs:
        st.header("📈 Classement général")
        maj_classement_rounds()
        classement_table()

# ----------------- MODE POULES + ELIMINATION -----------------
else:
    st.subheader("🧩 Paramètres des poules")

    # Sélection poules
    nb_poules = st.number_input("Nombre de poules", 1, 16, 4, key="nb_poules")
    taille_ok = [4,5,6,8,9,10]
    equipes_par_poule = st.selectbox("Équipes par poule (paires H+F)", options=taille_ok, index=0, key="eq_par_poule")

    if st.button("🎲 Générer équipes & poules", type="primary"):
        equipes = generer_equipes()
        st.session_state.equipes = equipes[:]
        poules, err = make_poules(equipes, nb_poules, equipes_par_poule)
        if err:
            st.error(f"❌ {err}")
        else:
            st.session_state.poules = poules
            # matchs de poule
            st.session_state.poules_matchs = [ round_robin(p) for p in poules ]
            st.session_state.poules_scores = {}
            st.session_state.poules_stats  = {}

            # reset tableaux
            st.session_state.main_bracket = {"rounds": [], "current": 0}
            st.session_state.cons_bracket = {"rounds": [], "current": 0}

    # Affichage Poules
    if st.session_state.poules:
        equipes = st.session_state.equipes
        poules  = st.session_state.poules
        poules_matchs = st.session_state.poules_matchs
        stats = st.session_state.poules_stats

        st.header("🏟️ Poules")
        for pid, rounds in enumerate(poules_matchs):
            with st.expander(f"🅿️ Poule {pid+1} — {len(poules[pid])} équipes — {len(rounds)} journées", expanded=False):
                # Rounds
                for ridx, rmatches in enumerate(rounds):
                    st.caption(f"Journée {ridx+1}")
                    cols = st.columns( len(rmatches) if len(rmatches)>0 else 1 )
                    for i,(a,b) in enumerate(rmatches):
                        with cols[i if i<len(cols) else -1]:
                            st.write(f"**{pair_name(equipes[a])}**  🆚  **{pair_name(equipes[b])}**")
                            key = f"pool_{pid}_R{ridx}_M{i}"
                            val = st.session_state.poules_scores.get(key,"")
                            st.session_state.poules_scores[key] = st.text_input("Score", value=val, key=key, label_visibility="collapsed")

                # Classement poule
                # Calcul à la volée depuis les scores saisis
                # Reset stats poule
                for idx in poules[pid]:
                    stats.setdefault(tuple(equipes[idx]), {"Points":0.0,"Jeux":0,"Matchs":0})
                    s = stats[tuple(equipes[idx])]
                    s["Points"]=0.0; s["Jeux"]=0; s["Matchs"]=0

                for ridx, rmatches in enumerate(rounds):
                    for midx,(a,b) in enumerate(rmatches):
                        key = f"pool_{pid}_R{ridx}_M{midx}"
                        tup = score_to_tuple(st.session_state.poules_scores.get(key,""))
                        if not tup: continue
                        s1,s2 = tup
                        A,B = tuple(equipes[a]), tuple(equipes[b])
                        if s1>s2:
                            apply_points(stats[A], s1, s2, True)
                            apply_points(stats[B], s1, s2, False)
                        else:
                            apply_points(stats[B], s2, s1, True)
                            apply_points(stats[A], s2, s1, False)

                df = standings_df(stats, poules[pid], equipes)
                st.table(df)

        st.markdown("---")
        if st.button("➡️ Calculer classements & préparer les tableaux"):
            # Top2 -> tableau principal ; 3e-4e -> consolante (si existent)
            equipes = st.session_state.equipes
            poules  = st.session_state.poules
            stats   = st.session_state.poules_stats

            main_teams = []
            cons_teams = []
            grp_of = {}  # équipe -> id poule
            for pid, lst in enumerate(poules):
                # classe les équipes de la poule
                df = standings_df(stats, lst, equipes)
                order = []
                for _,r in df.iterrows():
                    # retrouver l'équipe (tuple) depuis le nom texte
                    # plus simple : recalc tri localement pour robustesse
                    pass
                # on retrie via stats directement
                sub = []
                for idx in lst:
                    s = stats[tuple(equipes[idx])]
                    sub.append((idx, s["Points"], s["Jeux"]))
                sub.sort(key=lambda x:(x[1],x[2]), reverse=True)
                ordered_idx = [x[0] for x in sub]

                # mapping poule
                for idx in ordered_idx:
                    grp_of[tuple(equipes[idx])] = pid

                # Top2 -> main ; 3e-4e -> cons si présents
                top = ordered_idx[:2]
                main_teams += [equipes[i] for i in top]
                if len(ordered_idx)>=4:
                    cons = ordered_idx[2:4]
                    cons_teams += [equipes[i] for i in cons]

            # Construire les tableaux avec évitement 1er tour même poule
            st.session_state.main_bracket = build_bracket(main_teams, avoid_groups=grp_of)
            st.session_state.cons_bracket = build_bracket(cons_teams, avoid_groups=grp_of) if len(cons_teams)>=2 else {"rounds": [], "current":0}
            st.success("✅ Tableaux générés. Renseigne les scores de chaque tour puis valide pour avancer.")

        # ----- Affichage tableaux -----
        def render_bracket(title, key_prefix, bracket):
            if not bracket["rounds"]:
                st.info(f"Aucun {title.lower()} pour le moment.")
                return
            st.subheader(title)
            R = bracket["rounds"]
            cur = bracket["current"]
            # Affiche tous les tours déjà créés (jusqu'au courant)
            for ridx in range(0, cur+1):
                st.write(f"**Tour {ridx+1}**")
                cols = st.columns(len(R[ridx]) if len(R[ridx])>0 else 1)
                for midx,(A,B) in enumerate(R[ridx]):
                    with cols[midx if midx<len(cols) else -1]:
                        st.write(f"{pair_name(A)}  🆚  {pair_name(B)}")
                        key = f"{key_prefix}_R{ridx+1}_M{midx}"
                        st.session_state.setdefault(key,"")
                        st.session_state[key] = st.text_input("Score", value=st.session_state[key], key=key, label_visibility="collapsed")

            # Bouton avancer
            if st.button(f"✅ Valider le Tour {cur+1} ({title})"):
                ok = advance_bracket(bracket, key_prefix)
                if ok:
                    if "winner" in bracket:
                        st.success(f"🏆 Vainqueur {title} : {pair_name(bracket['winner'])}")
                    st.experimental_rerun()

        st.markdown("---")
        render_bracket("Tableau principal", "main", st.session_state.main_bracket)
        render_bracket("Consolante", "cons", st.session_state.cons_bracket)

