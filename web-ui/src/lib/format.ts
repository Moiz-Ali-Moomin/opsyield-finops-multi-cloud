
export const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null) return "$0.00";
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(value);
};

export const formatNumber = (value: number | undefined | null) => {
    if (value === undefined || value === null) return "0";
    return new Intl.NumberFormat('en-US').format(value);
};

export const formatPercentage = (value: number | undefined | null) => {
    if (value === undefined || value === null) return "0%";
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
    }).format(value / 100);
};
