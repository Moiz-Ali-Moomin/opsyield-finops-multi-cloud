
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useOpsStore } from '@/store/useOpsStore';
import { ChartCard } from '../dashboard/ChartCard';
import { formatCurrency } from '@/lib/format';

export function SpendTrendChart() {
    const { data, loading } = useOpsStore();

    return (
        <ChartCard title="Spend Trend (30 Days)" loading={loading}>
            <ResponsiveContainer width="100%" height={280} minWidth={0}>
                <AreaChart data={data?.trends || []}>
                    <defs>
                        <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" tickFormatter={(val) => `$${val}`} />
                    <Tooltip
                        formatter={(val: number | undefined) => val !== undefined ? formatCurrency(val) : ''}
                        contentStyle={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)' }}
                    />
                    <Area
                        type="monotone"
                        dataKey="amount"
                        stroke="#3b82f6"
                        fillOpacity={1}
                        fill="url(#colorCost)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </ChartCard>
    );
}
