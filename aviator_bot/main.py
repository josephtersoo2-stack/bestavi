from __future__ import annotations

import argparse
import threading
import time
from dataclasses import replace
from pathlib import Path

from aviator_bot.browser.controller import DryRunAdapter, PlaywrightAdapter
from aviator_bot.browser.observer import PlaywrightObserver
from aviator_bot.bot.paper import PaperTradingController
from aviator_bot.bot.controller import BotController
from aviator_bot.config.settings import load_settings
from aviator_bot.config.site_profiles import profile
from aviator_bot.interface.dashboard import run_dashboard


def main() -> None:
    parser = argparse.ArgumentParser(description="Aviator auto-stake bot")
    parser.add_argument("--settings", default="config/settings.json")
    parser.add_argument("--no-ui", action="store_true", help="run a short dry-run controller session")
    parser.add_argument("--observe", action="store_true", help="observe the configured live page without betting")
    parser.add_argument("--paper-trade", action="store_true", help="run strategy against the live page without placing bets")
    parser.add_argument("--live", action="store_true", help="run live auto-staking on the configured live page")
    parser.add_argument("--url", help="override browser.url for this run (useful for expiring iLOTBET links)")
    parser.add_argument("--site", choices=["ilotbet", "bcgame"], help="use a built-in site selector profile")
    args = parser.parse_args()
    settings = load_settings(Path(args.settings))
    if args.site:
        settings = replace(settings, site=args.site, browser=profile(args.site, settings.browser))
    if args.url:
        settings = replace(settings, browser=replace(settings.browser, url=args.url))
    if args.paper_trade:
        settings = replace(settings, dry_run=False, paper_trade=True)
    if args.live:
        settings = replace(settings, dry_run=False, paper_trade=False)
    if args.observe:
        observer = PlaywrightObserver(settings.browser)
        stop = threading.Event()
        try:
            observer.connect()
            observer.observe(stop.is_set, lambda snapshot: print(snapshot, flush=True))
        except KeyboardInterrupt:
            stop.set()
        finally:
            observer.close()
        return
    if args.paper_trade:
        # Keep the paper session isolated from a dashboard observer using the
        # same site profile; Chromium locks persistent profiles exclusively.
        paper_browser = replace(settings.browser,
                                user_data_dir=f"{settings.browser.user_data_dir}_paper")
        paper = PaperTradingController(settings, PlaywrightObserver(paper_browser), on_event=print)
        paper.start()
        try:
            while paper.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            paper.stop("Stopped by user")
            paper.close()
        return
    if args.live:
        adapter = PlaywrightAdapter(settings.browser)
        controller = BotController(settings, adapter, on_event=print)
        controller.start()
        try:
            while controller.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            controller.stop("Stopped by user")
            controller.close()
        return
    if not args.no_ui:
        run_dashboard(args.settings)
        return
    controller = BotController(settings, DryRunAdapter(results=[1.2, 2.0, 1.1], delay=0.01), on_event=print)
    controller.start()
    controller._thread.join(timeout=1.0)  # prototype CLI mode; dashboard uses explicit Stop


if __name__ == "__main__": main()
