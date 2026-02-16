"""
GCP Provider — Production-grade cloud status + cost analysis.

Status: subprocess.run(shell=True) for Windows .cmd compatibility.
Costs:  google-cloud-bigquery billing export with asyncio.to_thread().
Authentication is determined by CLI exit code, NOT by project list.
"""
import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from ..core.models import NormalizedCost

logger = logging.getLogger("opsyield-gcp")


# ─── Lazy BigQuery imports (optional dependency) ───
try:
    from google.cloud import bigquery
    from google.api_core import exceptions as gcp_exceptions
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False
    bigquery = None
    gcp_exceptions = None


def _clean_env() -> dict:
    """Strip PAGER (breaks CLIs on Windows) and return env copy."""
    env = os.environ.copy()
    env.pop("PAGER", None)
    return env


def _run(cmd: str, timeout: int = 15) -> dict:
    """
    Run a CLI command synchronously with full debug capture.

    Returns {ok, stdout, stderr, returncode} for every call —
    never raises, never swallows output.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,             # Required: gcloud/aws/az are .cmd on Windows
            timeout=timeout,
            env=_clean_env(),
        )
        logger.info(
            f"[GCP] cmd={cmd!r} rc={result.returncode} "
            f"stdout={len(result.stdout)}B stderr={len(result.stderr)}B"
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"[GCP] Timeout: {cmd}")
        return {"ok": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        logger.error(f"[GCP] Exception: {e}")
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}


def _parse_json(raw: str):
    """Safely parse JSON, return None on failure."""
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None


class GCPProvider:
    """
    GCP cloud provider with status detection and BigQuery-based cost analysis.

    Cost retrieval requires:
      - Billing export to BigQuery enabled in GCP Console
      - IAM roles: BigQuery Data Viewer + BigQuery Job User
      - pip install google-cloud-bigquery
    """

    # BigQuery billing export dataset/table pattern
    _BQ_DATASET = "billing_export"
    _BQ_TABLE_PATTERN = "gcp_billing_export_v1_*"

    def __init__(self, project_id: str = None, credentials_path: str = None):
        self.project_id = project_id
        self.credentials_path = credentials_path

    # ─────────────────────────────────────────────────
    # Status Detection (unchanged from previous version)
    # ─────────────────────────────────────────────────

    def get_status_sync(self) -> Dict[str, Any]:
        """
        Synchronous status check — called via asyncio.to_thread().

        Authentication logic:
          1. shutil.which("gcloud") → installed
          2. gcloud auth list --filter=status:ACTIVE --format=value(account)
             → if exit code 0 AND stdout non-empty → authenticated
          3. Fallback: gcloud auth application-default print-access-token
             → if exit code 0 → authenticated (service account / ADC)
          4. gcloud projects list --format=json (optional, for project data)
        """
        status: Dict[str, Any] = {
            "installed": False,
            "authenticated": False,
            "projects": [],
            "error": None,
            "debug": {},
        }

        # ── 1. Installation check ──
        gcloud_path = shutil.which("gcloud")
        if not gcloud_path:
            status["error"] = "gcloud CLI not found on PATH"
            status["debug"]["which"] = None
            return status
        status["installed"] = True
        status["debug"]["which"] = gcloud_path

        # ── 2. Primary auth check ──
        auth_cmd = "gcloud auth list --filter=status:ACTIVE --format=value(account)"
        auth = _run(auth_cmd)
        status["debug"]["auth_list"] = {
            "stdout": auth["stdout"][:200],
            "stderr": auth["stderr"][:200],
            "returncode": auth["returncode"],
        }

        if auth["ok"] and auth["stdout"].strip():
            status["authenticated"] = True
            status["debug"]["active_account"] = auth["stdout"].strip().split("\n")[0]
        else:
            # ── 3. Fallback: Application Default Credentials ──
            adc_cmd = "gcloud auth application-default print-access-token"
            adc = _run(adc_cmd, timeout=10)
            status["debug"]["adc"] = {
                "returncode": adc["returncode"],
                "has_token": bool(adc["stdout"].strip()),
            }
            if adc["ok"] and adc["stdout"].strip():
                status["authenticated"] = True
                status["debug"]["auth_method"] = "application-default"
            else:
                status["error"] = auth["stderr"] or "No active gcloud account"

        # ── 4. Project list (informational, does NOT affect auth) ──
        if status["authenticated"]:
            proj = _run("gcloud projects list --format=json")
            status["debug"]["projects_list"] = {
                "returncode": proj["returncode"],
                "stdout_len": len(proj["stdout"]),
            }
            parsed = _parse_json(proj["stdout"])
            if isinstance(parsed, list):
                status["projects"] = [
                    {"id": p.get("projectId", ""), "name": p.get("name", "")}
                    for p in parsed
                    if p.get("lifecycleState") == "ACTIVE"
                ]

        return status

    async def get_status(self) -> Dict[str, Any]:
        """Async wrapper — runs blocking subprocess in a thread."""
        return await asyncio.to_thread(self.get_status_sync)

    # ─────────────────────────────────────────────────
    # Cost Analysis via BigQuery Billing Export
    # ─────────────────────────────────────────────────

    def _resolve_project_id(self) -> str:
        """
        Resolve the GCP project ID for BigQuery queries.

        Priority: constructor arg → gcloud config get-value project
        """
        if self.project_id:
            return self.project_id

        result = _run("gcloud config get-value project", timeout=10)
        if result["ok"] and result["stdout"].strip():
            self.project_id = result["stdout"].strip()
            return self.project_id

        raise ValueError(
            "No GCP project_id provided and 'gcloud config get-value project' "
            "returned empty. Set a project with: gcloud config set project <PROJECT_ID>"
        )

    def _build_cost_query(self, project_id: str, days: int) -> str:
        """
        Build the BigQuery SQL for billing export aggregation.

        Uses wildcard table pattern for standard billing export tables.
        Groups by service + currency, aggregates SUM(cost), ordered by cost DESC.
        """
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        table = f"`{project_id}.{self._BQ_DATASET}.{self._BQ_TABLE_PATTERN}`"

        return f"""
            SELECT
                service.description    AS service_name,
                currency               AS currency,
                SUM(cost)              AS total_cost,
                MIN(usage_start_time)  AS earliest_usage,
                MAX(usage_start_time)  AS latest_usage,
                COUNT(*)               AS line_items
            FROM {table}
            WHERE
                DATE(usage_start_time) >= '{start_date}'
                AND cost > 0
            GROUP BY
                service_name, currency
            ORDER BY
                total_cost DESC
        """

    def _get_costs_sync(self, days: int) -> List[NormalizedCost]:
        """
        Synchronous BigQuery cost retrieval — called via asyncio.to_thread().

        Raises ValueError with actionable messages on setup issues.
        Returns List[NormalizedCost] on success.
        """
        if not HAS_BIGQUERY:
            raise ValueError(
                "google-cloud-bigquery is not installed. "
                "Run: pip install google-cloud-bigquery"
            )

        try:
            project_id = self._resolve_project_id()
        except ValueError:
            raise

        query = self._build_cost_query(project_id, days)
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(
            f"[GCP Costs] Querying BigQuery — "
            f"project={project_id}, dataset={self._BQ_DATASET}, "
            f"start_date={start_date}, days={days}"
        )

        t0 = time.monotonic()
        try:
            client = bigquery.Client(project=project_id)
            query_job = client.query(query)
            rows = list(query_job.result())  # blocks until complete
            elapsed = time.monotonic() - t0

            logger.info(
                f"[GCP Costs] Query complete — "
                f"{len(rows)} service groups in {elapsed:.2f}s"
            )

            costs: List[NormalizedCost] = []
            now = datetime.utcnow()

            for row in rows:
                # BigQuery returns Decimal for SUM(cost) — convert to float safely
                raw_cost = row.get("total_cost", 0)
                cost_float = float(raw_cost) if isinstance(raw_cost, Decimal) else float(raw_cost or 0)

                if cost_float <= 0:
                    continue

                costs.append(NormalizedCost(
                    provider="gcp",
                    service=row.get("service_name", "Unknown"),
                    region="global",                    # billing export is region-agnostic at aggregate level
                    resource_id="aggregated",           # aggregated across resources
                    cost=round(cost_float, 4),
                    currency=row.get("currency", "USD"),
                    timestamp=now,
                    tags={},
                    environment="production",
                ))

            logger.info(
                f"[GCP Costs] Returning {len(costs)} cost entries, "
                f"total=${sum(c.cost for c in costs):,.2f}"
            )
            return costs

        except Exception as e:
            elapsed = time.monotonic() - t0
            error_type = type(e).__name__
            error_msg = str(e)

            # ── Structured error handling with actionable messages ──
            if gcp_exceptions and isinstance(e, gcp_exceptions.NotFound):
                raise ValueError(
                    f"Billing export not enabled. "
                    f"Expected table: {project_id}.{self._BQ_DATASET}.{self._BQ_TABLE_PATTERN}\n"
                    f"Please run: opsyield gcp setup\n"
                    f"Or enable manually: GCP Console → Billing → Billing export → BigQuery export"
                )
            elif gcp_exceptions and isinstance(e, gcp_exceptions.Forbidden):
                raise ValueError(
                    f"Permission denied accessing billing data. "
                    f"Required IAM roles: roles/bigquery.dataViewer, roles/bigquery.jobUser\n"
                    f"Grant access: gcloud projects add-iam-policy-binding {project_id} "
                    f"--member='user:<EMAIL>' --role='roles/bigquery.dataViewer'"
                )
            elif gcp_exceptions and isinstance(e, gcp_exceptions.BadRequest):
                logger.error(
                    f"[GCP Costs] Bad query ({elapsed:.2f}s): {error_msg}"
                )
                return []
            else:
                logger.error(
                    f"[GCP Costs] {error_type} after {elapsed:.2f}s: {error_msg}"
                )
                return []

    async def get_costs(self, days: int = 30) -> List[NormalizedCost]:
        """
        Retrieve GCP costs from BigQuery billing export.

        Runs the blocking BigQuery query in a thread pool via asyncio.to_thread()
        to avoid blocking the event loop.

        Prerequisites:
          - Billing export to BigQuery enabled in GCP Console
          - pip install google-cloud-bigquery
          - IAM: BigQuery Data Viewer + BigQuery Job User
        """
        return await asyncio.to_thread(self._get_costs_sync, days)

    # ─────────────────────────────────────────────────
    # Infrastructure (stub)
    # ─────────────────────────────────────────────────

    async def get_infrastructure(self) -> List:
        return []

    def get_resource_metadata(self, resource_id: str) -> dict:
        return {"id": resource_id, "provider": "gcp"}
