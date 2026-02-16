
import { useOpsStore } from "@/store/useOpsStore";
import { Check, X, RefreshCw } from "lucide-react";
import { GcpProjectSelector } from "./GcpProjectSelector";
import { Badge } from "@/components/ui/badge";

export function CloudStatusBar() {
    const { provider, cloudStatus, fetchCloudStatus } = useOpsStore();

    if (!cloudStatus) return null;

    const providers = ['gcp', 'aws', 'azure'] as const;

    return (
        <div className="flex items-center gap-2">
            {provider === 'gcp' && <GcpProjectSelector />}

            <div className="flex items-center gap-3 border rounded-full px-3 py-1 text-xs bg-muted/50">
                {providers.map((p) => {
                    const status = cloudStatus[p as keyof typeof cloudStatus];
                    const isReady = status?.installed && status?.authenticated;

                    return (
                        <div key={p} className="flex items-center gap-1">
                            {isReady ? (
                                <Check className="w-3 h-3 text-green-500" />
                            ) : (
                                <X className="w-3 h-3 text-red-500" />
                            )}
                            <span className={`font-semibold uppercase ${isReady ? 'text-green-500' : 'text-red-500'}`}>
                                {p}
                            </span>
                            {!isReady && (
                                <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4 leading-none">
                                    Unconfigured
                                </Badge>
                            )}
                        </div>
                    );
                })}
            </div>

            <button onClick={() => fetchCloudStatus()} className="text-muted-foreground hover:text-foreground">
                <RefreshCw className="w-3 h-3" />
            </button>
        </div>
    );
}
