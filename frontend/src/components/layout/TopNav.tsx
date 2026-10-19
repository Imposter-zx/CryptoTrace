import { Sun, Moon, Menu, Terminal, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useTheme } from '@/hooks/useTheme';

export interface TopNavProps {
  onToggleSidebar?: () => void;
  title?: string;
}

export function TopNav({ onToggleSidebar, title }: TopNavProps) {
  const { theme, toggle } = useTheme();

  return (
    <header className="h-14 border-b border-border/80 bg-background-secondary/90 backdrop-blur-xs px-4 flex items-center justify-between gap-4 shrink-0 z-10">
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
            className="text-text-muted hover:text-text-primary"
          >
            <Menu className="h-4 w-4" />
          </Button>
        )}
        <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
          <Terminal className="h-3.5 w-3.5 text-primary" />
          <span>CRYPTO_TRACE://</span>
          <span className="text-text-primary font-sans font-medium">{title || 'Dashboard'}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded border border-emerald-800/40 bg-emerald-950/20 text-accent-green text-[11px] font-mono">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>AIR_GAPPED_MODE</span>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          className="text-text-muted hover:text-text-primary"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}
