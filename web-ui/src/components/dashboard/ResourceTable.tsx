
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/format";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Search } from "lucide-react";

export type Resource = {
    id: string;
    name: string;
    type: string;
    class_type?: string;
    state?: string;
    cost_30d?: number;
    currency?: string;
    idle_score?: number;
    waste_reasons?: string[];
    region?: string;
};

interface ResourceTableProps {
    resources: Resource[];
}

export function ResourceTable({ resources }: ResourceTableProps) {
    const [filter, setFilter] = useState("");

    const filtered = resources.filter((r) =>
        r.name.toLowerCase().includes(filter.toLowerCase()) ||
        r.type.toLowerCase().includes(filter.toLowerCase()) ||
        (r.state && r.state.toLowerCase().includes(filter.toLowerCase()))
    );

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2">
                <Search className="w-4 h-4 text-muted-foreground" />
                <Input
                    placeholder="Filter resources..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="max-w-sm"
                />
                <div className="ml-auto text-sm text-muted-foreground">
                    Showing {filtered.length} of {resources.length} resources
                </div>
            </div>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>State</TableHead>
                            <TableHead className="text-right">Cost (30d)</TableHead>
                            <TableHead className="text-center">Idle Score</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filtered.length > 0 ? (
                            filtered.map((r) => (
                                <TableRow key={r.id}>
                                    <TableCell className="font-medium">
                                        <div className="flex flex-col">
                                            <span>{r.name}</span>
                                            <span className="text-xs text-muted-foreground font-mono">
                                                {r.region || "global"}
                                            </span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <span>{r.type}</span>
                                            {r.class_type && (
                                                <span className="text-xs text-muted-foreground font-mono">
                                                    {r.class_type}
                                                </span>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        {r.state ? (
                                            <Badge variant={r.state.toLowerCase() === "running" ? "default" : "secondary"}>
                                                {r.state}
                                            </Badge>
                                        ) : (
                                            <span className="text-muted-foreground">-</span>
                                        )}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        {r.cost_30d !== undefined
                                            ? formatCurrency(r.cost_30d)
                                            : "-"}
                                    </TableCell>
                                    <TableCell className="text-center">
                                        {r.idle_score !== undefined ? (
                                            <Badge variant={r.idle_score > 50 ? "destructive" : "outline"}>
                                                {r.idle_score}
                                            </Badge>
                                        ) : "-"}
                                    </TableCell>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    No resources found.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
