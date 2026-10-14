"""Net Zero Portfolio Game · Streamlit app (individual play).

Run locally:  streamlit run app.py
Players use "Play"; the game master uses "Game master" (username and password from secrets).
All companies and figures are fictional.
"""
import html
import os
import time

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import engine as e
import storage as db
from game_data import PROFILES

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
.phase { background: #E8F3F6; border-radius: 8px; padding: 14px 18px; margin: 6px 0 10px 0; color: #1C3B69; font-size: 15px; }
.phase b { color: #152139; }
.phase.closed { background: #F3F3F3; }
.stat { background: #E8F3F6; border-radius: 8px; padding: 12px 16px; height: 100%; }
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
.chip { display: inline-block; font: 600 11px 'Open Sans', Arial, sans-serif; letter-spacing: .06em; text-transform: uppercase; padding: 3px 10px; border-radius: 999px; }
.chip.locked { background: #F3F3F3; color: #6B7280; } .chip.next { background: #366EB5; color: #fff; } .chip.later { background: #E8F3F6; color: #1C3B69; }
.chip.off { background: #FCE9E6; color: #B23A2E; }
table.lb { width: 100%; border-collapse: collapse; font-size: 15px; }
table.lb th { background: #1C3B69; color: #fff; text-align: left; padding: 8px 10px; font-weight: 600; }
table.lb td { padding: 8px 10px; border-bottom: 1px solid #D9DEE4; }
table.lb tr.me td { background: #E8F3F6; font-weight: 600; }
table.lb td.num { text-align: right; font-variant-numeric: tabular-nums; }
table.lb.big { font-size: 22px; } table.lb.big td, table.lb.big th { padding: 12px 14px; }
.news { border-left: 4px solid #366EB5; background: #F7F9FB; padding: 12px 16px; border-radius: 4px; margin-bottom: 12px; }
.news .when { font: 600 11px 'Open Sans', Arial, sans-serif; letter-spacing: .1em; text-transform: uppercase; color: #366EB5; }
.news .hl { font: 600 20px 'Zilla Slab', Georgia, serif; color: #152139; margin: 2px 0 4px 0; }
.news.big .hl { font-size: 34px; }
.foot { color: #6B7280; font-size: 12px; margin-top: 24px; }
.mini .mn { font: 600 18px 'Zilla Slab', Georgia, serif; color: #152139; line-height: 1.2; }
.mini .ms { font-size: 12.5px; color: #6B7280; margin-bottom: 6px; }
.mini .mt { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 13px; color: #1C3B69; margin: 6px 0; }
.mini .mt b { color: #366EB5; }
.mini .mc { font-size: 12.5px; color: #1D1D1B; background: #F3F3F3; border-radius: 6px; padding: 6px 8px; }
.mini .badge { margin: 2px 0 4px 0; }
/* company cards */
.cc-top { display: flex; align-items: center; gap: 10px; }
.cc-ic { width: 42px; height: 42px; flex: 0 0 42px; border-radius: 12px; background: #E8F3F6; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.cc-tt { flex: 1; min-width: 0; }
.cc-nm { font: 600 19px 'Zilla Slab', Georgia, serif; color: #152139; line-height: 1.15; }
.cc-sec { font-size: 12.5px; color: #6B7280; }
.held { font: 600 11px 'Open Sans', Arial, sans-serif; background: #366EB5; color: #fff; padding: 3px 9px; border-radius: 999px; white-space: nowrap; }
.pills { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 8px 0; }
.pill { font: 600 12px 'Open Sans', Arial, sans-serif; padding: 3px 9px; border-radius: 999px; }
.pill.ret { background: #E8F3F6; color: #1C3B69; }
.pill.good { background: #E3F1DF; color: #2F6B27; } .pill.mid { background: #FBEBD9; color: #8A4F0C; } .pill.bad { background: #FCE3E0; color: #A93226; }
.meter .mlab { display: flex; justify-content: space-between; font-size: 12.5px; color: #1C3B69; }
.meter .mlab b { font: 700 16px 'Zilla Slab', Georgia, serif; }
.track { position: relative; height: 8px; background: #EEF1F4; border-radius: 999px; margin: 4px 0 2px 0; }
.fill { height: 8px; border-radius: 999px; } .fill.good { background: #6BAF5D; } .fill.mid { background: #E69742; } .fill.bad { background: #D34E40; }
.fill.blue { background: #366EB5; }
.tick { position: absolute; top: -4px; width: 2px; height: 16px; background: #152139; }
.mcap { font-size: 11px; color: #6B7280; }
.cnote { font-size: 13px; color: #1D1D1B; background: #F7F5EE; border-left: 3px solid #E69742; border-radius: 4px; padding: 7px 9px; margin-top: 8px; }
.cbody { font-size: 13.5px; color: #1D1D1B; margin-top: 10px; }
.cbody .h { font: 600 11px 'Open Sans', Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; color: #6B7280; margin: 8px 0 2px 0; }
.cbody ul { margin: 0; padding-left: 0 !important; list-style: none; } .cbody li { margin: 2px 0; font-size: 13.5px !important; }
.ccgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.ccfull { border: 1px solid #D9DEE4; border-radius: 12px; padding: 14px 16px; background: #fff; }
.update { font-size: 13px; background: #FCE3E0; color: #7A1F16; border-radius: 6px; padding: 7px 9px; margin-top: 8px; }
/* portfolio panel */
.pf h4 { margin: 0 0 6px 0; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 12px 0; }
.chip2 { font-size: 12.5px; background: #E8F3F6; color: #1C3B69; padding: 4px 9px; border-radius: 999px; }
.gauge { margin: 10px 0 12px 0; } .gauge .gl { display: flex; justify-content: space-between; font-size: 13px; color: #1C3B69; }
.gauge .gl b { font: 700 18px 'Zilla Slab', Georgia, serif; }
.gauge .gs { font-size: 12px; color: #6B7280; margin-top: 2px; }
[data-testid="stButtonGroup"] button { padding-left: 2px !important; padding-right: 2px !important; min-width: 0 !important; }
.checks { list-style: none; padding: 0 !important; margin: 4px 0 10px 0; } .checks li { margin: 3px 0; font-size: 14px !important; }
@media (min-width: 900px) { div[data-testid="stColumn"]:has(.pf-anchor) { position: sticky; top: 3.8rem; align-self: flex-start; } }
.lbwrap { overflow-x: auto; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 4px 0 14px 0; }
.mbar { display: none; }
.block-container { padding-top: 2.2rem; }
@media (max-width: 640px) {
  .block-container { padding: 3.6rem 0.8rem 6.5rem 0.8rem !important; }
  .hero { padding: 14px 16px; margin-bottom: 10px; }
  .hero h1 { font-size: 24px; margin: 2px 0 4px 0; }
  .hero p { font-size: 13px; }
  .hero .kicker { font-size: 10px; letter-spacing: .1em; }
  .stats { grid-template-columns: 1fr 1fr; gap: 8px; }
  .stat { padding: 9px 12px; }
  .stat .val { font-size: 21px; }
  .stat .sub { display: none; }
  .phase { font-size: 14px; padding: 10px 12px; }
  table.lb { font-size: 14px; } table.lb td, table.lb th { padding: 7px 6px; }
  table.lb .dept, table.lb .chg { display: none; } table.lb.big { font-size: 16px; }
  .card .top .nm { font-size: 18px; }
  .mbar { display: flex; position: fixed; left: 0; right: 0; bottom: 0; z-index: 999990; background: #152139; color: #fff;
          padding: 10px 14px calc(10px + env(safe-area-inset-bottom)) 14px; justify-content: space-between; gap: 8px;
          font: 600 13px 'Open Sans', Arial, sans-serif; box-shadow: 0 -2px 10px rgba(0,0,0,.18); }
  .mbar .it { display: flex; flex-direction: column; } .mbar .k { font-size: 10px; color: #A9C3DC; letter-spacing: .08em; text-transform: uppercase; }
  .mbar .v { font: 700 17px Georgia, serif; } .mbar .g { color: #8FD38A; } .mbar .r { color: #FF9B8F; }
}
</style>
""", unsafe_allow_html=True)

RS = "₹"


def esc(s):
    return html.escape(str(s))


def stat(label, value, sub=""):
    return f'<div class="stat"><div class="lab">{esc(label)}</div><div class="val">{value}</div><div class="sub">{sub}</div></div>'


def stats(*tiles):
    st.markdown('<div class="stats">' + "".join(stat(*t) for t in tiles) + "</div>", unsafe_allow_html=True)


def load():
    fs = db.full_state()
    game = e.Game(fs["params"], fs["snapshots"], fs["revealed"])
    return fs, game


def round_name(fs, k):
    days = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday"}
    return f"Round {k} ({days[k]})" if fs["mode"] == "week" else f"Round {k}"


def news_when(fs, game, k):
    return f"News {k} · {game.news(k)['when']}" if fs["mode"] == "week" else f"News {k}"


def phase_text(fs, game):
    revealed, nxt = fs["revealed"], fs["revealed"] + 1
    if revealed >= e.ROUNDS:
        return False, "🏁 <b>Game over.</b> The final market close has happened. See the final leaderboard."
    if fs["open"]:
        extra = (" <b>This is your FINAL lock:</b> your portfolio must be within the carbon budget to win."
                 if nxt == e.ROUNDS else " You can change it as often as you like until the round closes.")
        return True, f"🟢 <b>{round_name(fs, nxt)} is open:</b> lock your portfolio.{extra}"
    if fs["deadline"] and fs["open_flag"]:
        return False, f"⏰ <b>Time's up for {round_name(fs, nxt).lower()}.</b> News {nxt} is coming."
    return False, f"⏸️ <b>Submissions are closed.</b> Waiting for news {nxt} from the game master."


def countdown(deadline, big=False):
    """Live countdown drawn in the browser (no page reloads)."""
    if not deadline:
        return
    remain = max(0.0, deadline - time.time())
    size, pad, h = (64, "18px 24px", 120) if big else (24, "10px 16px", 62)
    embed = (lambda h_, height: st.iframe(h_, height=height)) if hasattr(st, "iframe") else components.html
    embed(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;background:#152139;border-radius:8px;
         padding:{pad};font-family:'Open Sans',Arial,sans-serif;">
      <span style="color:#E8F3F6;font-size:{max(14, size // 3)}px;font-weight:600;letter-spacing:.08em;text-transform:uppercase">Time left this round</span>
      <span id="c" style="color:#5EC4E4;font:700 {size}px Georgia,serif;font-variant-numeric:tabular-nums"></span>
    </div>
    <script>
      const end = Date.now() + {remain * 1000:.0f};
      function tick() {{
        const s = Math.max(0, Math.round((end - Date.now()) / 1000));
        document.getElementById('c').textContent = s > 0 ? Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0') : "Time's up";
      }}
      tick(); setInterval(tick, 500);
    </script>""", height=h)  # our own fixed markup, not user input


@st.fragment(run_every=4)
def watcher():
    """Reload the page for everyone when the game master changes the game, or a round timer runs out."""
    fs = db.full_state()
    sig = (fs["revealed"], fs["open"], fs["deadline"], str(fs["params"]))
    if "sig" not in st.session_state:
        st.session_state["sig"] = sig
    elif st.session_state["sig"] != sig:
        st.session_state["sig"] = sig
        st.rerun(scope="app")


PLAN_CLS = {"Strong": "good", "Partial": "mid", "None": "bad"}
RISK_CLS = {"Low": "good", "Medium": "mid", "High": "bad"}


def inten_cls(x):
    return "good" if x <= 15 else "mid" if x <= 40 else "bad"


def card_head(i, game, weight=0):
    """Compact card: icon, name, return / plan / risk pills, CO₂ meter with the budget tick, analyst note."""
    co = e.CO[i]; pr = PROFILES[co["name"]]
    inten, plan = game.known_intensity(i), game.known_plan(i)
    held = f"<span class='held'>✓ {weight:g}%</span>" if weight else ""
    badge = "<div class='badge'>Corrected after investigation</div>" if game.corrected(i) else ""
    return (f"<div class='cc-top'><div class='cc-ic'>{pr['icon']}</div><div class='cc-tt'><div class='cc-nm'>{esc(co['name'])}</div>"
            f"<div class='cc-sec'>{esc(co['sector'])}</div></div>{held}</div>{badge}"
            f"<div class='pills'><span class='pill ret'>↗ {co['base'] * 100:.0f}% return a round</span>"
            f"<span class='pill {PLAN_CLS[plan]}'>Plan: {esc(plan)}</span>"
            f"<span class='pill {RISK_CLS[co['risk']]}'>Climate risk: {esc(co['risk'])}</span></div>"
            f"<div class='meter'><div class='mlab'><span>CO₂ intensity (tCO₂e per {RS} cr)</span><b>{inten:g}</b></div>"
            f"<div class='track'><div class='fill {inten_cls(inten)}' style='width:{min(inten, 100):.0f}%'></div>"
            f"<div class='tick' style='left:{min(game.budget, 100):.1f}%'></div></div>"
            f"</div>"
            f"<div class='cnote'>🔎 <b>Analyst note:</b> {esc(co['clue'])}</div>")


def card_body(i, game):
    co = e.CO[i]; pr = PROFILES[co["name"]]
    upd = ""
    if game.corrected(i):
        upd = (f"<div class='update'>🔍 <b>Investigation update:</b> true intensity is {co['true']:g}, not {co['rep']:g}, "
               f"and its transition plan has been downgraded to {esc(co['tplan'])}.</div>")
    return (f"<div class='cbody'>{esc(pr['about'])}{upd}"
            f"<div class='h'>Strengths</div><ul>{''.join(f'<li>✅ {esc(x)}</li>' for x in pr['strengths'])}</ul>"
            f"<div class='h'>Watch-outs</div><ul>{''.join(f'<li>⚠️ {esc(x)}</li>' for x in pr['watch'])}</ul></div>")


def company_cards(game):
    return "<div class='ccgrid'>" + "".join(
        f"<div class='ccfull'>{card_head(i, game)}{card_body(i, game)}</div>" for i in range(e.N)) + "</div>"


MEDAL = {1: '🥇', 2: '🥈', 3: '🥉'}


def leaderboard_html(rows, game, me=None, top=10, big=False):
    revealed = game.revealed
    if revealed == 0:
        return "<p>No results yet. The leaderboard appears after the first news item.</p>"
    if not rows:
        return "<p>No portfolios locked yet.</p>"
    final = revealed >= e.ROUNDS
    shown = rows[:top]
    if me is not None and all(r["pid"] != me for r in shown):
        shown = shown + [r for r in rows if r["pid"] == me]
    head = ("<tr><th>Rank</th><th>Player</th><th class='dept'>Department</th><th style='text-align:right'>Value (" + RS +
            " cr)</th><th class='chg' style='text-align:right'>Change</th><th style='text-align:right'>Intensity</th><th>Budget</th>"
            + ("<th style='text-align:right'>Points</th>" if final else "") + "</tr>")
    body = []
    for r in shown:
        status = '<span class="ok">Within</span>' if r["within"] else '<span class="bad">Over</span>'
        body.append(
            f"<tr class='{'me' if r['pid'] == me else ''}'><td>{MEDAL.get(r['rank'], r['rank'])}</td><td>{esc(r['name'])}</td>"
            f"<td class='dept'>{esc(r['dept'])}</td><td class='num'>{r['value']:.1f}</td><td class='num chg'>{r['change'] * 100:+.1f}%</td>"
            f"<td class='num'>{r['intensity']:.1f}</td><td>{status}</td>"
            + (f"<td class='num'>{r['points']}</td>" if final else "") + "</tr>")
    note = (f"<p class='foot'>Final round: only players within the carbon budget ({game.budget:.2f}) can win. "
            "300 / 200 / 100 points for the top three, plus 50 for everyone within budget.</p>" if final else
            f"<p class='foot'>Ranked by portfolio value after news {revealed}. Intensity is for the portfolio held in that round. "
            f"Your final portfolio must be at or below {game.budget:.2f} to win.</p>")
    return f"<div class='lbwrap'><table class='lb{' big' if big else ''}'>{head}{''.join(body)}</table></div>{note}"


def news_html(fs, game):
    if game.revealed == 0:
        return "<p>No news yet. The first news item breaks after round 1 closes.</p>"
    return "".join(
        f"<div class='news'><div class='when'>{esc(news_when(fs, game, k))}</div>"
        f"<div class='hl'>{news_icon(game, k)} {esc(game.news(k)['headline'])}</div><div>{esc(game.news(k)['body'])}</div></div>"
        for k in range(game.revealed, 0, -1))


def news_icon(game, k):
    return {1: "💸", 2: "🌊", 3: "🔍", 4: "🚀"}[k] if game.params(k)[e.SHOCK_KEY[k]] else "😴"


def rules_md(game):
    return f"""
**Your mission.** You manage {RS}100 crore of fictional money. Build a portfolio from 15 companies that earns the
highest return by the end of the game, while keeping its carbon intensity within the budget.

**Rules**
- Hold at least {game.min_holdings} companies, no more than {game.max_weight}% in any one, and weights must add up to 100%.
- Each round you lock a portfolio. You can change it as often as you like until the round closes.
- News breaks after each round and hits the portfolio you locked, so you can't dodge it.
- If you don't lock a new portfolio, your previous one carries over. Joined late? Until you lock your first
  portfolio, your money sits in cash and earns nothing.
- **To win, your final portfolio (round 4) must have a carbon intensity at or below {game.budget:.2f}** tCO₂e per {RS} crore.

**What the cards show**
- *Expected return:* what the company earns each round if no news hits it.
- *Intensity:* tonnes of CO₂e linked to every {RS}1 crore you invest. Your portfolio's intensity is the weighted average.
- *Transition plan:* how credible its plan to cut emissions is. *Physical risk:* exposure to floods, heat and similar events.
- *Analyst note:* read it. It may matter later.
"""


# ------------------------------------------------------------------ navigation
mode = st.sidebar.radio("Mode", ["Play", "Game master"], label_visibility="collapsed")
st.sidebar.markdown("<p class='foot'>Net Zero Portfolio Game · Credibl × BNY Pune<br>All companies and figures are fictional.</p>",
                    unsafe_allow_html=True)
st.markdown("""<div class="hero"><div class="kicker">Credibl × BNY Pune · Climate Change Week</div>
<h1>🌍 Net Zero Portfolio Game</h1><p>Invest ₹100 crore of fictional money. Ride out the climate shocks. Beat the market without blowing the carbon budget.</p></div>""",
            unsafe_allow_html=True)


# ------------------------------------------------------------------ PLAY
def play():
    pid = st.session_state.get("pid")
    if pid and not db.player(pid):
        st.session_state.pop("pid"); pid = None
    fs, game = load()

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
            st.markdown(rules_md(game))
        return

    watcher()
    _, name, dept = db.player(pid)
    subs = db.subs_for(pid)
    revealed = fs["revealed"]

    top_l, top_r = st.columns([5, 1])
    top_l.markdown(f"<div class='kicker'>Playing as</div><h3 style='margin-top:0'>👋 Hi, {esc(name.split()[0])}</h3>", unsafe_allow_html=True)
    if top_r.button("Log out"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    open_now, text = phase_text(fs, game)
    st.markdown(f"<div class='phase{'' if open_now else ' closed'}'>{text}</div>", unsafe_allow_html=True)
    if open_now:
        countdown(fs["deadline"])

    s = game.score(subs)
    rows = game.leaderboard(db.all_players())
    my_rank = next((r["rank"] for r in rows if r["pid"] == pid), None)
    rank_txt = (f"{MEDAL.get(my_rank, '')} {my_rank} of {len(rows)}".strip()) if (my_rank and revealed) else "–"
    stats(("💰 My value", f"{RS}{s['value']:.1f} cr", f"after news {revealed}" if revealed else "start of game"),
          ("🏆 My rank", rank_txt, "updates after each news item"),
          ("🌍 Carbon budget", f"{game.budget:.2f}", "for your final portfolio"),
          ("🔒 Rounds locked", ", ".join(str(k) for k in sorted(subs)) or "none yet", "previous portfolio carries over"))
    me_row = next((r for r in rows if r["pid"] == pid), None)
    if revealed >= e.ROUNDS and me_row and me_row["eligible"] and me_row["rank"] <= 3 and not st.session_state.get("celebrated"):
        st.balloons(); st.session_state["celebrated"] = True

    tabs = st.tabs(["📊 Portfolio", "🏢 Companies", "📰 News", "🏆 Leaderboard", "📘 Rules"])
    with tabs[0]:
        portfolio_tab(pid, subs, fs, game)
    with tabs[1]:
        st.caption("Everything a careful analyst knows about each company. Read the notes and watch-outs closely. "
                   "On each CO₂ bar, the black tick is the portfolio budget.")
        st.markdown(company_cards(game), unsafe_allow_html=True)
    with tabs[2]:
        st.markdown(news_html(fs, game), unsafe_allow_html=True)
    with tabs[3]:
        live_leaderboard(pid)
    with tabs[4]:
        st.markdown(rules_md(game))


def stake_options(game):
    return list(range(0, game.max_weight + 1, 5)) if game.max_weight <= 40 else None


def portfolio_tab(pid, subs, fs, game):
    revealed, nxt = fs["revealed"], fs["revealed"] + 1
    if st.session_state.get("toast"):
        st.toast(st.session_state.pop("toast"))
    opts = stake_options(game)
    if not st.session_state.get("prefilled"):
        latest = subs[max(subs)] if subs else [0] * e.N
        for i in range(e.N):
            st.session_state[f"w{i}"] = int(round(latest[i]))
        st.session_state["prefilled"] = True
    if opts:  # keep stored stakes on the menu even if the game master changes the maximum
        for i in range(e.N):
            v = st.session_state.get(f"w{i}")
            if v is not None and v not in opts:
                st.session_state[f"w{i}"] = min(opts, key=lambda o: abs(o - v))

    left, right = st.columns([7, 3], gap="medium")
    with left:
        st.markdown("#### Pick your companies")
        st.caption("Tap a stake (%) for each company you want to own and leave the rest at 0. On each CO₂ bar, the black "
                   "tick is the portfolio budget. Open *More about* for the full profile.")
        for r0 in range(0, e.N, 2):
            cols = st.columns(2)
            for j, i in enumerate(range(r0, min(r0 + 2, e.N))):
                co = e.CO[i]
                w_now = st.session_state.get(f"w{i}") or 0
                with cols[j].container(border=True):
                    st.markdown(card_head(i, game, w_now), unsafe_allow_html=True)
                    with st.expander(f"More about {co['name'].split()[0]}"):
                        st.markdown(card_body(i, game), unsafe_allow_html=True)
                    if opts:
                        st.segmented_control("Your stake (%)", opts, key=f"w{i}", format_func=str, width="stretch")
                    else:
                        st.number_input(f"Your stake in {co['name']} (%)", min_value=0, max_value=100, step=5, key=f"w{i}",
                                        label_visibility="collapsed")
    weights = [st.session_state.get(f"w{i}") or 0 for i in range(e.N)]
    problems = game.validate(weights)
    inten_now = game.portfolio_intensity(weights, [game.known_intensity(i) for i in range(e.N)])
    exp_ret = sum(w * c["base"] for w, c in zip(weights, e.CO)) / sum(weights) if sum(weights) else 0
    tot = sum(weights); n_held = sum(1 for x in weights if x > 0)
    ok_tot, ok_held = abs(tot - 100) < 0.01, n_held >= game.min_holdings
    ok_max, ok_co2 = (max(weights) <= game.max_weight), inten_now <= game.budget
    locked_same = nxt in subs and [round(x, 4) for x in subs[nxt]] == [round(float(x), 4) for x in weights]
    if revealed >= e.ROUNDS:
        state_txt = "Game over"
    elif locked_same and not problems:
        state_txt = "Locked ✓"
    elif problems:
        state_txt = "Fix below ↓"
    else:
        state_txt = "Lock below ↓" if fs["open"] else "Closed"
    # phone-only sticky bar: the key checks stay visible while scrolling through the companies
    st.markdown(
        f"<div class='mbar'>"
        f"<div class='it'><span class='k'>Invested</span><span class='v {'g' if ok_tot else 'r'}'>{tot:g}%</span></div>"
        f"<div class='it'><span class='k'>Companies</span><span class='v {'g' if ok_held and ok_max else 'r'}'>{n_held}</span></div>"
        f"<div class='it'><span class='k'>CO₂ / budget</span><span class='v {'g' if ok_co2 else 'r'}'>{inten_now:.1f}/{game.budget:.0f}</span></div>"
        f"<div class='it'><span class='k'>Status</span><span class='v'>{state_txt}</span></div></div>",
        unsafe_allow_html=True)
    with right:
        st.markdown("<div class='pf-anchor'></div>", unsafe_allow_html=True)
        st.markdown("#### Your portfolio")
        held = sorted([(w, i) for i, w in enumerate(weights) if w > 0], reverse=True)
        chips = "".join(f"<span class='chip2'>{PROFILES[e.CO[i]['name']]['icon']} {esc(e.CO[i]['name'])} · <b>{w:g}%</b></span>"
                        for w, i in held) or "<span class='chip2'>Nothing picked yet</span>"
        tot_cls = "good" if ok_tot else ("bad" if tot > 100 else "blue")
        tot_note = "Fully invested" if ok_tot else (f"Remove {tot - 100:g}%" if tot > 100 else f"{100 - tot:g}% still to invest")
        scale = max(game.budget * 2, inten_now, 1)
        co2_note = (f"✅ Within budget by {game.budget - inten_now:.1f}" if ok_co2 else f"❌ Over budget by {inten_now - game.budget:.1f}")
        st.markdown(
            f"<div class='pf'><div class='chips'>{chips}</div>"
            f"<div class='gauge'><div class='gl'><span>💼 Invested</span><b>{tot:g}%</b></div>"
            f"<div class='track'><div class='fill {tot_cls}' style='width:{min(tot, 100):.0f}%'></div></div>"
            f"<div class='gs'>{tot_note}</div></div>"
            f"<div class='gauge'><div class='gl'><span>🌍 Portfolio CO₂ intensity</span><b>{inten_now:.1f}</b></div>"
            f"<div class='track'><div class='fill {'good' if ok_co2 else 'bad'}' style='width:{min(inten_now / scale * 100, 100):.0f}%'></div>"
            f"<div class='tick' style='left:{game.budget / scale * 100:.1f}%'></div></div>"
            f"<div class='gs'>{co2_note} (budget {game.budget:.2f}, black tick)</div></div>"
            f"<ul class='checks'><li>{'✅' if ok_held else '❌'} At least {game.min_holdings} companies (you have {n_held})</li>"
            f"<li>{'✅' if ok_max else '❌'} No more than {game.max_weight}% in one company</li>"
            f"<li>📈 Expected return a round, before any news: <b>{exp_ret * 100:.1f}%</b></li></ul></div>",
            unsafe_allow_html=True)
        if revealed >= e.ROUNDS:
            st.info("🏁 The game is over. Your final portfolio is shown on the left.")
        elif not fs["open"]:
            st.info("⏸️ Submissions are closed right now. You can plan, but you can't lock until the next round opens.")
        else:
            if inten_now > game.budget and not problems:
                if nxt == e.ROUNDS:
                    st.warning("This is your final lock and you are over the carbon budget, so you can't win with this portfolio.")
                else:
                    st.caption("You're over the carbon budget. That's allowed before the final lock, but plan your way back.")
            for p in problems:
                st.error(p)
            label = "✓ Locked: update lock" if locked_same else f"🔒 Lock my portfolio for round {nxt}"
            if st.button(label, type="primary", disabled=bool(problems), width="stretch"):
                rnd, err = db.submit(pid, weights)
                if err: st.error(err)
                else:
                    st.session_state["toast"] = f"🔒 Locked for round {rnd}. Good luck!"
                    st.rerun()
        if nxt in subs and revealed < e.ROUNDS:
            st.success(f"You have a portfolio locked for round {nxt}. You can still change it until the round closes.")
        elif revealed < e.ROUNDS and subs:
            st.caption(f"No portfolio locked for round {nxt} yet: your round {max(subs)} portfolio will carry over.")

        sc = game.score(subs)
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


@st.fragment(run_every=10)
def live_leaderboard(pid=None, big=False, top=10):
    fs, game = load()
    rows = game.leaderboard(db.all_players())
    st.markdown(leaderboard_html(rows, game, me=pid, top=top, big=big), unsafe_allow_html=True)
    st.caption("Updates automatically every 10 seconds.")


# ------------------------------------------------------------------ GAME MASTER
def secret(key, default):
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)


GM_USER = secret("GM_USER", "gamemaster")
GM_PASSWORD = secret("GM_PASSWORD", "credibl-gm")


def game_master():
    if not st.session_state.get("gm"):
        st.markdown("### Game master sign-in")
        with st.form("gm_login"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
                if user.strip().lower() == str(GM_USER).lower() and pw == GM_PASSWORD:
                    st.session_state["gm"] = True; st.rerun()
                else:
                    st.error("Username or password is wrong.")
        return
    if GM_PASSWORD == "credibl-gm":
        st.warning("You're using the default game master password. Set GM_PASSWORD in the app's secrets before sharing the link.")
    watcher()
    fs, game = load()
    t_run, t_shock, t_screen, t_players, t_admin = st.tabs(
        ["Run the game", "Shocks and rules", "Presenter screen", "Players", "Backup and reset"])
    with t_run:
        run_tab(fs, game)
    with t_shock:
        shocks_tab(fs, game)
    with t_screen:
        presenter(fs, game)
    with t_players:
        players_tab(fs, game)
    with t_admin:
        admin_tab()


@st.fragment(run_every=4)
def gm_stats():
    fs, game = load()
    players = db.all_players()
    nxt = fs["revealed"] + 1
    locked_now = sum(1 for p in players if nxt in p[3])
    stats(("Players joined", len(players)),
          (f"Locked for round {min(nxt, 4)}", f"{locked_now} of {len(players)}" if fs["revealed"] < 4 else "–", "updates every few seconds"),
          ("News revealed", f"{fs['revealed']} of 4"),
          ("Carbon budget", f"{game.budget:.2f}"))


def run_tab(fs, game):
    revealed, nxt = fs["revealed"], fs["revealed"] + 1
    _, text = phase_text(fs, game)
    st.markdown(f"<div class='phase'>{text}</div>", unsafe_allow_html=True)
    if fs["open"]:
        countdown(fs["deadline"])
    gm_stats()
    st.write("")

    # --- game length
    with st.expander("Game length and timer", expanded=(revealed == 0)):
        a, b = st.columns(2)
        with a:
            m = st.radio("Format", ["Quick game (timed rounds)", "Full week (no timer)"],
                         index=0 if fs["mode"] == "quick" else 1, horizontal=False)
            new_mode = "quick" if m.startswith("Quick") else "week"
        with b:
            rl = st.number_input("Minutes per round", min_value=1.0, max_value=120.0, step=1.0, value=float(fs["round_len"]),
                                 disabled=new_mode == "week",
                                 help="Each round's timer. In a quick game, revealing news starts the next round's timer automatically.")
        if new_mode != fs["mode"] or rl != fs["round_len"]:
            db.set_timing(mode=new_mode, round_len=rl); st.rerun()
        if new_mode == "quick":
            st.caption(f"About {int(4 * rl + 4 * 2 + 10)} minutes in total: 4 rounds of {rl:g} min, about 2 min per news reveal, "
                       "and 10 min to introduce and wrap up.")

    if revealed >= e.ROUNDS:
        st.success("The game is over. Show the Presenter screen for the final results.")
    else:
        st.markdown(f"### {round_name(fs, nxt)}")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**Step 1 · Run the round**")
            if fs["mode"] == "quick":
                b1, b2, b3 = st.columns(3)
                if b1.button(f"{'Restart' if fs['deadline'] else 'Start'} {fs['round_len']:g}-min timer",
                             type="primary" if not fs["deadline"] else "secondary",
                             width="stretch"):
                    db.set_state(open_=True); db.set_deadline(time.time() + 60 * fs["round_len"]); st.rerun()
                if b2.button("+1 minute", disabled=not fs["deadline"], width="stretch"):
                    base_t = max(fs["deadline"] or 0, time.time())
                    db.set_state(open_=True); db.set_deadline(base_t + 60); st.rerun()
                if b3.button("End round now", disabled=not fs["open"], width="stretch"):
                    db.set_state(open_=False); db.set_deadline(None); st.rerun()
                if not fs["deadline"] and fs["open"]:
                    st.caption("Players can already lock portfolios. Start the timer when you're ready.")
            else:
                if fs["open_flag"]:
                    if st.button(f"Close round {nxt} submissions"):
                        db.set_state(open_=False); st.rerun()
                else:
                    if st.button(f"Reopen round {nxt} submissions"):
                        db.set_state(open_=True); st.rerun()
                st.caption("Closing is optional, for example at 5 pm. Revealing the news locks the round anyway.")
            if not fs["open_flag"] and fs["mode"] == "quick" and not fs["deadline"]:
                if st.button("Reopen without a timer"):
                    db.set_state(open_=True); st.rerun()
        with right:
            st.markdown(f"**Step 2 · Reveal news {nxt}**")
            item = game.news(nxt)
            on = game.params(nxt)[e.SHOCK_KEY[nxt]]
            chip = "<span class='chip next'>Shock on</span>" if on else "<span class='chip off'>Shock off: quiet round</span>"
            st.markdown(f"{chip}<br><b>{esc(item['headline'])}</b>", unsafe_allow_html=True)
            follow = (f"starts round {nxt + 1}" + (f" with a {fs['round_len']:g}-min timer" if fs["mode"] == "quick" else "")
                      if nxt < 4 else "ends the game")
            st.caption(f"Locks every round {nxt} portfolio, scores it with the current shock settings, and {follow}. "
                       "Change the shock in the 'Shocks and rules' tab first if you want.")
            sure = st.checkbox(f"Ready to reveal news {nxt}", key=f"sure{nxt}")
            if st.button(f"Reveal news {nxt}", type="primary", disabled=not sure, width="stretch"):
                db.reveal(nxt, fs["round_len"] if fs["mode"] == "quick" else None); st.rerun()

    st.divider()
    if revealed > 0:
        with st.expander("Undo the last reveal (for testing or mistakes)"):
            st.caption("Puts the game back to before the last news item. The settings used for it are unlocked again.")
            if st.button(f"Undo news {revealed}"):
                db.undo_reveal(); st.rerun()
    st.markdown("#### News script")
    for k in range(1, 5):
        done = "revealed" if k <= revealed else "not yet revealed"
        with st.expander(f"News {k} · {game.news(k)['headline']} ({done})"):
            st.write(game.news(k)["body"])


def pct(x):
    return round(float(x) * 100, 4)


def shocks_tab(fs, game):
    revealed = fs["revealed"]
    p = dict(game.p)
    st.markdown("Switch each shock on or off and set its size. A shock's settings are saved when you reveal it, so "
                "changes only ever affect news that hasn't been revealed yet.")
    labels = {1: "News 1 · Carbon price", 2: "News 2 · Coastal flood", 3: "News 3 · Greenwash exposé", 4: "News 4 · Green steel breakthrough"}

    with st.form("shocks"):
        new = {}
        for k in range(1, 5):
            locked = revealed >= k
            src = game.params(k)
            status = ("<span class='chip locked'>Revealed: locked</span>" if locked else
                      "<span class='chip next'>Up next</span>" if k == revealed + 1 else "<span class='chip later'>Later</span>")
            st.markdown(f"#### {labels[k]} &nbsp; {status}", unsafe_allow_html=True)
            key = e.SHOCK_KEY[k]
            c = st.columns(4)
            new[key] = c[0].toggle("Shock on", value=bool(src[key]), disabled=locked, key=f"t_{key}")
            if k == 1:
                new["carbon_r1"] = c[1].number_input("Round 1 hit: % of return lost per unit of intensity", 0.0, 2.0,
                                                     pct(src["carbon_r1"]), 0.01, format="%.2f", disabled=locked) / 100
                new["carbon_later"] = c[2].number_input("Lasting cost in later rounds: % per unit", 0.0, 2.0,
                                                        pct(src["carbon_later"]), 0.01, format="%.2f", disabled=locked) / 100
                new["strong_discount"] = c[3].number_input("Discount for a Strong plan (%)", 0.0, 100.0,
                                                           pct(src["strong_discount"]), 5.0, format="%.0f", disabled=locked) / 100
                st.caption("Example: at 0.15%, a company with intensity 80 loses 12% of return in round 1.")
            elif k == 2:
                new["flood_high"] = -c[1].number_input("Hit to High physical risk (%)", 0.0, 100.0, -pct(src["flood_high"]),
                                                       1.0, format="%.0f", disabled=locked) / 100
                new["flood_medium"] = -c[2].number_input("Hit to Medium physical risk (%)", 0.0, 100.0, -pct(src["flood_medium"]),
                                                         1.0, format="%.0f", disabled=locked) / 100
                new["flood_lasting"] = -c[3].number_input("Lasting cost, High risk, later rounds (%)", 0.0, 100.0,
                                                          -pct(src["flood_lasting"]), 1.0, format="%.0f", disabled=locked) / 100
            elif k == 3:
                new["greenwash_hit"] = -c[1].number_input("EverGreen share fall (%)", 0.0, 100.0, -pct(src["greenwash_hit"]),
                                                          5.0, format="%.0f", disabled=locked) / 100
                c[2].caption("When on, EverGreen's true intensity (60) and plan (None) are revealed and used from this round.")
            else:
                new["greensteel_jump"] = c[1].number_input("Vajra Steel jump (%)", 0.0, 200.0, pct(src["greensteel_jump"]),
                                                           5.0, format="%.0f", disabled=locked) / 100
            if locked:  # keep the saved values for revealed news
                for f in e.GROUPS[k]:
                    new[f] = src[f]
        st.markdown("#### Game rules")
        final_locked = revealed >= 4
        c = st.columns(3)
        new["budget_cut"] = c[0].number_input("Carbon budget: % below the average company", 0.0, 90.0, pct(p["budget_cut"]),
                                              5.0, format="%.0f", disabled=final_locked) / 100
        new["max_weight"] = int(c[1].number_input("Max % in one company", 10, 100, int(p["max_weight"]), 5, disabled=final_locked))
        new["min_holdings"] = int(c[2].number_input("Minimum holdings", 1, 15, int(p["min_holdings"]), 1, disabled=final_locked))
        budget_preview = round(e.BENCHMARK * (1 - new["budget_cut"]), 2)
        st.caption(f"Budget with this setting: {budget_preview:.2f} tCO₂e per ₹ crore (average company: {e.BENCHMARK:.2f}). "
                   "Players see rule changes straight away.")
        saved = st.form_submit_button("Save changes", type="primary")
    if saved:
        db.set_params(new); st.success("Saved. Players' screens update within a few seconds."); st.rerun()

    if st.button("Restore default settings for news not yet revealed"):
        restored = dict(game.p)
        for k in range(revealed + 1, 5):
            for f in e.GROUPS[k]:
                restored[f] = e.DEFAULTS[f]
        if revealed < 4:
            for f in ("budget_cut", "max_weight", "min_holdings"):
                restored[f] = e.DEFAULTS[f]
        db.set_params(restored); st.rerun()

    st.markdown("#### Preview: each company's return per round with these settings")
    st.caption("Revealed rounds show what actually happened. Unrevealed rounds show what will happen if you reveal with "
               "the current settings. Only you can see this.")
    preview = e.Game(fs["params"], fs["snapshots"], 4)
    df = pd.DataFrame({"Company": e.NAMES})
    for k in range(1, 5):
        col = f"R{k}" + (" (revealed)" if k <= revealed else "")
        df[col] = [r * 100 for r in preview.returns(k)]
    df["If held all game"] = [(pd.Series([1 + preview.returns(k)[i] for k in range(1, 5)]).prod() - 1) * 100 for i in range(e.N)]
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.1f%%") for c in df.columns if c != "Company"})


def presenter(fs, game):
    st.caption("Put this on the big screen. It updates by itself.")
    if fs["open"] and fs["deadline"]:
        countdown(fs["deadline"], big=True)
    _, text = phase_text(fs, game)
    st.markdown(f"<div class='phase'>{text}</div>", unsafe_allow_html=True)
    if fs["revealed"]:
        k = fs["revealed"]
        st.markdown(f"<div class='news big'><div class='when'>Latest · {esc(news_when(fs, game, k))}</div>"
                    f"<div class='hl'>{esc(game.news(k)['headline'])}</div><div>{esc(game.news(k)['body'])}</div></div>",
                    unsafe_allow_html=True)
    live_leaderboard(None, big=True, top=10)


def players_tab(fs, game):
    players = db.all_players()
    rows = game.leaderboard(players); by = {r["pid"]: r for r in rows}
    table = []
    for pid, name, dept, subs in players:
        r = by.get(pid)
        table.append({"Player": name, "Department": dept or "",
                      **{f"R{k}": ("Locked" if k in subs else "–") for k in range(1, 5)},
                      "Rank": r["rank"] if (r and fs["revealed"]) else None,
                      "Value (₹ cr)": round(r["value"], 2) if r else None,
                      "Intensity": round(r["intensity"], 2) if r else None})
    if not table:
        st.info("No players yet. Share the app link and ask people to join.")
        return
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
            else:
                st.error("Enter 4 digits.")
    with y:
        st.write("")
        if st.checkbox(f"Remove {who} from the game", key="rmsure") and st.button("Remove player"):
            db.delete_player(names[who]); st.rerun()
    lb = pd.DataFrame([{k: r[k] for k in ("rank", "name", "dept", "value", "change", "intensity", "within", "points")} for r in rows])
    st.download_button("Download leaderboard (CSV)", lb.to_csv(index=False).encode(), "leaderboard.csv", "text/csv")


def admin_tab():
    st.markdown("#### Backup")
    st.caption("Free hosting can restart the app and wipe its data. Download a backup after each round; restore it if needed.")
    st.download_button("Download backup (JSON)", db.export_json().encode(), "netzero_backup.json", "application/json")
    up = st.file_uploader("Restore from a backup", type=["json"])
    if up and st.button("Restore this backup"):
        db.import_json(up.read().decode()); st.success("Restored."); st.rerun()
    st.markdown("#### Reset")
    st.caption("Starts a new game. Your shock settings and game length are kept.")
    keep = st.checkbox("Keep players (only clear portfolios and news)", value=True)
    confirm = st.text_input("Type RESET to confirm")
    if st.button("Reset the game", disabled=confirm != "RESET"):
        db.reset_game(keep_players=keep); st.success("Game reset."); st.rerun()


if mode == "Play":
    play()
else:
    game_master()
