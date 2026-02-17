

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { KPIGrid } from './components/dashboard/KPIGrid';
import { SpendTrendChart } from './components/charts/SpendTrendChart';
import { ForecastChart } from './components/charts/ForecastChart';
import { RiskHeatmap } from './components/dashboard/RiskHeatmap';
import { FinOpsInsights } from './components/dashboard/FinOpsInsights';
import { SetupInstructions } from './components/onboarding/SetupInstructions';
import { useOpsStore } from './store/useOpsStore';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { InstructionsPage } from './pages/InstructionsPage';

function Dashboard() {
  const { error, executiveMode, provider, cloudStatus, isAggregate } = useOpsStore();

  // Check if the current provider is configured
  const currentStatus = cloudStatus?.[provider as keyof typeof cloudStatus];
  const isConfigured = currentStatus?.installed && currentStatus?.authenticated;

  // Show setup instructions if provider is not configured (and not in aggregate mode)
  if (cloudStatus && !isAggregate && !isConfigured) {
    return <SetupInstructions />;
  }

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

      <FinOpsInsights />

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
          <Route path="/instructions" element={<InstructionsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardLayout>
    </Router>
  );
}

export default App;
