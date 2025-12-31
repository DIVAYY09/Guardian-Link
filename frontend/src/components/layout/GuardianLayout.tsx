import React from 'react';
import { Header } from './Header';

interface GuardianLayoutProps {
    children: React.ReactNode;
    isConnected: boolean;
    emergencyTriggered: boolean;
}

export function GuardianLayout({ children, isConnected, emergencyTriggered }: GuardianLayoutProps) {
    return (
        <div className={`min-h-screen bg-medical-dark text-white flex flex-col overflow-hidden transition-all duration-500 ${emergencyTriggered ? 'ring-8 ring-inset ring-alert-red' : ''}`}>
            <div className={`${emergencyTriggered ? 'animate-pulse' : ''} absolute inset-0 pointer-events-none bg-alert-red opacity-[0.02] mix-blend-overlay`}></div>

            <Header isConnected={isConnected} />

            <main className="flex-1 flex flex-col md:flex-row gap-6 p-6 overflow-hidden relative z-10">
                {children}
            </main>
        </div>
    );
}
