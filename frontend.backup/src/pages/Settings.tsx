import { AppLayout } from "@/components/AppLayout";
import { Settings as SettingsIcon, Save } from "lucide-react";
import { useState } from "react";

export default function Settings() {
  const [weights, setWeights] = useState({
    swing: 50,
    intraday: 30,
    options: 20
  });

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <AppLayout>
      <div className="space-y-6 max-w-2xl">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <SettingsIcon className="h-8 w-8 text-primary" /> Risk OS Settings
          </h1>
          <p className="text-muted-foreground mt-2">Configure model weights and risk constraints.</p>
        </div>

        <div className="bg-card border border-border/50 rounded-xl p-6 space-y-6">
          <h3 className="font-semibold text-lg border-b border-border/40 pb-2">Capital Allocation Weights</h3>
          
          <div className="space-y-4">
            <div>
              <label className="flex justify-between text-sm mb-2">
                <span>Swing (Low Risk)</span>
                <span className="font-mono">{weights.swing}%</span>
              </label>
              <input type="range" min="0" max="100" value={weights.swing} onChange={e => setWeights({...weights, swing: parseInt(e.target.value)})} className="w-full accent-primary" />
            </div>
            
            <div>
              <label className="flex justify-between text-sm mb-2">
                <span>Intraday (Medium Risk)</span>
                <span className="font-mono">{weights.intraday}%</span>
              </label>
              <input type="range" min="0" max="100" value={weights.intraday} onChange={e => setWeights({...weights, intraday: parseInt(e.target.value)})} className="w-full accent-primary" />
            </div>

            <div>
              <label className="flex justify-between text-sm mb-2">
                <span>Options Alpha (High Risk)</span>
                <span className="font-mono">{weights.options}%</span>
              </label>
              <input type="range" min="0" max="100" value={weights.options} onChange={e => setWeights({...weights, options: parseInt(e.target.value)})} className="w-full accent-primary" />
            </div>
          </div>

          <div className="pt-4 flex items-center gap-4">
             <button onClick={handleSave} className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 transition-colors">
               <Save className="h-4 w-4" /> Save Configuration
             </button>
             {saved && <span className="text-sm text-green-500 font-medium">Settings saved to local environment!</span>}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
