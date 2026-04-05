import { useState } from 'react';
import { useOpsStore, DateMode } from '@/store/useOpsStore';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon } from 'lucide-react';

const PRESETS: { label: string; mode: Exclude<DateMode, 'custom'> }[] = [
    { label: '30D', mode: '30d' },
    { label: '60D', mode: '60d' },
    { label: '90D', mode: '90d' },
];

export function DateRangePicker() {
    const { dateMode, customStart, customEnd, days, setDateMode, setCustomDateRange } = useOpsStore();
    const [open, setOpen] = useState(false);
    const [localStart, setLocalStart] = useState<string>(customStart ?? '');
    const [localEnd, setLocalEnd] = useState<string>(customEnd ?? '');

    const label = dateMode === 'custom' && customStart && customEnd
        ? `${customStart} → ${customEnd}`
        : `${days}D`;

    function applyCustom() {
        if (localStart && localEnd && localEnd >= localStart) {
            setCustomDateRange(localStart, localEnd);
            setOpen(false);
        }
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs font-medium">
                    <CalendarIcon className="h-3.5 w-3.5" />
                    {label}
                </Button>
            </PopoverTrigger>

            <PopoverContent align="end" className="w-72 p-3">
                {/* Preset buttons */}
                <div className="flex gap-2 mb-3">
                    {PRESETS.map(({ label: l, mode }) => (
                        <Button
                            key={mode}
                            variant={dateMode === mode ? 'default' : 'outline'}
                            size="sm"
                            className="flex-1 h-8 text-xs"
                            onClick={() => {
                                setDateMode(mode);
                                setOpen(false);
                            }}
                        >
                            {l}
                        </Button>
                    ))}
                    <Button
                        variant={dateMode === 'custom' ? 'default' : 'outline'}
                        size="sm"
                        className="flex-1 h-8 text-xs"
                        onClick={() => setDateMode('custom')}
                    >
                        Custom
                    </Button>
                </div>

                {/* Custom date inputs — only shown when Custom is selected */}
                {dateMode === 'custom' && (
                    <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                                <label className="text-xs text-muted-foreground">From</label>
                                <input
                                    type="date"
                                    value={localStart}
                                    max={localEnd || undefined}
                                    onChange={(e) => setLocalStart(e.target.value)}
                                    className="w-full h-8 rounded-md border border-input bg-background px-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs text-muted-foreground">To</label>
                                <input
                                    type="date"
                                    value={localEnd}
                                    min={localStart || undefined}
                                    onChange={(e) => setLocalEnd(e.target.value)}
                                    className="w-full h-8 rounded-md border border-input bg-background px-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                                />
                            </div>
                        </div>
                        <Button
                            size="sm"
                            className="w-full h-8 text-xs"
                            disabled={!localStart || !localEnd || localEnd < localStart}
                            onClick={applyCustom}
                        >
                            Apply
                        </Button>
                    </div>
                )}
            </PopoverContent>
        </Popover>
    );
}
