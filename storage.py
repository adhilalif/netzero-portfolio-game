"""Shared game state in SQLite, safe for many players on one Streamlit server."""
import hashlib
import json
import os
import sqlite3
import threading
import time

DB_PATH = os.environ.get("GAME_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_state.db"))
_LOCK = threading.Lock()


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    with _LOCK, _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            dept TEXT,
            pin_hash TEXT NOT NULL,
            created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS submissions (
            player_id INTEGER NOT NULL,
            round INTEGER NOT NULL,
            weights TEXT NOT NULL,
            ts REAL NOT NULL,
            PRIMARY KEY (player_id, round));
        CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        c.execute("INSERT OR IGNORE INTO state VALUES ('revealed','0')")
        c.execute("INSERT OR IGNORE INTO state VALUES ('open','1')")


def _hash(name, pin):
    return hashlib.sha256(f"netzero:{name.strip().lower()}:{pin}".encode()).hexdigest()


def _state(c):
    return dict(c.execute("SELECT key, value FROM state").fetchall())


def _is_open(d, now=None):
    if d.get("open", "1") != "1":
        return False
    dl = d.get("deadline", "")
    return not dl or (now or time.time()) < float(dl)


def get_state():
    """(revealed, submissions_open). Open means the flag is on AND any round timer hasn't run out."""
    with _conn() as c:
        d = _state(c)
    return int(d.get("revealed", 0)), _is_open(d)


def full_state():
    """Everything the app needs in one read."""
    with _conn() as c:
        d = _state(c)
    snaps = {k: json.loads(d[f"params_r{k}"]) for k in range(1, 5) if f"params_r{k}" in d}
    dl = d.get("deadline", "")
    return dict(revealed=int(d.get("revealed", 0)), open=_is_open(d), open_flag=d.get("open", "1") == "1",
                deadline=float(dl) if dl else None, params=json.loads(d.get("params", "{}")),
                snapshots=snaps, mode=d.get("mode", "quick"), round_len=float(d.get("round_len", "6")))


def _put(c, key, value):
    c.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (key, str(value)))


def set_state(revealed=None, open_=None):
    with _LOCK, _conn() as c:
        if revealed is not None:
            _put(c, "revealed", int(revealed))
        if open_ is not None:
            _put(c, "open", "1" if open_ else "0")


def set_params(params):
    with _LOCK, _conn() as c:
        _put(c, "params", json.dumps(params))


def set_timing(mode=None, round_len=None):
    with _LOCK, _conn() as c:
        if mode is not None:
            _put(c, "mode", mode)
        if round_len is not None:
            _put(c, "round_len", float(round_len))


def set_deadline(epoch):
    """epoch=None clears the timer."""
    with _LOCK, _conn() as c:
        _put(c, "deadline", "" if epoch is None else float(epoch))


def reveal(k, start_next_timer_minutes=None):
    """Reveal news k: snapshot the current settings for round k, then open round k+1."""
    with _LOCK, _conn() as c:
        d = _state(c)
        if int(d.get("revealed", 0)) != k - 1:
            return False
        _put(c, f"params_r{k}", d.get("params", "{}"))
        _put(c, "revealed", k)
        _put(c, "open", "1" if k < 4 else "0")
        if k < 4 and start_next_timer_minutes:
            _put(c, "deadline", time.time() + 60 * float(start_next_timer_minutes))
        else:
            _put(c, "deadline", "")
        return True


def undo_reveal():
    with _LOCK, _conn() as c:
        d = _state(c)
        k = int(d.get("revealed", 0))
        if k == 0:
            return
        c.execute("DELETE FROM state WHERE key=?", (f"params_r{k}",))
        _put(c, "revealed", k - 1)
        _put(c, "open", "0")
        _put(c, "deadline", "")


def register(name, dept, pin):
    name = " ".join(name.split())
    with _LOCK, _conn() as c:
        try:
            cur = c.execute("INSERT INTO players (name, dept, pin_hash, created) VALUES (?,?,?,?)",
                            (name, dept.strip(), _hash(name, pin), time.time()))
            return cur.lastrowid, None
        except sqlite3.IntegrityError:
            return None, "That name is already taken. Use 'I've played before' with your PIN, or add your surname."


def login(name, pin):
    name = " ".join(name.split())
    with _conn() as c:
        row = c.execute("SELECT id, pin_hash, name FROM players WHERE name=?", (name,)).fetchone()
    if not row or row[1] != _hash(row[2], pin):
        return None
    return row[0]


def player(pid):
    with _conn() as c:
        row = c.execute("SELECT id, name, dept FROM players WHERE id=?", (pid,)).fetchone()
    return row


def submit(pid, weights):
    """Lock a portfolio for the round currently open. Returns (round, error)."""
    with _LOCK, _conn() as c:
        d = _state(c)
        revealed, is_open = int(d["revealed"]), _is_open(d)
        rnd = revealed + 1
        if not is_open or rnd > 4:
            return None, "Submissions are closed right now. Wait for the game master to open the next round."
        c.execute("INSERT OR REPLACE INTO submissions VALUES (?,?,?,?)",
                  (pid, rnd, json.dumps([float(w) for w in weights]), time.time()))
        return rnd, None


def subs_for(pid):
    with _conn() as c:
        rows = c.execute("SELECT round, weights FROM submissions WHERE player_id=?", (pid,)).fetchall()
    return {r: json.loads(w) for r, w in rows}


def all_players():
    """[(id, name, dept, {round: weights})]"""
    with _conn() as c:
        ps = c.execute("SELECT id, name, dept FROM players ORDER BY name COLLATE NOCASE").fetchall()
        ss = c.execute("SELECT player_id, round, weights FROM submissions").fetchall()
    subs = {}
    for pid, rnd, w in ss:
        subs.setdefault(pid, {})[rnd] = json.loads(w)
    return [(pid, name, dept, subs.get(pid, {})) for pid, name, dept in ps]


def reset_pin(pid, pin):
    with _LOCK, _conn() as c:
        name = c.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()[0]
        c.execute("UPDATE players SET pin_hash=? WHERE id=?", (_hash(name, pin), pid))


def delete_player(pid):
    with _LOCK, _conn() as c:
        c.execute("DELETE FROM submissions WHERE player_id=?", (pid,))
        c.execute("DELETE FROM players WHERE id=?", (pid,))


def reset_game(keep_players):
    with _LOCK, _conn() as c:
        c.execute("DELETE FROM submissions")
        if not keep_players:
            c.execute("DELETE FROM players")
        c.execute("UPDATE state SET value='0' WHERE key='revealed'")
        c.execute("UPDATE state SET value='1' WHERE key='open'")
        c.execute("DELETE FROM state WHERE key LIKE 'params_r%' OR key='deadline'")


def export_json():
    with _conn() as c:
        data = dict(
            players=[list(r) for r in c.execute("SELECT id, name, dept, pin_hash, created FROM players")],
            submissions=[list(r) for r in c.execute("SELECT player_id, round, weights, ts FROM submissions")],
            state=dict(c.execute("SELECT key, value FROM state").fetchall()),
            exported=time.time())
    return json.dumps(data, indent=1)


def import_json(text):
    data = json.loads(text)
    with _LOCK, _conn() as c:
        c.execute("DELETE FROM submissions"); c.execute("DELETE FROM players"); c.execute("DELETE FROM state")
        c.executemany("INSERT INTO players VALUES (?,?,?,?,?)", [tuple(r) for r in data["players"]])
        c.executemany("INSERT INTO submissions VALUES (?,?,?,?)", [tuple(r) for r in data["submissions"]])
        for k, v in data["state"].items():
            c.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (k, str(v)))
