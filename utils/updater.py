import json
import ssl
import webbrowser
import certifi
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal
from utils import config


def _is_safe_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc == "github.com"


class UpdateChecker(QThread):
    result_ready = Signal(bool, str, str, str)

    def run(self):
        url: str = f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest"
        try:
            req = Request(url)
            req.add_header('User-Agent', f'{config.APP_NAME}')

            context = ssl.create_default_context(cafile=certifi.where())
            response = urlopen(req, timeout=10, context=context)

            with response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    latest_tag = data.get("tag_name", "").lstrip("v")
                    html_url = data.get("html_url", "")

                    if not _is_safe_url(html_url):
                        self.result_ready.emit(False, "", "", "Security warning: the URL is not from github.com")
                        return

                    current_version = config.APP_VERSION.lstrip("v")

                    if latest_tag != current_version and latest_tag:
                        self.result_ready.emit(True, latest_tag, html_url, "")
                    else:
                        self.result_ready.emit(False, latest_tag, "", "")
                else:
                    self.result_ready.emit(False, "", "", f"API Error: {response.status}")

        except Exception as e:
            self.result_ready.emit(False, "", "", str(e))


def open_download_page(url: str):
    if "github.com" in url and url.startswith("https://"):
        webbrowser.open(url)