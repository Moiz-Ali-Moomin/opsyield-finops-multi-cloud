

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { KPIGrid } from './components/dashboard/KPIGrid';
import { SpendTrendChart } from './components/charts/SpendTrendChart';
import { ForecastChart } from './components/charts/ForecastChart';
import { RiskHeatmap } from './components/dashboard/RiskHeatmap';
import { useOpsStore } from './store/useOpsStore';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

function Dashboard() {
  const { error, executiveMode } = useOpsStore();

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <KPIGrid />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SpendTrendChart />
        <ForecastChart />
      </div>

      {executiveMode && (
        <div className="grid grid-cols-1 gap-6">
          <RiskHeatmap />
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardLayout>
    </Router>
  );
}

export default App;
