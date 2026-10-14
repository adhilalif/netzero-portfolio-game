"""Scoring engine for the Net Zero Portfolio Game.

Pure Python, no Streamlit. Mirrors the Excel master file exactly:
each round, a holding earns its base return plus that round's shock.
All companies and figures are fictional.
"""
from game_data import COMPANIES

N = len(COMPANIES)
NAMES = [c[0] for c in COMPANIES]

# Game parameters (same defaults as the Excel master's Settings sheet)
START_VALUE = 100.0          # ₹ crore
BUDGET_CUT = 0.30            # final portfolio must be 30% below the benchmark
MAX_WEIGHT = 25              # % in any one company
MIN_HOLDINGS = 5
CARBON_PRICE_R1 = 0.0015     # return lost per tCO2e/₹ cr in round 1
CARBON_PRICE_LATER = 0.0005  # lasting cost in rounds 2-4
STRONG_PLAN_DISCOUNT = 0.50  # strong-plan companies pay half the carbon cost
FLOOD_HIGH = -0.15
FLOOD_MEDIUM = -0.05
FLOOD_LASTING_HIGH = -0.03
GREENWASH_HIT = -0.25
GREEN_STEEL_JUMP = 0.30
ROUNDS = 4


def _field(i):
    name, sector, base, rep, true, rplan, tplan, risk, clue, special = COMPANIES[i]
    return dict(name=name, sector=sector, base=base, rep=rep, true=true, rplan=rplan,
                tplan=tplan, risk=risk, clue=clue, special=special)


CO = [_field(i) for i in range(N)]
BENCHMARK = sum(c["rep"] for c in CO) / N
BUDGET = round(BENCHMARK * (1 - BUDGET_CUT), 2)


def intensity(i, rnd):
    """Intensity used for scoring a portfolio held in round `rnd` (reported in 1-2, true in 3-4)."""
    return CO[i]["rep"] if rnd <= 2 else CO[i]["true"]


def known_intensity(i, revealed):
    """What players can see after `revealed` news items (the exposé is news 3)."""
    return CO[i]["true"] if revealed >= 3 else CO[i]["rep"]


def known_plan(i, revealed):
    return CO[i]["tplan"] if revealed >= 3 else CO[i]["rplan"]


def company_return(i, rnd):
    c = CO[i]
    strong = (c["rplan"] if rnd <= 2 else c["tplan"]) == "Strong"
    rate = CARBON_PRICE_R1 if rnd == 1 else CARBON_PRICE_LATER
    r = c["base"] - intensity(i, rnd) * rate * ((1 - STRONG_PLAN_DISCOUNT) if strong else 1)
    if rnd == 2:
        r += {"High": FLOOD_HIGH, "Medium": FLOOD_MEDIUM}.get(c["risk"], 0.0)
    if rnd >= 3 and c["risk"] == "High":
        r += FLOOD_LASTING_HIGH
    if rnd == 3 and c["special"] == "Greenwash trap":
        r += GREENWASH_HIT
    if rnd == 4 and c["special"] == "Green-steel winner":
        r += GREEN_STEEL_JUMP
    return r


RETURNS = {k: [company_return(i, k) for i in range(N)] for k in range(1, ROUNDS + 1)}


def validate(weights):
    """Return a list of problems; empty list means the portfolio is valid."""
    problems = []
    total = sum(weights)
    if abs(total - 100) > 0.01:
        problems.append(f"Weights add up to {total:g}%; they must add up to 100%.")
    held = sum(1 for w in weights if w > 0)
    if held < MIN_HOLDINGS:
        problems.append(f"You hold {held} companies; hold at least {MIN_HOLDINGS}.")
    if max(weights) > MAX_WEIGHT:
        problems.append(f"No more than {MAX_WEIGHT}% in any one company.")
    if min(weights) < 0:
        problems.append("Weights cannot be negative.")
    return problems


def portfolio_intensity(weights, intensities):
    total = sum(weights)
    if total <= 0:
        return 0.0
    return sum(w * x for w, x in zip(weights, intensities)) / total


def held_portfolios(subs):
    """subs: {round: weights}. Returns {round: weights or None} for rounds 1-4.

    A round with no submission carries the previous portfolio over.
    Before a player's first submission, their money sits in cash (None): 0% return, 0 intensity.
    """
    held, current = {}, None
    for k in range(1, ROUNDS + 1):
        if k in subs and subs[k] is not None:
            current = list(subs[k])
        held[k] = current
    return held


def score(subs, revealed):
    """Score one player after `revealed` news items.

    Returns dict with values (list, one per revealed round), value, the intensity of the
    portfolio held in the latest revealed round, and whether it is within budget.
    """
    held = held_portfolios(subs)
    value, values = START_VALUE, []
    for k in range(1, revealed + 1):
        w = held[k]
        if w:
            value *= 1 + sum(wi * r for wi, r in zip(w, RETURNS[k])) / sum(w)
        values.append(value)
    rnd = max(revealed, 1)
    w = held[rnd] if revealed else held.get(1)
    inten = portfolio_intensity(w, [intensity(i, rnd) for i in range(N)]) if w else 0.0
    return dict(values=values, value=value, intensity=inten, within=inten <= BUDGET,
                started=any(held[k] for k in range(1, ROUNDS + 1)))


def leaderboard(players, revealed):
    """players: list of (player_id, name, dept, subs). Returns ranked list of dicts.

    Rounds 1-3 rank by value. After the final round, players over budget drop below
    everyone within budget and earn no points. Ties go to the lower intensity.
    """
    rows = []
    for pid, name, dept, subs in players:
        s = score(subs, revealed)
        if not s["started"]:
            continue
        final = revealed >= ROUNDS
        eligible = (not final) or s["within"]
        rows.append(dict(pid=pid, name=name, dept=dept or "", value=s["value"],
                         change=s["value"] / START_VALUE - 1, intensity=s["intensity"],
                         within=s["within"], eligible=eligible))
    rows.sort(key=lambda r: (not r["eligible"], -round(r["value"], 9), r["intensity"], r["name"].lower()))
    for n, r in enumerate(rows, start=1):
        r["rank"] = n
        r["points"] = None
        if revealed >= ROUNDS:
            r["points"] = ({1: 300, 2: 200, 3: 100}.get(n, 0) + 50) if r["eligible"] else 0
    return rows


NEWS = {
    1: dict(when="Tuesday, 10 am", headline="Government announces a carbon price on industrial emissions",
            body="From this quarter, companies pay for every tonne of CO₂ they emit. High emitters take a hit now, "
                 "and the cost continues in every later round. Companies with credible transition plans are less exposed."),
    2: dict(when="Wednesday, 10 am", headline="Severe coastal flooding hits western India",
            body="Ports, refineries and seafront property are damaged. Insurers raise premiums for exposed sites from now on."),
    3: dict(when="Thursday, 10 am", headline="Investigation: EverGreen Agro's 'carbon neutral' claim does not hold up",
            body="Investigators find EverGreen's figures were self-reported and never independently checked. Its true "
                 "emissions intensity is 60 tCO₂e per ₹ crore, not 5, and its transition plan is downgraded. Shares fall "
                 "sharply. Today's portfolio is your final lock, and it must be within the carbon budget to win."),
    4: dict(when="Friday finale", headline="Vajra Steel's green hydrogen pilot succeeds early",
            body="Vajra signs long-term contracts to supply low-carbon steel to automakers. Shares jump at the final market close."),
}

ROUND_LABEL = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday (final lock)"}
