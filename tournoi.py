# -*- coding: utf-8 -*-
import streamlit as st
import random
import pandas as pd

# =========================
#   PAGE + CSS (compact)
# =========================
st.set_page_config(page_title="🎾 Tournoi de Padel", page_icon="🎾", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 0.6rem; padding-bottom: 0.6rem; max-width: 1400px;}
      .stTable td, .stTable th {padding: .25rem .40rem !important;}
      .stExpander {border: 1px solid #eaeaea !important; margin-bottom: .35rem;}
      /* élargir la colonne Joueur dans les tableaux streamlit (meilleure lisibilité) */
      table {table-layout: auto;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
#   STATE
# =========================
def init_state():
    if "joueurs" not in st.session_state:
        st.session_state.joueurs = {}  # {nom: {"Points":0.0, "Jeux":0, "Matchs":0, "Sexe":"H/F"}}
    if "matchs" not in st.session_state:
        st.session_state.matchs = []   # rounds libres: [ [([H,F],[H,F]), ...], ... ]
    if "poules" not in st.session_state:
        st.session_state.poules = {
            "params": {"nb_poules": 2, "teams_per_pool": 4},
            "teams": [],        # liste de paires (H,F)
            "pools": [],        # [{ "teams":[indices], "matches":[(ti,tj),...]}]
            "main_bracket": [], # [[(team,team),...], ...]
            "cons_bracket": [], # [[(team,team),...], ...]
        }
    if "classement_calcule" not in st.session_state:
        st.session_state.classement_calcule = False
    if "mode" not in st.session_state:
        st.session_state.mode = "Rounds libres"

init_state()

# =========================
#   SIDEBAR
# =========================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150, key="txt_h")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150, key="txt_f")

hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"👨 **Hommes :** {len(hommes)}")
st.sidebar.markdown(f"👩 **Femmes :** {len(femmes)}")
st.sidebar.markdown(f"🎯 **Total :** {len(hommes)+len(femmes)}")
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Mode du tournoi",
    ["Rounds libres", "Poules + Élimination"],
    index=0 if st.session_state.mode=="Rounds libres" else 1
)
st.session_state.mode = mode

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 4)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur (Rounds libres)", 1, 20, 4)

if st.sidebar.button("🔄 Reset Tournoi Complet", use_container_width=True):
    st.session_state.clear()
    init_state()
    st.rerun()

# =========================
#   SYNCHRONISER JOUEURS
# =========================
def sync_joueurs():
    nouveaux = set(hommes + femmes)
    for j in list(st.session_state.joueurs.keys()):
        if j not in nouveaux:
            del st.session_state.joueurs[j]
    for h in hommes:
        if h not in st.session_state.joueurs:
            st.session_state.joueurs[h] = {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"H"}
    for f in femmes:
        if f not in st.session_state.joueurs:
            st.session_state.joueurs[f] = {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"F"}

sync_joueurs()

# =========================
#   OUTILS COMMUNS
# =========================
def render_table_compact(df):
    """Affiche en table compacte, 1 décimale pour Points si présent."""
    if "Points" in df.columns and len(df) > 0:
        df = df.copy()
        df["Points"] = df["Points"].map(lambda x: f"{float(x):.1f}")
    st.table(df)

def add_points(players, s_g, s_p, gagnants, perdants):
    """Barème : Gagnant 3 + 0.1*jeux ; Perdant 0.5 + 0.1*jeux (et MAJ jeux / matchs)."""
    for p in gagnants:
        players[p]["Points"] += 3.0 + s_g * 0.1
        players[p]["Jeux"]   += s_g
        players[p]["Matchs"] += 1
    for p in perdants:
        players[p]["Points"] += 0.5 + s_p * 0.1
        players[p]["Jeux"]   += s_p
        players[p]["Matchs"] += 1

def parse_score(s):
    try:
        a,b = map(int, s.strip().split("-"))
        return a,b
    except Exception:
        return None

# =========================
#   CLASSEMENT GENERAL
# =========================
def maj_classement_global():
    # reset
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"]   = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    # 1) Rounds libres
    for r, matches in enumerate(st.session_state.matchs, start=1):
        for m_idx, (e1, e2) in enumerate(matches):
            key = f"score_{r}_{m_idx}"
            raw = (st.session_state.get(key) or "").strip()
            sc = parse_score(raw)
            if not sc:
                continue
            s1, s2 = sc
            if s1 > s2:
                add_points(st.session_state.joueurs, s1, s2, e1, e2)
            else:
                add_points(st.session_state.joueurs, s2, s1, e2, e1)

    # 2) Poules (round-robin)
    pools = st.session_state.poules.get("pools", [])
    teams = st.session_state.poules.get("teams", [])
    for p_idx, pool in enumerate(pools):
        for m_idx, (ti, tj) in enumerate(pool.get("matches", [])):
            key = f"pool_{p_idx}_m_{m_idx}"
            raw = (st.session_state.get(key) or "").strip()
            sc = parse_score(raw)
            if not sc:
                continue
            s1, s2 = sc
            e1, e2 = teams[ti], teams[tj]
            if s1 > s2:
                add_points(st.session_state.joueurs, s1, s2, e1, e2)
            else:
                add_points(st.session_state.joueurs, s2, s1, e2, e1)

    # 3) Tableaux (main & consolante)
    for name in ("main_bracket", "cons_bracket"):
        bracket = st.session_state.poules.get(name, [])
        for r_idx, rnd in enumerate(bracket, start=1):
            for m_idx, (A, B) in enumerate(rnd):
                key = f"{name}_r{r_idx}_m{m_idx}"
                raw = (st.session_state.get(key) or "").strip()
                sc = parse_score(raw)
                if not sc:
                    continue
                s1, s2 = sc
                if s1 > s2:
                    add_points(st.session_state.joueurs, s1, s2, A, B)
                else:
                    add_points(st.session_state.joueurs, s2, s1, B, A)

def df_classement():
    """DataFrame classement robuste même si 0 joueur."""
    if not st.session_state.joueurs:
        return pd.DataFrame(columns=["Joueur","Sexe","Points","Jeux","Matchs"])
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index":"Joueur"}, inplace=True)
    if "Points" not in df.columns: df["Points"] = 0.0
    if "Jeux"   not in df.columns: df["Jeux"]   = 0
    if "Matchs" not in df.columns: df["Matchs"] = 0
    if "Sexe"   not in df.columns: df["Sexe"]   = ""
    df["Points"] = df["Points"].astype(float).round(1)
    df["Jeux"]   = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points","Jeux"], ascending=False).reset_index(drop=True)
    return df

# =========================
#   ROUNDS LIBRES
# =========================
def scheduled_counts_rounds():
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for e1, e2 in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

def generer_round():
    counts = scheduled_counts_rounds()
    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    H = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"]=="H"]
    F = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"]=="F"]

    rnd = random.random
    H.sort(key=lambda x:(counts[x], rnd()))
    F.sort(key=lambda x:(counts[x], rnd()))

    matches = []
    terrains = min(nb_terrains, len(H)//2, len(F)//2)
    for _ in range(terrains):
        if len(H)>=2 and len(F)>=2:
            h1,h2 = H.pop(0), H.pop(0)
            f1,f2 = F.pop(0), F.pop(0)
            matches.append(([h1,f1],[h2,f2]))
    if matches:
        st.session_state.matchs.append(matches)
        return True, len(matches)
    return False, 0

def generer_tous_rounds():
    n = 0
    while True:
        ok, nb = generer_round()
        if not ok or nb==0:
            break
        n += 1
    return n

def section_rounds_libres():
    st.title("🎾 Tournoi de Padel – Rounds libres")

    counts = scheduled_counts_rounds()
    H_elig = sum(1 for j in st.session_state.joueurs
                 if st.session_state.joueurs[j]["Sexe"]=="H" and counts[j]<max_matchs)
    F_elig = sum(1 for j in st.session_state.joueurs
                 if st.session_state.joueurs[j]["Sexe"]=="F" and counts[j]<max_matchs)
    terrains_theo = min(nb_terrains, H_elig//2, F_elig//2)

    if st.session_state.joueurs:
        maj_classement_global()
        df_now = df_classement()
        if df_now.empty:
            st.info(f"📊 Aucun joueur classé pour l’instant. Limite : {max_matchs} match(s).")
        else:
            st.info(
                f"📊 Matchs joués : min={df_now['Matchs'].min()}, "
                f"max={df_now['Matchs'].max()}, limite={max_matchs}"
            )
        st.info(f"🗓️ Éligibles (planifiés < {max_matchs}) → Hommes: {H_elig} | Femmes: {F_elig}")
    else:
        st.info("Ajoute des joueurs dans la barre latérale pour commencer.")

    c1, c2 = st.columns(2)
    with c1:
        if terrains_theo>0 and st.button("⚡ Générer 1 round", use_container_width=True):
            ok, nb = generer_round()
            if ok:
                st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nb} match(s))")
                st.rerun()
            else:
                st.warning("Aucun match supplémentaire possible.")
    with c2:
        if terrains_theo>0 and st.button("🚀 Générer TOUS les rounds", use_container_width=True):
            nb = generer_tous_rounds()
            if nb>0:
                st.success(f"✅ {nb} round(s) générés")
                st.rerun()
            else:
                st.warning("Aucun round supplémentaire possible.")

    if st.session_state.matchs:
        st.header("📋 Matchs")
        for r,matches in enumerate(st.session_state.matchs, start=1):
            with st.expander(f"🏆 Round {r} - {len(matches)} match(s)", expanded=(r==len(st.session_state.matchs))):
                for idx,(e1,e2) in enumerate(matches):
                    c1,c2 = st.columns([3,1])
                    with c1:
                        st.write(f"**Terrain {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  🆚  {e2[0]} (H)+{e2[1]} (F)")
                    with c2:
                        st.text_input("Score (ex: 6-4)", key=f"score_{r}_{idx}", label_visibility="collapsed")

    st.markdown("---")
    st.header("📈 Classement général")
    maj_classement_global()
    df = df_classement()
    if df.empty:
        st.info("Aucun résultat à afficher pour l’instant.")
    else:
        df.insert(0,"Rang", df.index+1)
        render_table_compact(df)

# =========================
#   POULES + ÉLIMINATION
# =========================
def make_pairs_for_pools(nb_pairs):
    """Tire nb_pairs paires H+F aléatoires."""
    H = hommes[:]
    F = femmes[:]
    random.shuffle(H); random.shuffle(F)
    nb = min(len(H), len(F), nb_pairs)
    teams = []
    for i in range(nb):
        teams.append( (H[i], F[i]) )
    return teams

def round_robin_indices(n):
    """Retourne la liste à plat des matches (paires d'indices) pour un round-robin de n équipes."""
    idxs = list(range(n))
    if n % 2 == 1:
        idxs.append(None)
        n += 1
    half = n // 2
    schedule = []
    rows = idxs[:]
    for _ in range(n - 1):
        pairings = []
        for i in range(half):
            a = rows[i]
            b = rows[n - 1 - i]
            if a is not None and b is not None:
                pairings.append((a, b))
        rows = [rows[0]] + [rows[-1]] + rows[1:-1]  # rotation
        schedule.extend(pairings)
    return schedule

def build_pools():
    nb_p = st.session_state.poules["params"]["nb_poules"]
    tpp  = st.session_state.poules["params"]["teams_per_pool"]
    total_needed = nb_p * tpp
    teams = make_pairs_for_pools(total_needed)
    if len(teams) < total_needed:
        st.error(f"Pas assez de joueurs pour {nb_p} poule(s) de {tpp} équipes (il faut {total_needed} paires H+F).")
        return False
    st.session_state.poules["teams"]  = teams
    pools = []
    all_ids = list(range(total_needed))
    for p in range(nb_p):
        pool_ids = all_ids[p*tpp:(p+1)*tpp]
        rr = round_robin_indices(tpp)
        matches = []
        for (a,b) in rr:
            matches.append((pool_ids[a], pool_ids[b]))
        pools.append({"teams": pool_ids, "matches": matches})
    st.session_state.poules["pools"] = pools
    st.session_state.poules["main_bracket"] = []
    st.session_state.poules["cons_bracket"] = []
    return True

def render_pools():
    st.subheader("📦 Poules")
    teams = st.session_state.poules["teams"]
    pools = st.session_state.poules["pools"]

    main_candidates = []
    cons_candidates = []

    for p_idx, pool in enumerate(pools):
        with st.expander(f"🏁 Poule {p_idx+1} – {len(pool['teams'])} équipes", expanded=True):
            st.markdown("**Équipes :** " + ", ".join([f"{teams[i][0]}+{teams[i][1]}" for i in pool["teams"]]))

            for m_idx, (ti, tj) in enumerate(pool["matches"]):
                e1, e2 = teams[ti], teams[tj]
                c1,c2 = st.columns([3,1])
                with c1:
                    st.write(f"**Match {m_idx+1}:** {e1[0]}+{e1[1]} 🆚 {e2[0]}+{e2[1]}")
                with c2:
                    st.text_input("Score (ex: 6-4)", key=f"pool_{p_idx}_m_{m_idx}", label_visibility="collapsed")

            # Classement interne de poule (évolutif)
            scores = []
            for ti in pool["teams"]:
                scores.append({"team": ti, "Pts": 0.0, "Jeux": 0})

            def idx_of(team_id):
                for k,d in enumerate(scores):
                    if d["team"] == team_id: return k
                return None

            for m_idx, (ti, tj) in enumerate(pool["matches"]):
                raw = (st.session_state.get(f"pool_{p_idx}_m_{m_idx}") or "").strip()
                sc = parse_score(raw)
                if not sc: continue
                s1, s2 = sc
                iA = idx_of(ti); iB = idx_of(tj)
                if s1 > s2:
                    scores[iA]["Pts"] += 3.0 + s1*0.1
                    scores[iB]["Pts"] += 0.5 + s2*0.1
                else:
                    scores[iB]["Pts"] += 3.0 + s2*0.1
                    scores[iA]["Pts"] += 0.5 + s1*0.1
                scores[iA]["Jeux"] += s1; scores[iB]["Jeux"] += s2

            scores = sorted(scores, key=lambda x:(x["Pts"], x["Jeux"]), reverse=True)
            dfp = pd.DataFrame([{
                "Equipe": f"{teams[d['team']][0]}+{teams[d['team']][1]}",
                "Points": round(d["Pts"],1),
                "Jeux": d["Jeux"],
            } for d in scores])
            dfp.index = dfp.index + 1
            st.caption("Classement de la poule (évolutif)")
            render_table_compact(dfp)

            if len(scores) >= 2:
                main_candidates += [teams[scores[0]["team"]], teams[scores[1]["team"]]]
            if len(scores) >= 4:
                cons_candidates += [teams[scores[2]["team"]], teams[scores[3]["team"]]]

    c1,c2 = st.columns(2)
    with c1:
        if st.button("🎲 Générer tableaux (principal & consolante)"):
            if len(main_candidates) >= 4:
                tmp = main_candidates[:]
                random.shuffle(tmp)
                first_round = []
                for i in range(0, len(tmp), 2):
                    if i+1 < len(tmp):
                        first_round.append((tmp[i], tmp[i+1]))
                st.session_state.poules["main_bracket"] = [first_round]
            else:
                st.warning("Pas assez d’équipes pour un tableau principal.")

            if len(cons_candidates) >= 4:
                tmpc = cons_candidates[:]
                random.shuffle(tmpc)
                first_round_c = []
                for i in range(0, len(tmpc), 2):
                    if i+1 < len(tmpc):
                        first_round_c.append((tmpc[i], tmpc[i+1]))
                st.session_state.poules["cons_bracket"] = [first_round_c]
            st.rerun()
    with c2:
        if st.button("♻️ Reset tableaux"):
            st.session_state.poules["main_bracket"] = []
            st.session_state.poules["cons_bracket"] = []
            st.success("Tableaux réinitialisés")
            st.rerun()

def render_bracket(title, key_prefix, bracket):
    st.subheader(f"📈 {title}")
    if not bracket:
        st.info("Aucun tour pour le moment.")
        return

    for r_idx, rnd in enumerate(bracket, start=1):
        with st.expander(f"Tour {r_idx} – {len(rnd)} match(s)", expanded=(r_idx==len(bracket))):
            for m_idx, (A,B) in enumerate(rnd):
                c1,c2 = st.columns([3,1])
                with c1:
                    st.write(f"{A[0]}+{A[1]}  🆚  {B[0]}+{B[1]}")
                with c2:
                    st.text_input("Score (ex: 6-4)", key=f"{key_prefix}_r{r_idx}_m{m_idx}", label_visibility="collapsed")

            if r_idx == len(bracket):
                if st.button(f"✅ Valider le Tour {r_idx} ({title})"):
                    winners = []
                    ok_all = True
                    for m_idx, (A,B) in enumerate(rnd):
                        raw = (st.session_state.get(f"{key_prefix}_r{r_idx}_m{m_idx}") or "").strip()
                        sc = parse_score(raw)
                        if not sc:
                            ok_all = False
                            break
                        s1,s2 = sc
                        winners.append(A if s1>s2 else B)
                    if not ok_all or len(winners)<2:
                        st.warning("Veuillez compléter tous les scores du tour.")
                    else:
                        random.shuffle(winners)
                        next_round = []
                        for i in range(0, len(winners), 2):
                            if i+1 < len(winners):
                                next_round.append((winners[i], winners[i+1]))
                        if next_round:
                            bracket.append(next_round)
                            st.success("Tour suivant créé (tirage aléatoire).")
                            st.rerun()

def section_poules():
    st.title("🎾 Tournoi de Padel – Poules + Élimination")

    nb_p = st.number_input("Nombre de poules", 1, 16,
                           value=st.session_state.poules["params"]["nb_poules"], key="nb_poules")
    tpp  = st.number_input("Équipes par poule (paires H+F)", 2, 12,
                           value=st.session_state.poules["params"]["teams_per_pool"], key="teams_per_pool")
    st.session_state.poules["params"]["nb_poules"] = int(nb_p)
    st.session_state.poules["params"]["teams_per_pool"] = int(tpp)

    if st.button("⚡ Créer / Recréer les poules", type="primary"):
        if build_pools():
            st.success("Poules générées.")
            st.rerun()

    if st.session_state.poules["pools"]:
        render_pools()

    st.markdown("---")
    st.header("🏆 Tableaux à élimination directe")
    render_bracket("Tableau principal", "main_bracket", st.session_state.poules["main_bracket"])
    render_bracket("Tableau consolante", "cons_bracket", st.session_state.poules["cons_bracket"])

    st.markdown("---")
    st.header("📈 Classement général (agrégé)")
    maj_classement_global()
    df = df_classement()
    if df.empty:
        st.info("Aucun résultat à afficher pour l’instant.")
    else:
        df.insert(0,"Rang", df.index+1)
        render_table_compact(df)

# =========================
#   ROUTAGE
# =========================
if st.session_state.mode == "Rounds libres":
    section_rounds_libres()
else:
    section_poules()
