from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("aviator_bot.browser.session_launcher")


def clean_chromium_locks(profile_dir: Path) -> None:
    """Remove residual Chromium singleton locks that cause startup failures."""
    for lock_name in ("SingletonLock", "SingletonSocket", "SingletonCookie", "lockfile"):
        try:
            (profile_dir / lock_name).unlink(missing_ok=True)
        except Exception:
            pass


def kill_dangling_chrome() -> None:
    """Terminate stale chrome processes if locked."""
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            time.sleep(1.0)
        except Exception:
            pass


def launch_browser_session(user_data_dir: str, headless: bool = False) -> tuple[Any, Any, Any]:
    """Launch Playwright and return (playwright, context, page)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed; install requirements.txt") from exc

    if sys.platform == "win32":
        import asyncio
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass

    pw = sync_playwright().start()
    profile = Path(user_data_dir).expanduser().resolve()
    profile.mkdir(parents=True, exist_ok=True)
    clean_chromium_locks(profile)

    args = ["--no-first-run", "--no-default-browser-check", "--start-maximized"]

    try:
        context = pw.chromium.launch_persistent_context(
            str(profile),
            headless=headless,
            no_viewport=True,
            args=args,
        )
    except Exception as exc:
        if "ProcessSingleton" in str(exc) or "Lock file" in str(exc):
            logger.warning("Chromium profile locked, killing stale processes...")
            kill_dangling_chrome()
            clean_chromium_locks(profile)
            context = pw.chromium.launch_persistent_context(
                str(profile),
                headless=headless,
                no_viewport=True,
                args=args,
            )
        else:
            pw.stop()
            raise

    pages = context.pages
    if len(pages) > 1:
        for extra in pages[1:]:
            try:
                extra.close()
            except Exception:
                pass
    page = pages[0] if pages else context.new_page()
    try:
        page.bring_to_front()
    except Exception:
        pass

    return pw, context, page
