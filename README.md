# Aviator Auto-Stake Bot

This repository contains the first implementation of the Aviator Auto-Stake Bot described in `doc/Aviator_Auto_Stake_Bot_Implementation_Plan-1.md`.

The MVP is deliberately safe to develop:

- the staking, risk, and persistence layers are independent of any betting site;
- browser selectors are configured in `config/settings.json`;
- the default mode is `dry_run: true`, so no real bet is placed until the user explicitly configures a target site and disables dry-run;
- the controller stops on loss/profit/streak/stake limits and supports an emergency stop.

## Quick start

```powershell
python -m aviator_bot.main
```

To run the read-only observer after placing the current iLOTBET URL in `config/settings.json`:

```powershell
python -m aviator_bot.main --observe
```

For an expiring iLOTBET link, pass it for one run instead of saving it:

```powershell
python -m aviator_bot.main --observe --url "<current iLOTBET URL>"
```

BC.Game Crash is also supported through a built-in selector profile. Use the
dedicated settings file (or `--site bcgame`) to open the main crash page; it
does not use an iframe:

```powershell
python -m aviator_bot.main --observe --settings config/bcgame_settings.json --site bcgame
python -m aviator_bot.main --paper-trade --settings config/bcgame_settings.json --site bcgame
```

The dashboard's **Platform** selector switches between iLOTBET and BC.Game and
updates the URL/selectors automatically. Both observer and paper-trade modes
remain read-only: they never click Bet or submit a wager.

Every observed crash result is stored in `observed_rounds` with its platform
name, so iLOTBET and BC.Game histories remain separate. Use the dashboard's
**Export TXT**, **Export JSON**, or **Export Markdown** buttons to save the
currently selected platform's recent results.

The read-only observer gently scrolls the page at a random interval between
30 and 90 seconds to keep the session active. Configure
`activity_scroll_enabled`, `activity_scroll_min_seconds`, and
`activity_scroll_max_seconds` in the browser settings if needed. Bet timing is
not randomized because the application does not submit live wagers.

The bundled profiles use the requested paper strategy defaults: 50 base stake,
1.5× auto-cashout target, and a 3× progression after each loss (reset to 50
after a win). These values can be changed in the dashboard before starting.

The observer prints phase, balance, current multiplier, and the latest history multiplier. It never fills a stake field or clicks a betting control.

For paper trading, use the dashboard's **Paper-trade live page** execution mode, or run:

```powershell
python -m aviator_bot.main --paper-trade --url "<current iLOTBET URL>"
```

Paper trading plans and settles stakes from observed rounds, applies the configured risk limits, and writes simulated results to `round_history` without clicking the site's BET control.

The browser uses `data/browser_profile` as a persistent Playwright profile. Log in manually in the opened Chromium window; the session is reused on later observer launches. Remove that directory only if you intentionally want to clear the saved session.

Paper-trading uses a separate profile with a `_paper` suffix so it can run
without locking an already-open observer browser.

When paper trading is started from the dashboard, its observer snapshots are
also fed into the dashboard status fields. You do not need to press
**Connect observer** separately; that button is only for a standalone
read-only observer session.

The dashboard also provides **Manual-assist (click Bet yourself)**. It runs the
same read-only calculation, displays the next stake, and offers **Copy next
stake** so you can paste it into the site before making your own final Bet
decision.

For development, install the optional UI/browser dependencies:

```powershell
pip install -r requirements.txt
playwright install chromium
```

The dashboard starts in dry-run mode by default. Log in manually in the browser context when using a real site; credentials are not stored by this application.

## Project layout

`aviator_bot/strategy` contains stake progression algorithms, `aviator_bot/risk` enforces account limits, `aviator_bot/database` records every round, `aviator_bot/browser` abstracts game interaction, and `aviator_bot/interface` provides the desktop dashboard.

The browser adapter intentionally does not guess site-specific selectors. Update `config/settings.json` with selectors for the chosen site and test in dry-run before enabling live interaction.

The BC.Game profile is stored in `config/bcgame_settings.json` and uses a
persistent `data/browser_profile_bcgame` session, so you can log in manually in
the opened browser and reconnect without entering credentials into the bot.

## iLOTBET / Best Aviator selector profile

The supplied iLOTBET page was inspected and the current panel uses these selectors:

- game iframe: `iframe#iframe`
- betting-window indicator: `.awaiting`
- stake field (first bet card): `.bet-amount-input`
- auto tab (first bet card): `.common-tabs-container .tab-item:nth-child(2)`
- auto-cashout field (first bet card): `.cash-out-odds-input`
- bet control (first bet card): `.bet-button`
- live/completed multiplier: `.odds-box-value`

These are already populated in `config/settings.json`. The page URL is intentionally left blank because the supplied URL contains a session/content token that may expire. Paste the current URL locally when testing live mode.
