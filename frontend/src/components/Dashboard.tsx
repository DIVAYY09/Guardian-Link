import React, { useState } from 'react';
import CameraView from './CameraView';
import DispatcherLog from './DispatcherLog';
import EmergencyAction from './EmergencyAction';
import { Activity, Radio } from 'lucide-react';

interface SBAR {
    situation: string;
    background: string;
    assessment: string;
    recommendation: string;
    timestamp?: string;
}

const Dashboard: React.FC = () => {
    const [isEmergency, setIsEmergency] = useState(false);
    const [logs, setLogs] = useState<SBAR[]>([]);
    const [isSimulationMode, setIsSimulationMode] = useState(false);

    const handleEmergencyTrigger = (data: any) => {
        setIsEmergency(true);
        // If data contains SBAR, add it to logs
        if (data.sbar) {
            setLogs(prev => [data.sbar, ...prev]);
        } else if (isSimulationMode) {
            // Mock SBAR for simulation
            const mockSBAR: SBAR = {
                timestamp: new Date().toLocaleTimeString(),
                situation: "Sign language gesture 'HELP' detected with 98% confidence.",
                background: "User monitoring session active for 2 hours. No prior alerts.",
                assessment: "Immediate distress signal confirmed visually.",
                recommendation: "Dispatch paramedical unit to registered location immediately."
            };
            // Avoid duplicate logs if triggering continuously
            setLogs(prev => {
                const last = prev[0];
                if (last && last.situation === mockSBAR.situation && (new Date().getTime() - new Date().getTime()) < 5000) return prev;
                return [mockSBAR, ...prev];
            });
        }
    };

    const handleDispatch = () => {
        alert("Services Dispatched! (Mock functionality)");
        setIsEmergency(false);
        setIsSimulationMode(false);
    };

    return (
        <div className="min-h-screen bg-black text-white flex flex-col font-sans overflow-hidden">
            {/* Status Bar */}
            <header className="h-14 flex items-center justify-between px-6 border-b border-white/10 bg-black/80 backdrop-blur-md z-40">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                    <span className="font-bold tracking-wide text-sm">AI GUARDIAN</span>
                </div>
                <div className="flex items-center gap-4">
                    {/* Simulation Toggle */}
                    <button
                        onClick={() => setIsSimulationMode(!isSimulationMode)}
                        className={`text-xs border px-2 py-1 rounded transition-colors ${isSimulationMode ? 'bg-white text-black border-white' : 'border-white/20 text-white/50 hover:text-white'}`}
                    >
                        {isSimulationMode ? 'STOP SIMULATION' : 'TEST EMERGENCY'}
                    </button>

                    <div className="flex items-center gap-1.5 text-green-400 bg-green-400/10 px-2 py-0.5 rounded text-xs font-medium border border-green-400/20">
                        <Activity className="w-3 h-3" />
                        <span>ACTIVE</span>
                    </div>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 relative flex flex-col p-4 gap-4 overflow-hidden">
                {/* Camera Section (Top/Center) */}
                <div className="flex-none transition-[height] duration-500 ease-in-out" style={{ height: isEmergency ? '45%' : '60%' }}>
                    <div className="h-full w-full max-w-2xl mx-auto flex flex-col">
                        <CameraView
                            onEmergencyTrigger={handleEmergencyTrigger}
                            isSimulationMode={isSimulationMode}
                        />
                        {/* Signal Label */}
                        <div className="mt-4 flex justify-center">
                            <div className="flex items-center gap-2 text-white/40 text-xs tracking-[0.2em] font-light uppercase">
                                <Radio className="w-3 h-3" />
                                <span>Live Visual Feed Analysis</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Dispatcher Log (Bottom) */}
                <div className="flex-1 min-h-0 w-full max-w-2xl mx-auto">
                    <DispatcherLog logs={logs} />
                </div>
            </main>

            {/* Emergency Actions */}
            <EmergencyAction isVisible={isEmergency} onDispatch={handleDispatch} />
        </div>
    );
};

export default Dashboard;
