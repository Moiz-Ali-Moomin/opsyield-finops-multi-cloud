
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useOpsStore } from '@/store/useOpsStore';
import { ChartCard } from '../dashboard/ChartCard';
import { formatCurrency } from '@/lib/format';

export function ForecastChart() {
    const { data, loading } = useOpsStore();

    // Mock forecast data structure since we don't have the backend data structure confirmed
    const chartData = data?.forecast || [];

    return (
        <ChartCard title="Cost Forecast (Next 3 Months)" loading={loading}>
            <ResponsiveContainer width="100%" height={280} minWidth={0}>
                <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="month" className="text-xs" />
                    <YAxis className="text-xs" tickFormatter={(val) => `$${val}`} />
                    <Tooltip
                        formatter={(val: number | undefined) => val !== undefined ? formatCurrency(val) : ''}
                        contentStyle={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)' }}
                    />
                    <Legend />
                    <Bar dataKey="predicted_cost" name="Predicted" fill="#8884d8" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="confidence_low" name="Lower Bound" fill="#82ca9d" stackId="a" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="confidence_high" name="Upper Bound" fill="#ffc658" stackId="a" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </ChartCard>
    );
}
