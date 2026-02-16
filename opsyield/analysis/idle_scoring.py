class IdleScorer:

    def calculate_score(self, resource, cpu_avg=None):

        score = 0

        # No external IP
        if not resource.get("external_ip"):
            score += 30

        # Low CPU
        if cpu_avg is not None and cpu_avg < 0.05:
            score += 40

        # Long running
        if resource.get("days_running", 0) > 7:
            score += 30

        return score
