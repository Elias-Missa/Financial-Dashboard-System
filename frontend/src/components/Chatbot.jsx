import { useState, useEffect, useRef } from 'react';
import { AlertCircle, RefreshCw, ExternalLink } from 'lucide-react';

const SHINY_URL = 'http://localhost:3838';

export default function Chatbot() {
  const [status, setStatus] = useState('loading');
  const iframeRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function probe() {
      try {
        await fetch(SHINY_URL, { mode: 'no-cors', cache: 'no-store' });
        if (!cancelled) setStatus('connected');
      } catch {
        if (!cancelled) setStatus('disconnected');
      }
    }

    probe();
    const id = setInterval(probe, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  function handleRetry() {
    setStatus('loading');
    setTimeout(() => {
      if (iframeRef.current) {
        iframeRef.current.src = SHINY_URL;
      }
      fetch(SHINY_URL, { mode: 'no-cors', cache: 'no-store' })
        .then(() => setStatus('connected'))
        .catch(() => setStatus('disconnected'));
    }, 300);
  }

  if (status === 'disconnected') {
    return (
      <div className="flex flex-col h-full">
        <div className="p-6 pb-0">
          <h2 className="text-2xl font-bold text-white">Market Cipher AI</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            AI-Powered Signal Generator &amp; Backtesting
          </p>
        </div>

        <div className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-md text-center space-y-4">
            <div className="mx-auto w-14 h-14 rounded-full bg-amber-500/10 flex items-center justify-center">
              <AlertCircle size={28} className="text-amber-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Shiny App Not Running</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              The R Shiny chatbot server is not reachable at{' '}
              <code className="text-xs bg-slate-800 px-1.5 py-0.5 rounded">localhost:3838</code>.
              Start it with:
            </p>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-left">
              <code className="text-xs text-emerald-400 whitespace-pre">
                cd chatbot{'\n'}Rscript run_app.R
              </code>
            </div>
            <button
              onClick={handleRetry}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
            >
              <RefreshCw size={14} />
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 pb-0">
        <div>
          <h2 className="text-xl font-bold text-white">Market Cipher AI</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            AI-Powered Signal Generator &amp; Backtesting
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs text-slate-500">
            <span className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
            {status === 'connected' ? 'Connected' : 'Connecting...'}
          </span>
          <a
            href={SHINY_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded bg-slate-800 text-slate-400 hover:bg-slate-700 transition-colors"
            title="Open in new tab"
          >
            <ExternalLink size={14} />
          </a>
          <button
            onClick={handleRetry}
            className="p-1.5 rounded bg-slate-800 text-slate-400 hover:bg-slate-700 transition-colors"
            title="Refresh"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 m-4 mt-2 rounded-xl overflow-hidden border border-slate-800">
        <iframe
          ref={iframeRef}
          src={SHINY_URL}
          title="Market Cipher AI"
          className="w-full h-full border-0"
          onLoad={() => setStatus('connected')}
        />
      </div>
    </div>
  );
}
