"""Standalone privacy filters for the external recorder.

Intentionally kept independent of the diagnostics CLI import path; both tools
use equivalent best-effort filters. Review logs manually before sharing.
"""
import re


def scrub(text: str) -> str:
    text = re.sub(
        r"(?im)^\s*(set_pass_admin|password|passwd|token|api[_-]?key|auth[_-]?token)\s*(?:[:=]|\s)\s*\S+.*$",
        r"\1 <REDACTED>", text)
    text = re.sub(
        r"(?i)\b(?:[a-z]:\\Users\\|/Users/|/home/)[^\\/\s\"']+",
        "<USER_HOME>", text)
    text = re.sub(r"(?i)\b(?:steam[_ -]?id|steamid)\s*[:=]?\s*\d{8,20}",
                  "SteamID:<REDACTED>", text)
    text = re.sub(r"(?<!\d)7656119\d{10}(?!\d)", "<STEAM_ID>", text)
    text = re.sub(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
                  "<EMAIL>", text)
    text = re.sub(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?(?![\d.])",
                  "<IP_ADDRESS>", text)
    text = re.sub(r"(?i)\b(?:Bearer\s+)[A-Za-z0-9._~+/\-]{12,}",
                  "Bearer <REDACTED>", text)
    return text
