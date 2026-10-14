"""Scoring engine for the Net Zero Portfolio Game.

Pure Python, no Streamlit. With default settings it reproduces the Excel master exactly.
Shocks and rules are parameters the game master can change. The values in force when a news
item is revealed are snapshotted, so later changes only affect rounds not yet revealed.
All companies and figures are fictional.
"""
import copy
from game_data import COMPANIES

N = len(COMPANIES)
NAMES = [c[0] for c in COMPANIES]
ROUNDS = 4
START_VALUE = 100.0  # ₹ crore

DEFAULTS = dict(
    # game rules
    budget_cut=0.30,          # final portfolio must be this far below the benchmark
    max_weight=25,            # % in any one company
    min_holdings=5,
    # news 1: carbon price
    carbon_on=True, carbon_r1=0.0015, carbon_later=0.0005, strong_discount=0.50,
    # news 2: coastal flood
    flood_on=True, flood_high=-0.15, flood_medium=-0.05, flood_lasting=-0.03,
    # news 3: greenwash expose
    greenwash_on=True, greenwash_hit=-0.25,
    # news 4: green steel
    greensteel_on=True, greensteel_jump=0.30,
)

# which settings belong to which news item (locked once that news is revealed)
GROUPS = {
    1: ["carbon_on", "carbon_r1", "carbon_later", "strong_discount"],
    2: ["flood_on", "flood_high", "flood_medium", "flood_lasting"],
    3: ["greenwash_on", "greenwash_hit"],
    4: ["greensteel_on", "greensteel_jump"],
}


def _field(i):
    name, sector, base, rep, true, rplan, tplan, risk, clue, special = COMPANIES[i]
    return dict(name=name, sector=sector, base=base, rep=rep, true=true, rplan=rplan,
                tplan=tplan, risk=risk, clue=clue, special=special)


CO = [_field(i) for i in range(N)]
BENCHMARK = sum(c["rep"] for c in CO) / N

NEWS = {
    1: dict(when="Tuesday, 10 am", headline="Government announces a carbon price on industrial emissions",
            body="From this quarter, companies pay for every tonne of CO₂ they emit. High emitters take a hit now, "
                 "and the cost continues in every later round. Companies with credible transition plans are less exposed."),
    2: dict(when="Wednesday, 10 am", headline="Severe coastal flooding hits western India",
            body="Ports, refineries and seafront property are damaged. Insurers raise premiums for exposed sites from now on."),
    3: dict(when="Thursday, 10 am", headline="Investigation: EverGreen Agro's 'carbon neutral' claim does not hold up",
            body="Investigators find EverGreen's figures were self-reported and never independently checked. Its true "
                 "emissions intensity is 60 tCO₂e per ₹ crore, not 5, and its transition plan is downgraded. Shares fall "
                 "sharply. The next portfolio is your final lock, and it must be within the carbon budget to win."),
    4: dict(when="Friday finale", headline="Vajra Steel's green hydrogen pilot succeeds early",
            body="Vajra signs long-term contracts to supply low-carbon steel to automakers. Shares jump at the final market close."),
}
QUIET_NEWS = dict(headline="A quiet day in the markets",
                  body="No major news this round. Companies earn their expected returns, plus any lasting effects from earlier news.")
SHOCK_KEY = {1: "carbon_on", 2: "flood_on", 3: "greenwash_on", 4: "greensteel_on"}


def merged(params):
    p = copy.deepcopy(DEFAULTS)
    if params:
        p.update({k: v for k, v in params.items() if k in DEFAULTS})
    return p


class Game:
    """Everything that depends on the current settings and how many news items are revealed.

    current: settings in force now (used for rounds not yet revealed and for the rules)
    snapshots: {round: settings used when that news was revealed}
    """

    def __init__(self, current=None, snapshots=None, revealed=0):
        self.p = merged(current)
        self.revealed = int(revealed)
        self.snap = {int(k): merged(v) for k, v in (snapshots or {}).items()}

    # ---- settings per round
    def params(self, rnd):
        return self.snap.get(rnd, self.p)

    @property
    def budget(self):
        return round(BENCHMARK * (1 - self.p["budget_cut"]), 2)

    @property
    def max_weight(self):
        return int(self.p["max_weight"])

    @property
    def min_holdings(self):
        return int(self.p["min_holdings"])

    def exposed(self, upto_round=None):
        """Was the greenwash expose active for the round in question (round 3 onwards)?"""
        r = self.revealed if upto_round is None else upto_round
        return r >= 3 and bool(self.params(3)["greenwash_on"])

    # ---- company figures
    def intensity(self, i, rnd):
        """Intensity used to score a portfolio held in round `rnd`."""
        return CO[i]["true"] if self.exposed(rnd) else CO[i]["rep"]

    def plan(self, i, rnd):
        return CO[i]["tplan"] if self.exposed(rnd) else CO[i]["rplan"]

    def known_intensity(self, i):
        """What players can see now."""
        return CO[i]["true"] if self.exposed() else CO[i]["rep"]

    def known_plan(self, i):
        return CO[i]["tplan"] if self.exposed() else CO[i]["rplan"]

    def corrected(self, i):
        return self.exposed() and CO[i]["true"] != CO[i]["rep"]

    def company_return(self, i, rnd):
        p = self.params(rnd)
        p1 = self.params(1)
        c = CO[i]
        r = c["base"]
        # carbon price: introduced by news 1, lasting cost afterwards (if news 1 was on)
        if p1["carbon_on"] and (rnd == 1 or p["carbon_on"]):
            rate = p["carbon_r1"] if rnd == 1 else p["carbon_later"]
            strong = self.plan(i, rnd) == "Strong"
            r -= self.intensity(i, rnd) * rate * ((1 - p["strong_discount"]) if strong else 1)
        # flood: hit in round 2, lasting cost for High risk afterwards (if news 2 was on)
        if rnd == 2 and p["flood_on"]:
            r += {"High": p["flood_high"], "Medium": p["flood_medium"]}.get(c["risk"], 0.0)
        if rnd >= 3 and self.params(2)["flood_on"] and p["flood_on"] and c["risk"] == "High":
            r += p["flood_lasting"]
        if rnd == 3 and p["greenwash_on"] and c["special"] == "Greenwash trap":
            r += p["greenwash_hit"]
        if rnd == 4 and p["greensteel_on"] and c["special"] == "Green-steel winner":
            r += p["greensteel_jump"]
        return r

    def returns(self, rnd):
        return [self.company_return(i, rnd) for i in range(N)]

    # ---- news
    def news(self, k):
        if not self.params(k)[SHOCK_KEY[k]]:
            return dict(when=NEWS[k]["when"], **QUIET_NEWS)
        return NEWS[k]

    # ---- portfolios
    def validate(self, weights):
        problems = []
        total = sum(weights)
        if abs(total - 100) > 0.01:
            problems.append(f"Weights add up to {total:g}%; they must add up to 100%.")
        held = sum(1 for w in weights if w > 0)
        if held < self.min_holdings:
            problems.append(f"You hold {held} companies; hold at least {self.min_holdings}.")
        if max(weights) > self.max_weight:
            problems.append(f"No more than {self.max_weight}% in any one company.")
        if min(weights) < 0:
            problems.append("Weights cannot be negative.")
        return problems

    @staticmethod
    def portfolio_intensity(weights, intensities):
        total = sum(weights)
        if total <= 0:
            return 0.0
        return sum(w * x for w, x in zip(weights, intensities)) / total

    @staticmethod
    def held_portfolios(subs):
        """No submission in a round: the previous portfolio carries over.
        Before a player's first submission their money sits in cash (None): 0% return, 0 intensity."""
        held, current = {}, None
        for k in range(1, ROUNDS + 1):
            if subs.get(k) is not None:
                current = list(subs[k])
            held[k] = current
        return held

    def score(self, subs):
        held = self.held_portfolios(subs)
        value, values = START_VALUE, []
        for k in range(1, self.revealed + 1):
            w = held[k]
            if w:
                value *= 1 + sum(wi * r for wi, r in zip(w, self.returns(k))) / sum(w)
            values.append(value)
        rnd = max(self.revealed, 1)
        w = held[rnd]
        inten = self.portfolio_intensity(w, [self.intensity(i, rnd) for i in range(N)]) if w else 0.0
        return dict(values=values, value=value, intensity=inten, within=inten <= self.budget,
                    started=any(held[k] for k in range(1, ROUNDS + 1)))

    def leaderboard(self, players):
        """players: [(id, name, dept, subs)]. Rounds 1-3 rank by value. After the final round,
        players over budget rank below everyone within budget and earn no points."""
        final = self.revealed >= ROUNDS
        rows = []
        for pid, name, dept, subs in players:
            s = self.score(subs)
            if not s["started"]:
                continue
            rows.append(dict(pid=pid, name=name, dept=dept or "", value=s["value"],
                             change=s["value"] / START_VALUE - 1, intensity=s["intensity"],
                             within=s["within"], eligible=(not final) or s["within"]))
        rows.sort(key=lambda r: (not r["eligible"], -round(r["value"], 9), r["intensity"], r["name"].lower()))
        for n, r in enumerate(rows, start=1):
            r["rank"] = n
            r["points"] = (({1: 300, 2: 200, 3: 100}.get(n, 0) + 50) if r["eligible"] else 0) if final else None
        return rows
