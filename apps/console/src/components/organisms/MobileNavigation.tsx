import { Home, Compass, FileText, User } from 'lucide-react';

interface MobileNavigationProps {
  activeTab: 'home' | 'map' | 'permits' | 'profile';
  setActiveTab: (tab: 'home' | 'map' | 'permits' | 'profile') => void;
}

export function MobileNavigation({ activeTab, setActiveTab }: MobileNavigationProps) {
  const tabs = [
    { id: 'home', label: 'Home', icon: <Home className="h-5 w-5" /> },
    { id: 'map', label: 'Map', icon: <Compass className="h-5 w-5" /> },
    { id: 'permits', label: 'Permits', icon: <FileText className="h-5 w-5" /> },
    { id: 'profile', label: 'Exposure', icon: <User className="h-5 w-5" /> },
  ] as const;

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-panel border-t border-line flex items-center justify-around z-40 select-none">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`flex flex-col items-center justify-center w-16 h-12 rounded cursor-pointer transition-colors ${
            activeTab === tab.id ? 'text-ink' : 'text-ink-dim hover:text-ink'
          }`}
          style={{ minWidth: '44px', minHeight: '44px' }}
        >
          {tab.icon}
          <span className="text-[9px] font-mono font-bold uppercase mt-0.5">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
