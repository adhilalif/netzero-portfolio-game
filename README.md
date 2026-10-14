# Net Zero Portfolio Game

A web version of the Net Zero Portfolio Game for Climate Change Week (Credibl × BNY Pune).
Individual play: players join with their name and a 4-digit PIN, build a portfolio from 15 fictional
companies and lock it each round. The game master reveals one news item per round, and a live
leaderboard updates for everyone. All companies and figures are fictional.

## Game master sign-in

The username and password are in `.streamlit/secrets.toml`:

```
GM_USER = "gamemaster"
GM_PASSWORD = "..."
```

Keep that file private. It is excluded from Git. If you deploy online, paste the same two lines into the
host's Secrets settings (see Option 2). Without a secrets file, the fallback is `gamemaster` / `credibl-gm`,
and the app shows a warning.

## Option 1: Run it on your laptop (best for an internal test)

1. Install Python 3.10 or newer.
2. In this folder, run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Your browser opens the game. The terminal also shows a **Network URL** (like `http://192.168.1.20:8501`).
   Colleagues on the same Wi-Fi open that link on their phones or laptops to play.
   If they can't connect, allow Python through your firewall when Windows or macOS asks, or use Option 2.

## Option 2: Put it online with Streamlit Community Cloud (free)

1. Create a GitHub repository and upload everything in this folder **except** `.streamlit/secrets.toml`
   and any `game_state.db` file.
2. Go to https://share.streamlit.io, sign in with GitHub, and choose **Create app**.
3. Pick your repository, branch `main`, and main file `app.py`.
4. Open **Advanced settings → Secrets** and paste the two lines from `.streamlit/secrets.toml`.
5. Deploy. You get a link like `https://your-app-name.streamlit.app` to share.

**Before the real event:** check with BNY IT that staff can open `*.streamlit.app` links. Free hosting can
restart when idle and wipe the game data, so download a backup after each round (Backup and reset tab).

## Running a quick game (30-60 minutes)

1. Open the app, choose **Game master** in the sidebar (on a phone, tap the arrow at the top left), and sign in.
2. **Run the game → Game length and timer:** choose *Quick game* and set the minutes per round (5-6 works well).
3. Share the link. Players join and can lock a round 1 portfolio straight away.
4. Press **Start timer**. Everyone sees a countdown. When it hits zero, locking stops automatically.
   Use **+1 minute** if people need more time, or **End round now** to stop early.
5. Tick **Ready to reveal**, then press **Reveal news**. This scores the round, posts the news to every
   player, and starts the next round's timer automatically.
6. Repeat until news 4. Round 4 is the final lock: portfolios must be within the carbon budget to win.
7. Put the **Presenter screen** tab on the big screen: it shows the countdown, the latest news and the leaderboard.

Players' screens update by themselves within a few seconds when you start a timer or reveal news.

For the full-week version, choose *Full week (no timer)*. You then close rounds yourself (for example at 5 pm)
and reveal each morning.

## Changing shocks during the game

**Shocks and rules** tab:
- Switch any news item's shock **on or off**. A shock that is off becomes a "quiet day in the markets" for players.
  Switching off the greenwash exposé means EverGreen's true figures are never revealed.
- Change each shock's size, for example a bigger flood or a smaller green-steel jump.
- Change the rules: the carbon budget, the maximum % in one company, and the minimum number of holdings.
- Press **Save changes**. The preview table shows every company's return per round under your settings.

A news item's settings are saved at the moment you reveal it, so changes only affect news not yet revealed.
Revealed news shows as locked. **Undo the last reveal** unlocks it again (handy when testing).

## Other game master tools

- **Players:** who has locked each round, reset a forgotten PIN, remove a test player, download the leaderboard (CSV).
- **Backup and reset:** download or restore a backup, or reset the game. "Keep players" clears only portfolios
  and news; your shock settings and timer are kept.

## Files

| File | What it does |
|---|---|
| `app.py` | The Streamlit app: player pages and game master pages |
| `engine.py` | Scoring rules and default shock settings (same numbers as the Excel master) |
| `game_data.py` | The 15 companies, their figures and analyst notes |
| `storage.py` | Shared game state, saved in a small SQLite file (`game_state.db`) |
| `tests/test_engine.py` | Checks scoring against the Excel master and the shock settings rules |
| `.streamlit/config.toml` | Colours and settings |
| `.streamlit/secrets.toml` | Game master username and password (private) |
