import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { InvestigationsPage } from '@/pages/InvestigationsPage';
import { NewInvestigationPage } from '@/pages/NewInvestigationPage';
import { InvestigationDetailPage } from '@/pages/InvestigationDetailPage';
import { EvidenceExplorerPage } from '@/pages/EvidenceExplorerPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { BlockchainInvestigationPage } from '@/pages/BlockchainInvestigationPage';
import { useTheme } from '@/hooks/useTheme';

export default function App() {
  // Initialize theme on application mount
  useTheme();

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/blockchain" element={<BlockchainInvestigationPage />} />
        <Route path="/investigations" element={<InvestigationsPage />} />
        <Route path="/investigations/new" element={<NewInvestigationPage />} />
        <Route path="/investigations/:id" element={<InvestigationDetailPage />} />
        <Route path="/evidence" element={<EvidenceExplorerPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
