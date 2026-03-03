import { useState } from 'react';
import { LayoutDashboard, FlaskConical, MessageCircle } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Backtest from './components/Backtest';
import Chatbot from './components/Chatbot';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'backtest', label: 'Backtest', icon: FlaskConical },
  { id: 'chatbot', label: 'Chatbot', icon: MessageCircle },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-5 border-b border-slate-800">
          <h1 className="text-lg font-semibold tracking-tight text-white">
            Financial Dashboard
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">S&P 500 ML Predictor</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === id
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <p className="text-[10px] text-slate-600 text-center">
            Ridge Regression &middot; 21-Day Horizon
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-slate-950">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'backtest' && <Backtest />}
        {activeTab === 'chatbot' && <Chatbot />}
      </main>
    </div>
  );
}
