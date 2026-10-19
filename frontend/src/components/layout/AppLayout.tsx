import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopNav } from './TopNav';

const ROUTE_TITLES: Record<string, string> = {
  '/': 'Operations Dashboard',
  '/blockchain': 'Blockchain Forensics Engine',
  '/investigations': 'Case Investigations',
  '/investigations/new': 'Initiate New Case',
  '/evidence': 'Evidence Explorer',
  '/settings': 'System Settings & Connectivity',
};

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const getPageTitle = () => {
    if (ROUTE_TITLES[location.pathname]) {
      return ROUTE_TITLES[location.pathname];
    }
    if (location.pathname.startsWith('/investigations/')) {
      return 'Investigation Forensic Record';
    }
    return 'Forensic Station';
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-text-primary">
      <Sidebar collapsed={collapsed} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopNav onToggleSidebar={() => setCollapsed((c) => !c)} title={getPageTitle()} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
