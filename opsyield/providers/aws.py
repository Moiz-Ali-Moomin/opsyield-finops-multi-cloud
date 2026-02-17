"""
AWS Provider — Production-grade cloud status detection.

Uses subprocess.run(shell=True) for Windows .cmd compatibility.
Authentication is determined by CLI exit code of `aws sts get-caller-identity`.
"""
import json
import logging
import os
import shutil
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ..core.models import NormalizedCost, Resource

logger = logging.getLogger("opsyield-aws")


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
            f"[AWS] cmd={cmd!r} rc={result.returncode} "
            f"stdout={len(result.stdout)}B stderr={len(result.stderr)}B"
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"[AWS] Timeout: {cmd}")
        return {"ok": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        logger.error(f"[AWS] Exception: {e}")
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}


def _parse_json(raw: str):
    """Safely parse JSON, return None on failure."""
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None


class AWSProvider:
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        self.region = region
        self.profile = profile

    def get_status_sync(self) -> Dict[str, Any]:
        """
        Synchronous status check — called via asyncio.to_thread().

        Authentication logic:
          1. shutil.which("aws") → installed
          2. aws sts get-caller-identity --output json
             → exit code 0 → authenticated
             → Parse Account field from JSON stdout
        """
        status: Dict[str, Any] = {
            "installed": False,
            "authenticated": False,
            "account": None,
            "error": None,
            "debug": {},
        }

        # ── 1. Installation check ──
        aws_path = shutil.which("aws")
        if not aws_path:
            status["error"] = "AWS CLI not found on PATH"
            status["debug"]["which"] = None
            return status
        status["installed"] = True
        status["debug"]["which"] = aws_path

        # ── 2. Authentication check via STS ──
        sts_cmd = "aws sts get-caller-identity --output json"
        sts = _run(sts_cmd)
        status["debug"]["sts"] = {
            "stdout": sts["stdout"][:300],
            "stderr": sts["stderr"][:300],
            "returncode": sts["returncode"],
        }

        if sts["ok"]:
            # CLI exit code 0 → authenticated
            status["authenticated"] = True
            parsed = _parse_json(sts["stdout"])
            if isinstance(parsed, dict):
                status["account"] = parsed.get("Account")
                status["debug"]["arn"] = parsed.get("Arn", "")
        else:
            status["error"] = sts["stderr"] or "AWS credentials not configured"

        # ── 3. Environment hints ──
        status["debug"]["env"] = {
            "AWS_PROFILE": os.environ.get("AWS_PROFILE", "(not set)"),
            "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", "(not set)"),
            "AWS_ACCESS_KEY_ID": "***set***" if os.environ.get("AWS_ACCESS_KEY_ID") else "(not set)",
        }

        return status

    async def get_status(self) -> Dict[str, Any]:
        """Async wrapper — runs blocking subprocess in a thread."""
        import asyncio
        return await asyncio.to_thread(self.get_status_sync)

    async def get_costs(self, days: int = 30) -> List[NormalizedCost]:
        if not HAS_BOTO3:
            return []
        import asyncio
        return await asyncio.to_thread(self._sync_get_costs, days)

    def _sync_get_costs(self, days: int) -> List[NormalizedCost]:
        costs = []
        try:
            session = boto3.Session(
                profile_name=self.profile,
                region_name=self.region,
            ) if self.profile else boto3.Session(region_name=self.region)

            ce = session.client("ce")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            response = ce.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            for rbt in response.get("ResultsByTime", []):
                dt = datetime.strptime(rbt["TimePeriod"]["Start"], "%Y-%m-%d")
                for group in rbt.get("Groups", []):
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    if amount > 0.001:
                        costs.append(NormalizedCost(
                            provider="aws",
                            service=group["Keys"][0],
                            region=self.region,
                            resource_id="aggregated",
                            cost=round(amount, 4),
                            currency="USD",
                            timestamp=dt,
                            tags={},
                            environment="production",
                        ))
        except Exception as e:
            logger.error(f"AWS cost fetch failed: {e}")
        return costs

    async def get_infrastructure(self) -> List:
        if not HAS_BOTO3:
            return []

        import asyncio
        return await asyncio.to_thread(self._sync_get_infrastructure)

    def _sync_get_infrastructure(self) -> List[Resource]:
        """
        Minimal AWS inventory: EC2 instances.

        Returns Resource objects enriched with extra fields (via dataclass attrs):
          - state, class_type(instance_type), external_ip
        """
        resources: List[Resource] = []
        try:
            session = boto3.Session(
                profile_name=self.profile,
                region_name=self.region,
            ) if self.profile else boto3.Session(region_name=self.region)

            ec2 = session.client("ec2")
            paginator = ec2.get_paginator("describe_instances")

            for page in paginator.paginate():
                for reservation in page.get("Reservations", []):
                    for inst in reservation.get("Instances", []):
                        instance_id = inst.get("InstanceId", "")
                        instance_type = inst.get("InstanceType", "unknown")
                        state = (inst.get("State") or {}).get("Name", "unknown")
                        launch_time = inst.get("LaunchTime")
                        name_tag = ""
                        for t in inst.get("Tags", []) or []:
                            if t.get("Key") == "Name":
                                name_tag = t.get("Value") or ""
                                break

                        public_ip = inst.get("PublicIpAddress")

                        r = Resource(
                            id=instance_id,
                            name=name_tag or instance_id,
                            type="ec2_instance",
                            provider="aws",
                            region=self.region,
                            creation_date=launch_time,
                        )

                        # Extra fields (frontend allows [key: string]: any)
                        setattr(r, "state", state)
                        setattr(r, "class_type", instance_type)
                        setattr(r, "external_ip", public_ip)
                        resources.append(r)

        except Exception as e:
            logger.error(f"AWS infrastructure fetch failed: {e}")

        return resources

    def get_resource_metadata(self, resource_id: str) -> dict:
        return {"id": resource_id, "provider": "aws"}
