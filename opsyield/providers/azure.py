"""
Azure Provider — Production-grade cloud status detection.

Uses subprocess.run(shell=True) for Windows .cmd compatibility.
Authentication is determined by CLI exit code of `az account show`.
"""
import json
import logging
import os
import shutil
import subprocess
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..core.models import NormalizedCost

logger = logging.getLogger("opsyield-azure")


def _clean_env() -> dict:
    """Strip PAGER (breaks CLIs on Windows) and return env copy."""
    env = os.environ.copy()
    env.pop("PAGER", None)
    return env


def _run(cmd: str, timeout: int = 15) -> dict:
    """
    Run a CLI command synchronously with full debug capture.

    Returns {ok, stdout, stderr, returncode} — never raises.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,
            timeout=timeout,
            env=_clean_env(),
        )
        logger.info(
            f"[AZ] cmd={cmd!r} rc={result.returncode} "
            f"stdout={len(result.stdout)}B stderr={len(result.stderr)}B"
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"[AZ] Timeout: {cmd}")
        return {"ok": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        logger.error(f"[AZ] Exception: {e}")
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}


def _parse_json(raw: str):
    """Safely parse JSON, return None on failure."""
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None


class AzureProvider:
    def __init__(self, subscription_id: str = None):
        self.subscription_id = subscription_id

    def get_status_sync(self) -> Dict[str, Any]:
        """
        Synchronous status check — called via asyncio.to_thread().

        Authentication logic:
          1. shutil.which("az") → installed
          2. az account show --output json
             → exit code 0 → authenticated
             → Parse id (subscription), name, user from JSON stdout
        """
        status: Dict[str, Any] = {
            "installed": False,
            "authenticated": False,
            "subscriptions": [],
            "error": None,
            "debug": {},
        }

        # ── 1. Installation check ──
        az_path = shutil.which("az")
        if not az_path:
            status["error"] = "Azure CLI not found on PATH"
            status["debug"]["which"] = None
            return status
        status["installed"] = True
        status["debug"]["which"] = az_path

        # ── 2. Authentication check via az account show ──
        show_cmd = "az account show --output json"
        show = _run(show_cmd)
        status["debug"]["account_show"] = {
            "stdout": show["stdout"][:400],
            "stderr": show["stderr"][:300],
            "returncode": show["returncode"],
        }

        if show["ok"]:
            # CLI exit code 0 → authenticated
            status["authenticated"] = True
            parsed = _parse_json(show["stdout"])
            if isinstance(parsed, dict):
                sub_id = parsed.get("id", "")
                sub_name = parsed.get("name", "")
                user_info = parsed.get("user", {})

                if sub_id:
                    status["subscriptions"] = [{"id": sub_id, "name": sub_name}]
                    if not self.subscription_id:
                        self.subscription_id = sub_id

                status["debug"]["user"] = user_info.get("name", "")
                status["debug"]["tenant"] = parsed.get("tenantId", "")
        else:
            # Fallback: try az account list
            list_cmd = "az account list --output json"
            acct_list = _run(list_cmd)
            status["debug"]["account_list"] = {
                "returncode": acct_list["returncode"],
                "stdout_len": len(acct_list["stdout"]),
            }

            if acct_list["ok"]:
                parsed_list = _parse_json(acct_list["stdout"])
                if isinstance(parsed_list, list) and len(parsed_list) > 0:
                    status["authenticated"] = True
                    status["subscriptions"] = [
                        {"id": a.get("id", ""), "name": a.get("name", "")}
                        for a in parsed_list
                        if isinstance(a, dict) and a.get("state") == "Enabled"
                    ]
                    if status["subscriptions"] and not self.subscription_id:
                        self.subscription_id = status["subscriptions"][0]["id"]
                else:
                    status["error"] = "No Azure subscriptions. Run: az login"
            else:
                status["error"] = show["stderr"] or "Azure credentials not configured"

        # ── 3. Environment hints ──
        status["debug"]["env"] = {
            "AZURE_CONFIG_DIR": os.environ.get("AZURE_CONFIG_DIR", "(not set)"),
        }

        return status

    async def get_status(self) -> Dict[str, Any]:
        """Async wrapper — runs blocking subprocess in a thread."""
        import asyncio
        return await asyncio.to_thread(self.get_status_sync)

    async def get_costs(self, days: int = 30) -> List[NormalizedCost]:
        return []

    async def get_infrastructure(self) -> List:
        return []

    def get_resource_metadata(self, resource_id: str) -> dict:
        return {"id": resource_id, "provider": "azure"}
