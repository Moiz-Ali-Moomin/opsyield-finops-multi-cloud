from datetime import datetime, timezone


class WasteDetector:

    MAX_RUNTIME_DAYS = 7

    def detect(self, resources):

        waste = []
        now = datetime.now(timezone.utc)

        for r in resources:

            reasons = []

            if not r.get("external_ip"):
                reasons.append("No external IP attached")

            created_at = r.get("created_at")
            if created_at:
                days_running = (now - created_at).days
                if days_running > self.MAX_RUNTIME_DAYS:
                    reasons.append(
                        f"Running for {days_running} days"
                    )

            if reasons:
                waste.append({
                    "name": r["name"],
                    "type": r["type"],
                    "reasons": reasons
                })

        return waste
