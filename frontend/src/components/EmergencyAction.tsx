import React from 'react';
import { Phone, ArrowRight, ShieldAlert } from 'lucide-react';
import clsx from 'clsx';

interface EmergencyActionProps {
    isVisible: boolean;
    onDispatch: () => void;
}

const EmergencyAction: React.FC<EmergencyActionProps> = ({ isVisible, onDispatch }) => {
    return (
        <div className={clsx(
            "fixed bottom-0 left-0 right-0 z-50 transition-transform duration-500 ease-out p-4",
            isVisible ? "translate-y-0" : "translate-y-full"
        )}>
            <div className="bg-red-600 rounded-3xl p-1 shadow-[0_-10px_40px_rgba(220,38,38,0.4)]">
                <div className="bg-gradient-to-b from-gray-900 to-black rounded-[20px] p-6 border border-white/10">
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <ShieldAlert className="w-5 h-5 text-red-500 animate-pulse" />
                                <h3 className="text-red-500 font-bold tracking-widest uppercase text-sm">Action Required</h3>
                            </div>
                            <h2 className="text-2xl font-bold text-white">Emergency Detected</h2>
                            <p className="text-white/60 text-sm mt-1">Mock SBAR generated. Dispatch recommended.</p>
                        </div>
                        <div className="w-12 h-12 rounded-full bg-red-600/20 flex items-center justify-center border border-red-500/30 animate-pulse text-red-500 font-bold">
                            !
                        </div>
                    </div>

                    <button
                        onClick={onDispatch}
                        className="w-full bg-white text-black font-bold py-4 rounded-xl flex items-center justify-center gap-2 active:scale-95 transition-transform"
                    >
                        <Phone className="w-5 h-5 fill-black" />
                        <span>Dispatch Emergency Services</span>
                        <ArrowRight className="w-5 h-5 ml-auto opacity-50" />
                    </button>

                    <button className="w-full mt-3 py-3 text-white/40 text-xs font-mono text-center hover:text-white transition-colors">
                        DISMISS ALERT (FALSIFIED)
                    </button>
                </div>
            </div>
        </div>
    );
};

export default EmergencyAction;
