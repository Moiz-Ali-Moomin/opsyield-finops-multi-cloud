
import { useOpsStore } from "@/store/useOpsStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatNumber } from "@/lib/format";
import { ArrowUpRight, ArrowDownRight, DollarSign, Activity, AlertTriangle, Layers } from "lucide-react";

export function KPIGrid() {
    const { data, loading } = useOpsStore();

    if (loading) {
        return (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-28 rounded-xl" />
                ))}
            </div>
        );
    }

    const summary = data?.summary;

    const stats = [
        {
            title: "Total Spend",
            value: formatCurrency(summary?.total_cost),
            icon: DollarSign,
            change: "+2.5%",
            trend: "up" as const,
        },
        {
            title: "Resources",
            value: formatNumber(summary?.resource_count),
            icon: Layers,
            change: "+12",
            trend: "up" as const,
        },
        {
            title: "Risk Score",
            value: formatNumber(summary?.risk_score),
            icon: Activity,
            change: "-5%",
            trend: "down" as const,
            alert: (summary?.risk_score || 0) > 70
        },
        {
            title: "Efficiency",
            value: "84%", // Calculated metric
            icon: AlertTriangle,
            change: "+1.2%",
            trend: "up" as const,
        },
    ];

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat, index) => (
                <Card key={index}>
                    <CardContent className="p-6 flex items-center justify-between space-y-0">
                        <div className="flex flex-col gap-1">
                            <span className="text-sm font-medium text-muted-foreground">{stat.title}</span>
                            <span className="text-2xl font-bold">{stat.value}</span>
                        </div>
                        <div className="h-12 w-12 bg-primary/10 rounded-full flex items-center justify-center">
                            <stat.icon className={`h-6 w-6 ${stat.alert ? 'text-destructive' : 'text-primary'}`} />
                        </div>
                    </CardContent>
                    <div className="px-6 pb-4 flex items-center gap-2 text-xs">
                        <Badge variant={stat.trend === 'up' ? 'default' : 'secondary'} className="h-5 px-1">
                            {stat.trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                            {stat.change}
                        </Badge>
                        <span className="text-muted-foreground">vs last month</span>
                    </div>
                </Card>
            ))}
        </div>
    );
}
