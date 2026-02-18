import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useOpsStore } from "@/store/useOpsStore";
import { formatCurrency, formatNumber } from "@/lib/format";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogDescription
} from "@/components/ui/dialog";
import { ResourceTable, Resource } from "./ResourceTable";
import { Table as TableIcon } from "lucide-react";

type HighCostResource = {
    id: string;
    name: string;
    class_type?: string;
    type?: string;
    cost_30d?: number;
    currency?: string;
};

type IdleResource = {
    id: string;
    name: string;
    type: string;
    class_type?: string;
    idle_score: number;
};

type WasteFinding = {
    name: string;
    reasons?: string[];
};

function isRecord(v: unknown): v is Record<string, unknown> {
    return typeof v === "object" && v !== null;
}

function asHighCostResources(arr: unknown[]): HighCostResource[] {
    return arr
        .filter(isRecord)
        .map((r) => ({
            id: String(r.id ?? ""),
            name: String(r.name ?? ""),
            class_type: typeof r.class_type === "string" ? r.class_type : undefined,
            type: typeof r.type === "string" ? r.type : undefined,
            cost_30d: typeof r.cost_30d === "number" ? r.cost_30d : undefined,
            currency: typeof r.currency === "string" ? r.currency : undefined,
        }))
        .filter((r) => r.id.length > 0 && r.name.length > 0);
}

function asIdleResources(arr: unknown[]): IdleResource[] {
    return arr
        .filter(isRecord)
        .map((r) => ({
            id: String(r.id ?? ""),
            name: String(r.name ?? ""),
            type: String(r.type ?? "unknown"),
            class_type: typeof r.class_type === "string" ? r.class_type : undefined,
            idle_score: typeof r.idle_score === "number" ? r.idle_score : 0,
        }))
        .filter((r) => r.id.length > 0 && r.name.length > 0);
}

function asWasteFindings(arr: unknown[]): WasteFinding[] {
    return arr
        .filter(isRecord)
        .map((w) => ({
            name: String(w.name ?? ""),
            reasons: Array.isArray(w.reasons) ? w.reasons.map(String) : undefined,
        }))
        .filter((w) => w.name.length > 0);
}

function sortEntriesDesc(obj: Record<string, number> | undefined) {
    return Object.entries(obj || {}).sort((a, b) => (b[1] || 0) - (a[1] || 0));
}

export function FinOpsInsights() {
    const { data, loading } = useOpsStore();

    if (loading || !data) return null;

    const resourceTypes = data.resource_types || {};
    const runningCount = data.running_count || 0;
    const costDrivers = data.cost_drivers || [];
    const highCost = asHighCostResources((data.high_cost_resources || []) as unknown[]);
    const idle = asIdleResources((data.idle_resources || []) as unknown[]);
    const waste = asWasteFindings((data.waste_findings || []) as unknown[]);
    const allResources = (data.resources || []) as unknown as Resource[];

    const topTypes = sortEntriesDesc(resourceTypes).slice(0, 8);
    const topDrivers = costDrivers.slice(0, 8);
    const topHighCost = highCost.slice(0, 6);
    const topIdle = idle.slice(0, 6);
    const topWaste = waste.slice(0, 6);

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="flex flex-col">
                <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between">
                        <span>Resource Inventory</span>
                        <Badge variant="secondary">
                            Running: {formatNumber(runningCount)}
                        </Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 flex-1">
                    <div className="text-sm text-muted-foreground">
                        Total discovered resources:{" "}
                        <span className="font-semibold text-foreground">
                            {formatNumber(data.summary?.resource_count)}
                        </span>
                    </div>

                    {topTypes.length > 0 ? (
                        <div className="space-y-2">
                            <div className="text-xs text-muted-foreground uppercase tracking-wide">
                                Top types
                            </div>
                            {topTypes.map(([t, c]) => (
                                <div key={t} className="flex items-center justify-between text-sm">
                                    <span className="font-mono text-xs truncate max-w-[70%]">{t}</span>
                                    <Badge variant="outline">{formatNumber(c)}</Badge>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-muted-foreground">
                            No resource inventory yet (provider may not support listing, or credentials missing).
                        </div>
                    )}
                </CardContent>
                <div className="p-4 pt-0 mt-auto">
                    <Dialog>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="w-full">
                                <TableIcon className="w-4 h-4 mr-2" />
                                View All Resources
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
                            <DialogHeader>
                                <DialogTitle>Resource Inventory</DialogTitle>
                                <DialogDescription>
                                    List of all discovered resources, their costs, and status.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="flex-1 overflow-auto min-h-0">
                                <ResourceTable resources={allResources} />
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
            </Card>

            <Card>
                <CardHeader className="pb-3">
                    <CardTitle>Top Cost Drivers</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {topDrivers.length > 0 ? (
                        <div className="space-y-2">
                            {topDrivers.map((d, idx) => (
                                <div key={`${d.service}-${idx}`} className="flex items-center justify-between text-sm">
                                    <span className="truncate max-w-[70%]">{d.service}</span>
                                    <span className="font-semibold">{formatCurrency(d.cost)}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-muted-foreground">
                            No cost driver data yet.
                        </div>
                    )}

                    {topHighCost.length > 0 && (
                        <div className="pt-2 border-t space-y-2">
                            <div className="text-xs text-muted-foreground uppercase tracking-wide">
                                Highest cost resources (30d)
                            </div>
                            {topHighCost.map((r, idx) => (
                                <div key={`${r.id}-${idx}`} className="flex items-center justify-between text-sm">
                                    <span className="truncate max-w-[70%]">
                                        {r.name}{" "}
                                        {r.class_type ? (
                                            <span className="text-xs text-muted-foreground font-mono">
                                                ({r.class_type})
                                            </span>
                                        ) : null}
                                    </span>
                                    <span className="font-semibold">{formatCurrency(r.cost_30d)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between">
                        <span>Waste & Idle</span>
                        <Badge variant={idle.length > 0 ? "default" : "secondary"}>
                            Idle: {formatNumber(idle.length)}
                        </Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {topIdle.length > 0 ? (
                        <div className="space-y-2">
                            <div className="text-xs text-muted-foreground uppercase tracking-wide">
                                Idle candidates
                            </div>
                            {topIdle.map((r, idx) => (
                                <div key={`${r.id}-${idx}`} className="flex items-center justify-between text-sm">
                                    <span className="truncate max-w-[70%]">
                                        {r.name}{" "}
                                        <span className="text-xs text-muted-foreground font-mono">
                                            {r.class_type || r.type}
                                        </span>
                                    </span>
                                    <Badge variant="outline">score {r.idle_score}</Badge>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-muted-foreground">
                            No idle candidates detected yet.
                        </div>
                    )}

                    {topWaste.length > 0 && (
                        <div className="pt-2 border-t space-y-2">
                            <div className="text-xs text-muted-foreground uppercase tracking-wide">
                                Waste findings
                            </div>
                            {topWaste.map((w, idx) => (
                                <div key={`${w.name}-${idx}`} className="text-sm">
                                    <div className="font-medium truncate">{w.name}</div>
                                    {Array.isArray(w.reasons) && w.reasons.length > 0 && (
                                        <div className="text-xs text-muted-foreground truncate">
                                            {w.reasons.join("; ")}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}

