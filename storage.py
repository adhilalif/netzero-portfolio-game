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


def get_state():
    with _conn() as c:
        d = dict(c.execute("SELECT key, value FROM state").fetchall())
    return int(d.get("revealed", 0)), d.get("open", "1") == "1"


def set_state(revealed=None, open_=None):
    with _LOCK, _conn() as c:
        if revealed is not None:
            c.execute("UPDATE state SET value=? WHERE key='revealed'", (str(int(revealed)),))
        if open_ is not None:
            c.execute("UPDATE state SET value=? WHERE key='open'", ("1" if open_ else "0",))


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
        d = dict(c.execute("SELECT key, value FROM state").fetchall())
        revealed, is_open = int(d["revealed"]), d["open"] == "1"
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
        c.execute("DELETE FROM submissions"); c.execute("DELETE FROM players")
        c.executemany("INSERT INTO players VALUES (?,?,?,?,?)", [tuple(r) for r in data["players"]])
        c.executemany("INSERT INTO submissions VALUES (?,?,?,?)", [tuple(r) for r in data["submissions"]])
        for k, v in data["state"].items():
            c.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (k, str(v)))
