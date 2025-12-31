import { useEffect, useState } from 'react';
import { PhoneCall, AlertTriangle } from 'lucide-react';

interface EmergencyModalProps {
    isOpen: boolean;
    onCancel: () => void;
}

export function EmergencyModal({ isOpen, onCancel }: EmergencyModalProps) {
    const [countdown, setCountdown] = useState(5);

    useEffect(() => {
        if (!isOpen) {
            setCountdown(5);
            return;
        }

        if (countdown > 0) {
            const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [isOpen, countdown]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="w-full max-w-md p-8 bg-gray-900 border-2 border-alert-red rounded-xl shadow-[0_0_50px_rgba(255,59,48,0.5)] text-center relative overflow-hidden">
                {/* Background Pulse */}
                <div className="absolute inset-0 bg-alert-red opacity-10 animate-pulse-fast"></div>

                <div className="relative z-10">
                    <div className="w-20 h-20 bg-alert-red rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
                        <PhoneCall className="w-10 h-10 text-white" />
                    </div>

                    <h2 className="text-3xl font-bold text-white mb-2 tracking-widest">EMERGENCY DETECTED</h2>
                    <p className="text-gray-400 mb-8">CONTACTING EMERGENCY SERVICES IN</p>

                    <div className="text-8xl font-bold text-alert-red mb-8 font-mono">
                        {countdown}
                    </div>

                    <button
                        onClick={onCancel}
                        className="w-full py-4 bg-gray-800 hover:bg-gray-700 text-white font-bold rounded-lg border border-gray-600 transition-colors flex items-center justify-center gap-2"
                    >
                        <AlertTriangle className="w-5 h-5" />
                        CANCEL DISPATCH
                    </button>
                </div>
            </div>
        </div>
    );
}
