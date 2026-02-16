
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface ChartCardProps {
    title: string;
    children: React.ReactNode;
    height?: string;
    loading?: boolean;
    className?: string;
}

export function ChartCard({ title, children, height = "h-[300px]", loading, className }: ChartCardProps) {
    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent className={`relative ${height}`}>
                {loading ? (
                    <Skeleton className="w-full h-full" />
                ) : (
                    children
                )}
            </CardContent>
        </Card>
    );
}
