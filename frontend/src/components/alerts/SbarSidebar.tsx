
import { useEffect, useState } from 'react';
import { FileText, Radio, ShieldAlert } from 'lucide-react';

interface SbarSidebarProps {
    data: string | null;
}

export function SbarSidebar({ data }: SbarSidebarProps) {
    const [displayText, setDisplayText] = useState('');
    // Use provided data as full text, or default placeholders if empty/null
    const fullText = data || "AWAITING DISPATCH DATA...\n\nMONITORING ACTIVE JOBS...";

    useEffect(() => {
        // Reset if no data
        if (!data && !displayText.startsWith("AWAITING")) {
            setDisplayText('');
        }

        let index = 0;
        // Don't clear text immediately on new data, acts as buffer, but for now simple reset is fine
        // setDisplayText(''); 

        const interval = setInterval(() => {
            setDisplayText(() => fullText.slice(0, index));
            index++;
            if (index > fullText.length) clearInterval(interval);
        }, 10); // Faster typewriter

        return () => clearInterval(interval);
    }, [fullText, data, displayText]); // Added displayText to dependencies to ensure the reset condition works correctly

    return (
        <div className="w-full md:w-96 bg-gray-900 border-l border-gray-800 flex flex-col h-full backdrop-blur-md bg-opacity-90">
            <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-md font-bold tracking-widest text-gray-100">
                    <FileText className="w-4 h-4 text-alert-red" />
                    DISPATCH LOG
                </h2>
                <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-success-green rounded-full animate-pulse"></span>
                    <span className="text-xs text-gray-500 font-mono">LIVE</span>
                </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-gray-300 leading-relaxed">
                {data ? (
                    <div className="whitespace-pre-wrap">{displayText}</div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600 space-y-4">
                        <Radio className="w-12 h-12 animate-pulse" />
                        <p>AWAITING DATA STREAM...</p>
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-gray-800 bg-gray-950">
                <div className="flex items-center gap-3 p-3 rounded bg-red-900/10 border border-red-900/30">
                    <ShieldAlert className="w-5 h-5 text-alert-red" />
                    <div>
                        <div className="text-xs text-gray-500 font-bold uppercase">Priority Level</div>
                        <div className="text-sm font-mono text-alert-red font-bold">MONITORING</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
