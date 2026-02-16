

import { useOpsStore } from "@/store/useOpsStore";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function GcpProjectSelector() {
    const { cloudStatus, selectedProjectId, setSelectedProject } = useOpsStore();
    const projects = cloudStatus?.gcp?.projects || [];

    if (!projects.length) return null;

    return (
        <Select value={selectedProjectId || ""} onValueChange={setSelectedProject}>
            <SelectTrigger className="w-[200px] h-8 text-xs">
                <SelectValue placeholder="Select Project" />
            </SelectTrigger>
            <SelectContent>
                {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id} className="text-xs">
                        {p.name} ({p.id})
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}
