import { useEffect } from 'react';
import { useOpsStore } from '@/store/useOpsStore';
import { Button } from '@/components/ui/button';
import { Activity, RefreshCw } from 'lucide-react';
import { CloudStatusBar } from './CloudStatusBar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

export function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { provider, setProvider, loading, fetchData, isAggregate, setAggregateMode, fetchCloudStatus, cloudStatus, executiveMode, setExecutiveMode } = useOpsStore();

    useEffect(() => {
        fetchCloudStatus();
    }, []);

    const isProviderReady = (key: string) => {
        if (!cloudStatus) return false; // fast fail
        const status = cloudStatus[key as keyof typeof cloudStatus];
        return status?.installed && status?.authenticated;
    };

    return (
        <div className="min-h-screen bg-background flex flex-col font-sans text-foreground">
            {/* Top Navigation */}
            <header className="border-b bg-card sticky top-0 z-50">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                            <Activity className="text-white w-5 h-5" />
                        </div>
                        <span className="font-bold text-xl tracking-tight">OpsYield <span className="text-blue-500">Executive</span></span>
                        <CloudStatusBar />
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center space-x-2 mr-4">
                            <Switch
                                id="executive-mode"
                                checked={executiveMode}
                                onCheckedChange={setExecutiveMode}
                            />
                            <Label htmlFor="executive-mode" className="text-xs font-medium cursor-pointer">
                                {executiveMode ? 'Executive View' : 'Standard View'}
                            </Label>
                        </div>
                        <nav className="flex items-center gap-1 bg-secondary/50 p-1 rounded-lg">
                            <TooltipProvider>
                                {['gcp', 'aws', 'azure'].map((p) => {
                                    const ready = isProviderReady(p);
                                    return (
                                        <Tooltip key={p}>
                                            <TooltipTrigger asChild>
                                                <span>
                                                    <Button
                                                        variant={!isAggregate && provider === p ? 'default' : 'ghost'}
                                                        size="sm"
                                                        onClick={() => setProvider(p)}
                                                        disabled={!ready}
                                                        className={`text-xs ${!ready ? 'opacity-50 cursor-not-allowed' : ''}`}
                                                    >
                                                        {p.toUpperCase()}
                                                    </Button>
                                                </span>
                                            </TooltipTrigger>
                                            {!ready && (
                                                <TooltipContent>
                                                    <p>Not Configured</p>
                                                </TooltipContent>
                                            )}
                                        </Tooltip>
                                    );
                                })}
                            </TooltipProvider>

                            <div className="w-px h-4 bg-border mx-1" />
                            <Button
                                variant={isAggregate ? 'default' : 'ghost'}
                                size="sm"
                                onClick={() => setAggregateMode(true)}
                                className="text-xs font-bold"
                            >
                                AGGREGATE
                            </Button>
                        </nav>

                        <Button variant="outline" size="icon" onClick={() => fetchData()} disabled={loading}>
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        </Button>
                        <div className="w-8 h-8 rounded-full bg-slate-800 border flex items-center justify-center text-xs font-bold text-white">
                            CTO
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 container mx-auto px-6 py-8">
                {children}
            </main>
        </div>
    );
}
