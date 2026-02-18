from ..base import BaseCollector
import google.auth
import google.auth.transport.requests
from typing import Optional

class GCPBaseCollector(BaseCollector):
    def __init__(self, project_id: Optional[str] = None, region: str = "global"):
        super().__init__("gcp", region)
        self.project_id = project_id or self._resolve_project_id()
        self.credentials, self.project_id = google.auth.default()
        # If project_id was passed explicitly, use it, otherwise default() might have found it.
        if project_id:
            self.project_id = project_id

    def _resolve_project_id(self) -> str:
        # Minimal fallback if google.auth.default() didn't catch it
        # Real logic handled in __init__ via google.auth.default() usually
        return self.project_id or ""

    def _handle_gcp_error(self, operation: str, error: Exception):
        # Specific GCP error handling could go here
        self._handle_error(operation, error)
