"""Net Zero Portfolio Game · Streamlit app (individual play).

Run locally:  streamlit run app.py
Players use the "Play" page; the game master uses "Game master" (password protected).
All companies and figures are fictional.
"""
import html
import os

import altair as alt
import pandas as pd
import streamlit as st

import engine as e
import storage as db

st.set_page_config(page_title="Net Zero Portfolio Game", page_icon="🌍", layout="wide")
db.init()

# ------------------------------------------------------------------ look and feel (Credibl brand)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@500;600;700&family=Open+Sans:wght@400;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, li, label, input, button, td, th { font-family: 'Open Sans', Arial, sans-serif; }
h1, h2, h3, h4 { font-family: 'Zilla Slab', Georgia, serif !important; color: #152139 !important; font-weight: 600 !important; }
.kicker { font: 600 12px 'Open Sans', Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; color: #366EB5; margin-bottom: 2px; }
.hero { background: #152139; color: #fff; padding: 22px 26px; border-radius: 8px; margin-bottom: 14px; }
.hero h1 { color: #fff !important; margin: 4px 0 6px 0; font-size: 34px; }
.hero p { color: #E8F3F6; margin: 0; font-size: 15px; }
.hero .kicker { color: #5EC4E4; }
.phase { background: #E8F3F6; border-radius: 8px; padding: 14px 18px; margin: 6px 0 14px 0; color: #1C3B69; font-size: 15px; }
.phase b { color: #152139; }
.phase.closed { background: #F3F3F3; }
.stat { background: #E8F3F6; border-radius: 8px; padding: 12px 16px; }
.stat .lab { font: 600 11px 'Open Sans', Arial, sans-serif; letter-spacing: .1em; text-transform: uppercase; color: #6B7280; }
.stat .val { font: 700 28px 'Zilla Slab', Georgia, serif; color: #366EB5; line-height: 1.15; }
.stat .sub { font-size: 12px; color: #6B7280; }
.ok { color: #3E7F33; font-weight: 600; } .bad { color: #B23A2E; font-weight: 600; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 14px; }
.card { border: 1px solid #D9DEE4; border-radius: 8px; overflow: hidden; background: #fff; }
.card .top { background: #152139; padding: 12px 16px; }
.card .top .kicker { color: #5EC4E4; font-size: 11px; }
.card .top .nm { font: 600 20px 'Zilla Slab', Georgia, serif; color: #fff; }
.card .top .sec { color: #E8F3F6; font-size: 13px; }
.card .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 12px 16px 4px 16px; }
.card .tile { background: #E8F3F6; border-radius: 6px; padding: 8px 10px; }
.card .tile .lab { font: 600 10px 'Open Sans', Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; color: #6B7280; }
.card .tile .v { font: 700 19px 'Zilla Slab', Georgia, serif; color: #1C3B69; }
.card .note { padding: 6px 16px 14px 16px; font-size: 13.5px; color: #1D1D1B; }
.card .note .kicker { font-size: 10px; }
.badge { display: inline-block; background: #FCE9E6; color: #B23A2E; font: 600 11px 'Open Sans', Arial, sans-serif; padding: 2px 8px; border-radius: 999px; margin-top: 6px; }
table.lb { width: 100%; border-collapse: collapse; font-size: 15px; }
table.lb th { background: #1C3B69; color: #fff; text-align: left; padding: 8px 10px; font-weight: 600; }
table.lb td { padding: 8px 10px; border-bottom: 1px solid #D9DEE4; }
table.lb tr.me td { background: #E8F3F6; font-weight: 600; }
table.lb td.num { text-align: right; font-variant-numeric: tabular-nums; }
table.lb.big { font-size: 22px; } table.lb.big td, table.lb.big th { padding: 12px 14px; }
.news { border-left: 4px solid #366EB5; background: #F7F9FB; padding: 12px 16px; border-radius: 4px; margin-bottom: 12px; }
.news .when { font: 600 11px 'Open Sans', Arial, sans-serif; letter-spacing: .1em; text-transform: uppercase; color: #366EB5; }
.news .hl { font: 600 20px 'Zilla Slab', Georgia, serif; color: #152139; margin: 2px 0 4px 0; }
.foot { color: #6B7280; font-size: 12px; margin-top: 24px; }
.lbwrap { overflow-x: auto; }
@media (max-width: 640px) { table.lb .dept { display: none; } table.lb.big { font-size: 16px; } }
</style>
""", unsafe_allow_html=True)

RS = "₹"


def esc(s):
    return html.escape(str(s))


def stat(label, value, sub=""):
    return f'<div class="stat"><div class="lab">{esc(label)}</div><div class="val">{value}</div><div class="sub">{sub}</div></div>'


def phase_text(revealed, is_open):
    nxt = revealed + 1
    if revealed >= e.ROUNDS:
        return False, "<b>Game over.</b> The final market close has happened. See the final leaderboard."
    if is_open:
        extra = (" <b>This is your FINAL lock:</b> your portfolio must be within the carbon budget to win."
                 if nxt == e.ROUNDS else " You can change it as often as you like until the game master closes the round.")
        return True, f"<b>Round {nxt} is open</b> ({e.ROUND_LABEL[nxt]}): lock your portfolio.{extra}"
    return False, f"<b>Submissions are closed.</b> Waiting for news {nxt} from the game master."


def company_cards(revealed):
    out = ['<div class="cards">']
    for i, c in enumerate(e.CO):
        corrected = revealed >= 3 and c["true"] != c["rep"]
        inten = e.known_intensity(i, revealed); plan = e.known_plan(i, revealed)
        badge = '<div class="badge">Corrected after investigation</div>' if corrected else ""
        out.append(f"""
        <div class="card"><div class="top"><div class="kicker">Company {i + 1:02d}</div>
        <div class="nm">{esc(c['name'])}</div><div class="sec">{esc(c['sector'])}</div>{badge}</div>
        <div class="grid">
          <div class="tile"><div class="lab">Expected return</div><div class="v">{c['base'] * 100:.0f}%</div></div>
          <div class="tile"><div class="lab">Intensity</div><div class="v">{inten:g}</div></div>
          <div class="tile"><div class="lab">Transition plan</div><div class="v">{esc(plan)}</div></div>
          <div class="tile"><div class="lab">Physical risk</div><div class="v">{esc(c['risk'])}</div></div>
        </div>
        <div class="note"><div class="kicker">Analyst note</div>{esc(c['clue'])}</div></div>""")
    out.append("</div>")
    return "".join(out)


def leaderboard_html(rows, revealed, me=None, top=10, big=False):
    if revealed == 0:
        return "<p>No results yet. The leaderboard appears after the first news item.</p>"
    if not rows:
        return "<p>No portfolios locked yet.</p>"
    final = revealed >= e.ROUNDS
    shown = rows[:top]
    if me is not None and all(r["pid"] != me for r in shown):
        shown = shown + [r for r in rows if r["pid"] == me]
    head = ("<tr><th>Rank</th><th>Player</th><th class='dept'>Department</th><th style='text-align:right'>Value (" + RS +
            " cr)</th><th style='text-align:right'>Change</th><th style='text-align:right'>Intensity</th><th>Budget</th>"
            + ("<th style='text-align:right'>Points</th>" if final else "") + "</tr>")
    body = []
    for r in shown:
        status = '<span class="ok">Within</span>' if r["within"] else '<span class="bad">Over</span>'
        body.append(
            f"<tr class='{'me' if r['pid'] == me else ''}'><td>{r['rank']}</td><td>{esc(r['name'])}</td>"
            f"<td class='dept'>{esc(r['dept'])}</td><td class='num'>{r['value']:.1f}</td><td class='num'>{r['change'] * 100:+.1f}%</td>"
            f"<td class='num'>{r['intensity']:.1f}</td><td>{status}</td>"
            + (f"<td class='num'>{r['points']}</td>" if final else "") + "</tr>")
    note = (f"<p class='foot'>Final round: only players within the carbon budget ({e.BUDGET:.2f}) can win. "
            "300 / 200 / 100 points for the top three, plus 50 for everyone within budget.</p>" if final else
            f"<p class='foot'>Ranked by portfolio value after news {revealed}. Intensity is for the portfolio held in that round. "
            f"Your final portfolio must be at or below {e.BUDGET:.2f} to win.</p>")
    return f"<div class='lbwrap'><table class='lb{' big' if big else ''}'>{head}{''.join(body)}</table></div>{note}"


def news_html(revealed):
    if revealed == 0:
        return "<p>No news yet. The first news item breaks after Monday's lock.</p>"
    return "".join(
        f"<div class='news'><div class='when'>News {k} · {esc(e.NEWS[k]['when'])}</div>"
        f"<div class='hl'>{esc(e.NEWS[k]['headline'])}</div><div>{esc(e.NEWS[k]['body'])}</div></div>"
        for k in range(revealed, 0, -1))


RULES_MD = f"""
**Your mission.** You manage {RS}100 crore of fictional money. Build a portfolio from 15 companies that earns the
highest return by the end of the week, while keeping its carbon intensity within the budget.

**Rules**
- Hold at least {e.MIN_HOLDINGS} companies, no more than {e.MAX_WEIGHT}% in any one, and weights must add up to 100%.
- Each round you lock a portfolio. You can change it as often as you like until the round closes.
- News breaks after each lock and hits the portfolio you locked, so you can't dodge it.
- If you don't lock a new portfolio, your previous one carries over. Joined late? Until you lock your first
  portfolio, your money sits in cash and earns nothing.
- **To win, your final portfolio (round 4) must have a carbon intensity at or below {e.BUDGET:.2f}** tCO₂e per {RS} crore.
  That is 30% below the average of all 15 companies.

**What the cards show**
- *Expected return:* what the company earns each round if no news hits it.
- *Intensity:* tonnes of CO₂e linked to every {RS}1 crore you invest. Your portfolio's intensity is the weighted average.
- *Transition plan:* how credible its plan to cut emissions is. *Physical risk:* exposure to floods, heat and similar events.
- *Analyst note:* read it. It may matter later.
"""


# ------------------------------------------------------------------ navigation
mode = st.sidebar.radio("Mode", ["Play", "Game master"], label_visibility="collapsed")
st.sidebar.markdown(f"<p class='foot'>Net Zero Portfolio Game · Credibl × BNY Pune<br>All companies and figures are fictional.</p>",
                    unsafe_allow_html=True)

st.markdown("""<div class="hero"><div class="kicker">Credibl × BNY Pune · Climate Change Week</div>
<h1>Net Zero Portfolio Game</h1><p>Invest ₹100 crore of fictional money. Beat the market. Stay within the carbon budget.</p></div>""",
            unsafe_allow_html=True)


# ------------------------------------------------------------------ PLAY
def play():
    pid = st.session_state.get("pid")
    if pid and not db.player(pid):
        st.session_state.pop("pid"); pid = None

    if not pid:
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            t_new, t_back = st.tabs(["Join the game", "I've played before"])
            with t_new:
                with st.form("join"):
                    name = st.text_input("Your name", max_chars=40, placeholder="e.g. Priya Sharma")
                    dept = st.text_input("Department or team (optional)", max_chars=40)
                    pin = st.text_input("Choose a 4-digit PIN", type="password", max_chars=4,
                                        help="You'll need it to come back to your portfolio from another device.")
                    if st.form_submit_button("Join", type="primary"):
                        if len(name.strip()) < 2:
                            st.error("Enter your name.")
                        elif not (pin.isdigit() and len(pin) == 4):
                            st.error("Your PIN must be exactly 4 digits.")
                        else:
                            new_id, err = db.register(name, dept, pin)
                            if err: st.error(err)
                            else:
                                st.session_state["pid"] = new_id; st.rerun()
            with t_back:
                with st.form("login"):
                    name = st.text_input("Your name", max_chars=40)
                    pin = st.text_input("Your PIN", type="password", max_chars=4)
                    if st.form_submit_button("Continue", type="primary"):
                        got = db.login(name, pin)
                        if got: st.session_state["pid"] = got; st.rerun()
                        else: st.error("Name and PIN don't match. Ask the game master to reset your PIN if you've forgotten it.")
        with c2:
            st.markdown("### How to play")
            st.markdown(RULES_MD)
        return

    _, name, dept = db.player(pid)
    revealed, is_open = db.get_state()
    subs = db.subs_for(pid)

    top_l, top_r = st.columns([5, 1])
    top_l.markdown(f"<div class='kicker'>Playing as</div><h3 style='margin-top:0'>{esc(name)}</h3>", unsafe_allow_html=True)
    if top_r.button("Log out"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    open_now, text = phase_text(revealed, is_open)
    st.markdown(f"<div class='phase{'' if open_now else ' closed'}'>{text}</div>", unsafe_allow_html=True)

    s = e.score(subs, revealed)
    rows = e.leaderboard(db.all_players(), revealed)
    my_rank = next((r["rank"] for r in rows if r["pid"] == pid), None)
    c = st.columns(4)
    c[0].markdown(stat("My portfolio value", f"{RS}{s['value']:.1f} cr", f"after news {revealed}" if revealed else "start of game"), unsafe_allow_html=True)
    c[1].markdown(stat("My rank", f"{my_rank} of {len(rows)}" if (my_rank and revealed) else "–", "updates after each news item"), unsafe_allow_html=True)
    c[2].markdown(stat("Carbon budget", f"{e.BUDGET:.2f}", "for your final portfolio"), unsafe_allow_html=True)
    locked_rounds = ", ".join(str(k) for k in sorted(subs)) or "none yet"
    c[3].markdown(stat("Rounds locked", locked_rounds, "previous portfolio carries over"), unsafe_allow_html=True)
    st.write("")

    tabs = st.tabs(["My portfolio", "Companies", "News", "Leaderboard", "How to play"])
    with tabs[0]:
        portfolio_tab(pid, subs, revealed, is_open)
    with tabs[1]:
        st.markdown(company_cards(revealed), unsafe_allow_html=True)
    with tabs[2]:
        st.markdown(news_html(revealed), unsafe_allow_html=True)
    with tabs[3]:
        live_leaderboard(pid)
    with tabs[4]:
        st.markdown(RULES_MD)


def portfolio_tab(pid, subs, revealed, is_open):
    nxt = revealed + 1
    # prefill inputs from the latest locked portfolio once per login
    if not st.session_state.get("prefilled"):
        latest = subs[max(subs)] if subs else [0] * e.N
        for i in range(e.N):
            st.session_state[f"w{i}"] = int(round(latest[i]))
        st.session_state["prefilled"] = True

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("#### Set your weights (%)")
        st.caption("Type a whole-number percentage for each company you want to hold. Leave the rest at 0.")
        cols = st.columns(3)
        for i, co in enumerate(e.CO):
            with cols[i % 3]:
                inten = e.known_intensity(i, revealed)
                st.number_input(
                    co["name"], min_value=0, max_value=e.MAX_WEIGHT, step=5, key=f"w{i}",
                    help=f"{co['sector']} · return {co['base'] * 100:.0f}% · intensity {inten:g} · "
                         f"plan {e.known_plan(i, revealed)} · physical risk {co['risk']}")
    weights = [st.session_state[f"w{i}"] for i in range(e.N)]
    problems = e.validate(weights)
    inten_now = e.portfolio_intensity(weights, [e.known_intensity(i, revealed) for i in range(e.N)])
    exp_ret = sum(w * c["base"] for w, c in zip(weights, e.CO)) / sum(weights) if sum(weights) else 0
    with right:
        st.markdown("#### Checks")
        total = sum(weights); held = sum(1 for w in weights if w > 0)
        lines = [
            ("Total", f"{total:g}%", abs(total - 100) < 0.01, "must be 100%"),
            ("Holdings", f"{held}", held >= e.MIN_HOLDINGS, f"at least {e.MIN_HOLDINGS}"),
            ("Largest weight", f"{max(weights):g}%", max(weights) <= e.MAX_WEIGHT, f"{e.MAX_WEIGHT}% or less"),
            ("Carbon intensity", f"{inten_now:.2f}", inten_now <= e.BUDGET, f"budget {e.BUDGET:.2f}"),
        ]
        html_rows = "".join(
            f"<tr><td>{a}</td><td class='num'><b>{b}</b></td><td><span class='{'ok' if good else 'bad'}'>"
            f"{'OK' if good else ('Over budget' if a == 'Carbon intensity' else 'Fix')}</span></td><td style='color:#6B7280'>{d}</td></tr>"
            for a, b, good, d in lines)
        st.markdown(f"<table class='lb'>{html_rows}</table>", unsafe_allow_html=True)
        st.caption(f"Expected return per round before any news: {exp_ret * 100:.1f}%. The news changes actual returns.")
        if revealed >= e.ROUNDS:
            st.info("The game is over. Your final portfolio is shown on the left.")
        elif not is_open:
            st.info("Submissions are closed right now. You can plan, but you can't lock until the next round opens.")
        else:
            if inten_now > e.BUDGET and not problems:
                if nxt == e.ROUNDS:
                    st.warning("This is your final lock and you are over the carbon budget, so you can't win with this portfolio.")
                else:
                    st.caption("You're over the carbon budget. That's allowed before the final lock, but plan your way back.")
            if problems:
                for p in problems: st.error(p)
            if st.button(f"Lock my portfolio for round {nxt}", type="primary", disabled=bool(problems), width="stretch"):
                rnd, err = db.submit(pid, weights)
                if err: st.error(err)
                else:
                    st.success(f"Locked for round {rnd}. You can change it until the round closes.")
                    st.rerun()
        if nxt in subs and revealed < e.ROUNDS:
            st.success(f"You have a portfolio locked for round {nxt}.")
        elif revealed < e.ROUNDS and subs:
            st.caption(f"No portfolio locked for round {nxt} yet: your round {max(subs)} portfolio will carry over.")

        sc = e.score(subs, revealed)
        if revealed and sc["values"]:
            st.markdown("#### My portfolio value")
            df = pd.DataFrame({"Point": ["Start"] + [f"After news {k}" for k in range(1, revealed + 1)],
                               "Value": [e.START_VALUE] + sc["values"]})
            df["Order"] = range(len(df))
            base = alt.Chart(df).encode(
                x=alt.X("Point:N", sort=alt.SortField("Order"), title=None, axis=alt.Axis(labelAngle=0, grid=False)),
                y=alt.Y("Value:Q", title=f"{RS} crore", scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor="#EEF1F4")),
                tooltip=[alt.Tooltip("Point:N", title=""), alt.Tooltip("Value:Q", title="Value (₹ cr)", format=".1f")])
            chart = (base.mark_line(color="#366EB5", strokeWidth=2) +
                     base.mark_point(color="#366EB5", filled=True, size=80)).properties(height=220)
            st.altair_chart(chart.configure_view(strokeWidth=0), width="stretch")


@st.fragment(run_every=15)
def live_leaderboard(pid=None, big=False, top=10):
    revealed, _ = db.get_state()
    rows = e.leaderboard(db.all_players(), revealed)
    st.markdown(leaderboard_html(rows, revealed, me=pid, top=top, big=big), unsafe_allow_html=True)
    st.caption("Updates automatically every 15 seconds.")


# ------------------------------------------------------------------ GAME MASTER
def gm_password():
    try:
        return st.secrets["GM_PASSWORD"]
    except Exception:
        return os.environ.get("GM_PASSWORD", "credibl-gm")


def game_master():
    if not st.session_state.get("gm"):
        with st.form("gm_login"):
            pw = st.text_input("Game master password", type="password")
            if st.form_submit_button("Enter", type="primary"):
                if pw == gm_password(): st.session_state["gm"] = True; st.rerun()
                else: st.error("Wrong password.")
        return
    if gm_password() == "credibl-gm":
        st.warning("You're using the default game master password. Set GM_PASSWORD in the app's secrets before sharing the link.")

    revealed, is_open = db.get_state()
    players = db.all_players()
    nxt = revealed + 1
    locked_now = sum(1 for p in players if nxt in p[3])
    _, text = phase_text(revealed, is_open)
    st.markdown(f"<div class='phase'>{text}</div>", unsafe_allow_html=True)
    c = st.columns(4)
    c[0].markdown(stat("Players joined", len(players)), unsafe_allow_html=True)
    c[1].markdown(stat(f"Locked for round {min(nxt, 4)}", locked_now if revealed < 4 else "–"), unsafe_allow_html=True)
    c[2].markdown(stat("News revealed", f"{revealed} of 4"), unsafe_allow_html=True)
    c[3].markdown(stat("Carbon budget", f"{e.BUDGET:.2f}"), unsafe_allow_html=True)
    st.write("")

    t_ctrl, t_screen, t_players, t_admin = st.tabs(["Run the game", "Presenter screen", "Players", "Backup and reset"])
    with t_ctrl:
        a, b = st.columns(2, gap="large")
        with a:
            st.markdown("#### Step 1 · Close the round")
            st.caption("Optional: stops players changing their portfolio (for example at 5 pm).")
            if revealed < 4:
                if is_open:
                    if st.button(f"Close round {nxt} submissions"): db.set_state(open_=False); st.rerun()
                else:
                    if st.button(f"Reopen round {nxt} submissions"): db.set_state(open_=True); st.rerun()
        with b:
            if revealed < 4:
                st.markdown(f"#### Step 2 · Reveal news {nxt}")
                st.markdown(f"**{e.NEWS[nxt]['headline']}**")
                st.caption(f"This locks every round {nxt} portfolio, scores it, and "
                           + (f"opens round {nxt + 1}." if nxt < 4 else "ends the game."))
                sure = st.checkbox(f"I'm ready to reveal news {nxt}", key=f"sure{nxt}")
                if st.button(f"Reveal news {nxt}", type="primary", disabled=not sure):
                    db.set_state(revealed=nxt, open_=nxt < 4); st.rerun()
            else:
                st.markdown("#### The game is over")
                st.caption("Final results are on the Presenter screen.")
        st.divider()
        if revealed > 0:
            with st.expander("Undo the last reveal (for testing or mistakes)"):
                if st.button(f"Undo news {revealed}"):
                    db.set_state(revealed=revealed - 1, open_=False); st.rerun()
        st.markdown("#### News to read out")
        for k in range(1, 5):
            done = "Revealed" if k <= revealed else "Not yet revealed"
            with st.expander(f"News {k} · {e.NEWS[k]['headline']} ({done})"):
                st.write(e.NEWS[k]["body"])
        st.markdown("#### What changes behind the scenes (game master only)")
        st.markdown(
            "- **News 1, carbon price:** each company loses intensity × 0.15% this round and × 0.05% in every later round; "
            "strong-plan companies pay half.\n"
            "- **News 2, flood:** High physical risk −15% this round and −3% in each later round; Medium −5% this round.\n"
            "- **News 3, exposé:** EverGreen Agro −25%; its intensity becomes 60 and its plan None from now on.\n"
            "- **News 4, green steel:** Vajra Steel +30% in the final round.")
    with t_screen:
        st.caption("Put this on the big screen. It refreshes every 15 seconds.")
        if revealed:
            st.markdown(f"<div class='news'><div class='when'>Latest news · {esc(e.NEWS[revealed]['when'])}</div>"
                        f"<div class='hl'>{esc(e.NEWS[revealed]['headline'])}</div></div>", unsafe_allow_html=True)
        live_leaderboard(None, big=True, top=10)
    with t_players:
        rows = e.leaderboard(players, revealed); by = {r["pid"]: r for r in rows}
        table = []
        for pid, name, dept, subs in players:
            r = by.get(pid)
            table.append({"Player": name, "Department": dept or "",
                          **{f"R{k}": ("Locked" if k in subs else "–") for k in range(1, 5)},
                          "Rank": r["rank"] if (r and revealed) else None,
                          "Value (₹ cr)": round(r["value"], 2) if r else None,
                          "Intensity": round(r["intensity"], 2) if r else None})
        if table:
            st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
            names = {f"{n} ({d})" if d else n: pid for pid, n, d, _ in players}
            st.markdown("#### Help a player")
            who = st.selectbox("Player", list(names))
            x, y = st.columns(2)
            with x:
                new_pin = st.text_input("New 4-digit PIN", max_chars=4, key="newpin")
                if st.button("Reset PIN"):
                    if new_pin.isdigit() and len(new_pin) == 4:
                        db.reset_pin(names[who], new_pin); st.success(f"PIN reset for {who}.")
                    else: st.error("Enter 4 digits.")
            with y:
                st.write("")
                if st.checkbox(f"Remove {who} from the game", key="rmsure") and st.button("Remove player"):
                    db.delete_player(names[who]); st.rerun()
            lb = pd.DataFrame([{k: r[k] for k in ("rank", "name", "dept", "value", "change", "intensity", "within", "points")} for r in rows])
            st.download_button("Download leaderboard (CSV)", lb.to_csv(index=False).encode(), "leaderboard.csv", "text/csv")
        else:
            st.info("No players yet. Share the app link and ask people to join.")
    with t_admin:
        st.markdown("#### Backup")
        st.caption("Free hosting can restart the app and wipe its data. Download a backup after each round; restore it if needed.")
        st.download_button("Download backup (JSON)", db.export_json().encode(), "netzero_backup.json", "application/json")
        up = st.file_uploader("Restore from a backup", type=["json"])
        if up and st.button("Restore this backup"):
            db.import_json(up.read().decode()); st.success("Restored."); st.rerun()
        st.markdown("#### Reset")
        keep = st.checkbox("Keep players (only clear portfolios and news)", value=True)
        confirm = st.text_input("Type RESET to confirm")
        if st.button("Reset the game", disabled=confirm != "RESET"):
            db.reset_game(keep_players=keep); st.success("Game reset."); st.rerun()


if mode == "Play":
    play()
else:
    game_master()
