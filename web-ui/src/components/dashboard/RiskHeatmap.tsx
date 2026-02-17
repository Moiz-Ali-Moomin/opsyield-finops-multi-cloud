
import { useOpsStore } from "@/store/useOpsStore";
import { ChartCard } from "./ChartCard";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export function RiskHeatmap() {
    const { data, loading } = useOpsStore();

    // Mock data based on data.resources
    const resources = data?.resources || [];

    const computeRisk = (r: any) => {
        const state = String(r.state || "").toLowerCase();
        const running = state.includes("running");
        const idleScore = typeof r.idle_score === "number" ? r.idle_score : 0;
        const cost = typeof r.cost_30d === "number" ? r.cost_30d : 0;
        const hasExternalIp = Boolean(r.external_ip);

        let risk = 0;
        if (running) risk += 20;
        if (!hasExternalIp) risk += 10;
        risk += Math.min(60, idleScore * 0.6);
        if (cost > 100) risk += 20;
        if (cost > 500) risk += 20;

        return Math.max(0, Math.min(100, risk));
    };

    // Group method for heatmap (just list for now as an example)
    const riskItems = resources.map(r => ({
        id: r.id,
        name: r.name,
        risk: computeRisk(r)
    })).sort((a, b) => b.risk - a.risk).slice(0, 20);

    return (
        <ChartCard title="Risk Heatmap (Top Technical Debt)" loading={loading} height="h-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
                <TooltipProvider>
                    {riskItems.map((item) => (
                        <Tooltip key={item.id}>
                            <TooltipTrigger asChild>
                                <div
                                    className={`h-16 rounded-md flex items-center justify-center text-xs font-bold p-2 text-center cursor-pointer transition-colors
                                        ${item.risk > 80 ? 'bg-destructive/80 text-destructive-foreground hover:bg-destructive' :
                                            item.risk > 50 ? 'bg-orange-500/80 text-white hover:bg-orange-500' :
                                                'bg-green-500/80 text-white hover:bg-green-500'}`}
                                >
                                    {item.name}
                                </div>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p className="font-bold">{item.name}</p>
                                <p>Risk Score: {item.risk.toFixed(0)}</p>
                            </TooltipContent>
                        </Tooltip>
                    ))}
                </TooltipProvider>
                {riskItems.length === 0 && (
                    <div className="col-span-full text-center text-muted-foreground py-8">
                        No active resources found to assess risk.
                    </div>
                )}
            </div>
        </ChartCard>
    );
}
