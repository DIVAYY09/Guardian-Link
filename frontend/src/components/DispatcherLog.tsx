import React from 'react';
import { FileText, Clock, ShieldCheck } from 'lucide-react';

interface SBAR {
    situation: string;
    background: string;
    assessment: string;
    recommendation: string;
    timestamp?: string;
}

interface DispatcherLogProps {
    logs: SBAR[];
}

const DispatcherLog: React.FC<DispatcherLogProps> = ({ logs }) => {
    return (
        <div className="w-full h-full flex flex-col bg-gray-900/50 backdrop-blur-xl border-t border-white/10 rounded-t-3xl p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                        <FileText className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-white font-bold text-lg">Dispatcher Log</h3>
                        <p className="text-white/40 text-xs">Live AI Transcription</p>
                    </div>
                </div>
                <div className="bg-green-500/10 border border-green-500/20 px-3 py-1 rounded-full flex items-center gap-1.5">
                    <ShieldCheck className="w-3 h-3 text-green-400" />
                    <span className="text-green-400 text-[10px] font-bold tracking-wider uppercase">Secure</span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                {logs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-white/20 gap-2">
                        <Clock className="w-8 h-8 opacity-50" />
                        <p className="text-sm">Waiting for emergency events...</p>
                    </div>
                ) : (
                    logs.map((log, index) => (
                        <div key={index} className="bg-white/5 border border-white/5 rounded-2xl p-4 space-y-3">
                            <div className="flex items-center justify-between border-b border-white/5 pb-2">
                                <span className="text-xs font-mono text-blue-400">REPORT #{1000 + index}</span>
                                <span className="text-xs text-white/30">{log.timestamp || new Date().toLocaleTimeString()}</span>
                            </div>
                            <div className="space-y-2 text-sm text-gray-300">
                                <div><strong className="text-white/60 text-xs uppercase tracking-wide">Situation:</strong> <p>{log.situation}</p></div>
                                <div><strong className="text-white/60 text-xs uppercase tracking-wide">Background:</strong> <p>{log.background}</p></div>
                                <div><strong className="text-white/60 text-xs uppercase tracking-wide">Assessment:</strong> <p>{log.assessment}</p></div>
                                <div><strong className="text-white/60 text-xs uppercase tracking-wide">Recommendation:</strong> <p className="text-blue-300 font-medium">{log.recommendation}</p></div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default DispatcherLog;
