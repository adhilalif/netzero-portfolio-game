# Net Zero Portfolio Game

A web version of the Net Zero Portfolio Game for Climate Change Week (Credibl × BNY Pune).
Individual play. Players join with their name and a 4-digit PIN, build a portfolio from 15 fictional
companies, and lock it each round. The game master reveals one news item per round, and a live
leaderboard updates for everyone. All companies and figures are fictional.

## Files

| File | What it does |
|---|---|
| `app.py` | The Streamlit app: player pages and the game master pages |
| `engine.py` | Scoring rules (same numbers as the Excel master). Edit game parameters here |
| `game_data.py` | The 15 companies, their figures and analyst notes |
| `storage.py` | Shared game state, saved in a small SQLite file (`game_state.db`) |
| `tests/test_engine.py` | Checks the scoring matches the Excel master |
| `.streamlit/config.toml` | Colours and settings |

## Option 1: Run it on your laptop (good for an internal test)

1. Install Python 3.10 or newer.
2. In this folder, run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Your browser opens the game. The terminal also shows a **Network URL** (like `http://192.168.1.20:8501`).
   Colleagues on the same Wi-Fi can open that link on their phones or laptops to play.

## Option 2: Put it online with Streamlit Community Cloud (free)

1. Create a GitHub repository and upload everything in this folder (keep the `.streamlit` folder).
   Do not upload `game_state.db` if one exists.
2. Go to https://share.streamlit.io, sign in with GitHub, and choose **Create app**.
3. Pick your repository, branch `main`, and main file `app.py`.
4. Open **Advanced settings → Secrets** and add:
   ```
   GM_PASSWORD = "choose-a-strong-password"
   ```
5. Deploy. You get a link like `https://your-app-name.streamlit.app` to share.

**Before the real event:**
- Check with BNY IT that staff can open `*.streamlit.app` on the office network and on phones.
- Free hosting can restart or put the app to sleep when nobody uses it, which wipes the game data.
  Open the app shortly before each round, and download a backup after each round
  (Game master → Backup and reset). You can restore it in one click.
- For a large office, a paid host (for example Render, Railway or Azure App Service) is more reliable.
  The app runs there unchanged with `streamlit run app.py`.

## Running the game (game master)

Open the app, choose **Game master** in the sidebar (on a phone, tap the arrow at the top left) and enter
the password. The default is `credibl-gm` if you haven't set `GM_PASSWORD`; change it before sharing the link.

| When | Do this |
|---|---|
| Monday | Share the link. Players join and lock their round 1 portfolio |
| 5 pm each day (optional) | **Close round** so nobody can change their portfolio |
| Next morning | **Reveal news** (tick the box, then press the button). This scores the locked portfolios and opens the next round |
| Thursday | Round 4 is the final lock: portfolios must be within the carbon budget to win |
| Friday finale | Reveal news 4, then show the **Presenter screen** on the big screen |

Other tools:
- **Undo the last reveal**, if you press it by mistake or during a test.
- **Players**: see who has locked each round, reset a forgotten PIN, remove a test player, and download the leaderboard as CSV.
- **Backup and reset**: download or restore a backup, or reset the game. "Keep players" clears only portfolios and news.

For a quick 45-minute internal test, run all four rounds back to back, giving players about 5 minutes per round.

## Rules players see

- Start with ₹100 crore. Hold at least 5 companies, no more than 25% in any one, weights adding up to 100%.
- Each news item hits the portfolio locked before it, so players can't dodge it.
- No new portfolio means the previous one carries over. Late joiners hold cash (0% return) until their first lock.
- To win, the final (round 4) portfolio must have a carbon intensity at or below 27.25 tCO₂e per ₹ crore.
- Final points: 300 / 200 / 100 for the top three within budget, plus 50 for everyone within budget.

## Changing the game

- Company figures and analyst notes: `game_data.py`.
- Shock sizes, budget cut, holding rules: the constants at the top of `engine.py`.
- News text: `NEWS` in `engine.py`.
- After a change, run `python tests/test_engine.py`. The test that compares against the Excel master will fail
  if you changed the numbers on purpose; update its expected values.
