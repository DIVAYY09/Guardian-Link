import { Activity, Wifi } from 'lucide-react';

interface HeaderProps {
    isConnected: boolean;
}

export function Header({ isConnected }: HeaderProps) {
    return (
        <header className="flex items-center justify-between px-6 py-4 bg-medical-dark border-b border-gray-800">
            <div className="flex items-center gap-3">
                <div className="relative">
                    <Activity className="w-8 h-8 text-alert-red animate-pulse-fast" />
                    <div className="absolute inset-0 bg-alert-red blur-lg opacity-20 animate-pulse-fast"></div>
                </div>
                <h1 className="text-2xl font-bold tracking-wider text-white">
                    GUARDIAN<span className="text-alert-red">LINK</span>
                </h1>
            </div>

            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-900 border border-gray-800">
                <Wifi className={`w-4 h-4 ${isConnected ? 'text-success-green' : 'text-gray-500'}`} />
                <span className={`text-sm font-medium ${isConnected ? 'text-success-green' : 'text-gray-500'}`}>
                    {isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
                </span>
            </div>
        </header>
    );
}
