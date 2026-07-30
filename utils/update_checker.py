from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from utils import app_config


class UpdateCheckError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    url: str


@dataclass(frozen=True)
class UpdateStatus:
    current_version: str
    latest_version: str
    release_url: str
    is_update_available: bool


def check_latest_release(current_version: str = app_config.APP_VERSION) -> UpdateStatus:
    latest_release = fetch_latest_release()
    return UpdateStatus(
        current_version=current_version,
        latest_version=latest_release.version,
        release_url=latest_release.url,
        is_update_available=is_newer_version(latest_release.version, current_version),
    )


def fetch_latest_release(timeout_ms: int = 10_000) -> ReleaseInfo:
    manager = QNetworkAccessManager()
    request = QNetworkRequest(QUrl(app_config.LATEST_RELEASE_API_URL))
    request.setRawHeader(b"Accept", b"application/vnd.github+json")
    request.setRawHeader(b"User-Agent", f"Tilf/{app_config.APP_VERSION}".encode("utf-8"))

    reply = manager.get(request)
    event_loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(event_loop.quit)
    reply.finished.connect(event_loop.quit)
    timeout.start(timeout_ms)
    event_loop.exec()

    if not timeout.isActive():
        reply.abort()
        raise UpdateCheckError("request timed out")

    timeout.stop()
    try:
        if reply.error() != QNetworkReply.NetworkError.NoError:
            raise UpdateCheckError(reply.errorString())

        raw_payload = cast(bytes, reply.readAll().data())
        payload = json.loads(raw_payload.decode("utf-8"))
        tag_name = payload.get("tag_name")
        release_url = payload.get("html_url") or app_config.RELEASES_URL
        if not isinstance(tag_name, str):
            raise UpdateCheckError("latest release response does not include a tag name")
        if not isinstance(release_url, str):
            raise UpdateCheckError("latest release response does not include a release URL")

        return ReleaseInfo(version=tag_name.lstrip("vV"), url=release_url)
    except json.JSONDecodeError as error:
        raise UpdateCheckError(str(error)) from error
    finally:
        reply.deleteLater()
        manager.deleteLater()


def is_newer_version(candidate: str, current: str) -> bool:
    return parse_version(candidate) > parse_version(current)


def parse_version(version: str) -> tuple[int, int, int]:
    numeric_parts: list[int] = []
    for part in version.lstrip("vV").split("."):
        digits = ""
        for character in part:
            if not character.isdigit():
                break
            digits += character
        numeric_parts.append(int(digits or "0"))

    while len(numeric_parts) < 3:
        numeric_parts.append(0)

    major, minor, patch = numeric_parts[:3]
    return major, minor, patch
