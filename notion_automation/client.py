import logging
import time

import requests

from . import NOTION_VERSION

LOG = logging.getLogger(__name__)


class NotionAPIError(RuntimeError):
    pass


class NotionClient:
    def __init__(self, token, timeout=15, retries=3, session=None):
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def request(self, method, path, payload=None):
        url = f"https://api.notion.com{path}"
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(
                    method, url, headers=self.headers, json=payload, timeout=self.timeout
                )
            except requests.Timeout as exc:
                if attempt == self.retries:
                    raise NotionAPIError("Notion request timed out") from exc
                time.sleep(2 ** attempt)
                continue
            except requests.RequestException as exc:
                raise NotionAPIError(f"Notion request failed: {exc}") from exc

            if response.status_code == 429 and attempt < self.retries:
                wait = float(response.headers.get("Retry-After", 1))
                LOG.warning("Notion rate limit reached; retrying in %.1fs", wait)
                time.sleep(wait)
                continue
            if response.status_code >= 500 and attempt < self.retries:
                time.sleep(2 ** attempt)
                continue
            try:
                data = response.json()
            except ValueError as exc:
                raise NotionAPIError("Notion returned invalid JSON") from exc
            if not response.ok:
                message = data.get("message", "Unknown Notion API error") if isinstance(data, dict) else "Unknown Notion API error"
                raise NotionAPIError(f"HTTP {response.status_code}: {message}")
            return data
        raise NotionAPIError("Notion request failed after retries")

    def query_data_source(self, data_source_id, payload=None):
        base_payload = dict(payload or {})
        base_payload.setdefault("page_size", 100)
        results = []
        cursor = None
        while True:
            page_payload = dict(base_payload)
            if cursor:
                page_payload["start_cursor"] = cursor
            data = self.request("POST", f"/v1/data_sources/{data_source_id}/query", page_payload)
            batch = data.get("results")
            if not isinstance(batch, list):
                raise NotionAPIError("Notion response does not contain a valid results list")
            results.extend(batch)
            if not data.get("has_more"):
                return results
            cursor = data.get("next_cursor")
            if not cursor:
                raise NotionAPIError("Notion pagination response is missing next_cursor")

    def get_page(self, page_id):
        return self.request("GET", f"/v1/pages/{page_id}")

    def create_page(self, data_source_id, properties, icon=None):
        payload = {"parent": {"type": "data_source_id", "data_source_id": data_source_id}, "properties": properties}
        if icon:
            payload["icon"] = icon
        return self.request("POST", "/v1/pages", payload)

    def update_page(self, page_id, properties):
        return self.request("PATCH", f"/v1/pages/{page_id}", {"properties": properties})
