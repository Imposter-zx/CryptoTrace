import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderSearch,
  FilePlus2,
  Database,
  Settings,
  ShieldAlert,
  Layers,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/blockchain', label: 'Blockchain Forensics', icon: Layers },
  { to: '/investigations', label: 'Investigations', icon: FolderSearch, end: true },
  { to: '/investigations/new', label: 'New Case', icon: FilePlus2 },
  { to: '/evidence', label: 'Evidence Explorer', icon: Database },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export interface SidebarProps {
  collapsed?: boolean;
}

export function Sidebar({ collapsed = false }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-background-secondary border-r border-border transition-all duration-200 select-none z-20 shrink-0',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-border/80 h-14">
        <div className="rounded p-1 bg-cyan-950/60 border border-cyan-800/50 text-primary">
          <ShieldAlert className="h-5 w-5 shrink-0" />
        </div>
        {!collapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold tracking-tight text-text-primary leading-tight font-mono">
              CryptoTrace<span className="text-primary font-sans font-bold">.AI</span>
            </span>
            <span className="text-[10px] uppercase font-mono tracking-wider text-text-muted">Forensic Node</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto" aria-label="Main Navigation">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-medium transition-colors',
                isActive
                  ? 'bg-surface text-primary border border-primary/30 shadow-xs'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface/50 border border-transparent'
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer Info */}
      {!collapsed && (
        <div className="p-3 border-t border-border/80 bg-background/50 text-[11px] text-text-muted space-y-1 font-mono">
          <div className="flex justify-between">
            <span>VERSION</span>
            <span className="text-text-secondary">v0.1.0-alpha</span>
          </div>
          <div className="flex justify-between">
            <span>SECURITY</span>
            <span className="text-accent-green">LOCAL-FIRST</span>
          </div>
        </div>
      )}
    </aside>
  );
}
