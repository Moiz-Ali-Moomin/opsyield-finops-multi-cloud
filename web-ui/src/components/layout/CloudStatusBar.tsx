
import { useOpsStore } from "@/store/useOpsStore";

import { Check, X, RefreshCw } from "lucide-react";
import { GcpProjectSelector } from "./GcpProjectSelector";

export function CloudStatusBar() {
    const { provider, cloudStatus, fetchCloudStatus } = useOpsStore();

    if (!cloudStatus) return null;

    const currentStatus = cloudStatus[provider as keyof typeof cloudStatus];

    return (
        <div className="flex items-center gap-2">
            {provider === 'gcp' && <GcpProjectSelector />}

            <div className="flex items-center gap-2 border rounded-full px-3 py-1 text-xs bg-muted/50">
                <span className="font-semibold uppercase">{provider}</span>
                <div className="h-3 w-px bg-border" />
                <div className="flex items-center gap-1">
                    <span className={currentStatus?.installed ? "text-green-500" : "text-red-500"}>
                        CLI
                    </span>
                    {currentStatus?.installed ? <Check className="w-3 h-3 text-green-500" /> : <X className="w-3 h-3 text-red-500" />}
                </div>
                <div className="flex items-center gap-1">
                    <span className={currentStatus?.authenticated ? "text-green-500" : "text-red-500"}>
                        AUTH
                    </span>
                    {currentStatus?.authenticated ? <Check className="w-3 h-3 text-green-500" /> : <X className="w-3 h-3 text-red-500" />}
                </div>
            </div>
            <button onClick={() => fetchCloudStatus()} className="text-muted-foreground hover:text-foreground">
                <RefreshCw className="w-3 h-3" />
            </button>
        </div>
    );
}
