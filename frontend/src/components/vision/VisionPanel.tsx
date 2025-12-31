import { useRef, useEffect, useState } from 'react';
import { Scan, AlertCircle } from 'lucide-react';

interface VisionPanelProps {
    onResults: (data: any) => void;
    isConnected: boolean;
    setIsConnected: (status: boolean) => void;
    setEmergencyTriggered: (status: boolean) => void;
}

export function VisionPanel({ onResults, setIsConnected, setEmergencyTriggered }: VisionPanelProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [caption, setCaption] = useState<string>("Initializing scanning protocols...");

    // Initialize Camera
    useEffect(() => {
        async function setupCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480, facingMode: 'environment' }
                });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
            } catch (err) {
                console.error("Camera Access Error:", err);
                setCaption("CAMERA CONNECTION FAILED");
            }
        }
        setupCamera();
    }, []);

    // WebSocket Logic
    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8005/ws/stream');
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('Connected to Vision Server');
            setIsConnected(true);
            setCaption("System Online. Scanning sector...");
        };

        ws.onclose = () => {
            console.log('Disconnected from Vision Server');
            setIsConnected(false);
            setCaption("CONNECTION LOST - RECONNECTING...");
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onResults(data);

            if (data.status === "fallback") {
                setCaption(`⚠️ SYSTEM ALERT: ${data.caption}`);
            } else {
                setCaption(`ANALYSIS: ${data.caption ? data.caption.toUpperCase() : "SCANNING..."}`);
            }

            if (data.status === "alert") {
                setEmergencyTriggered(true);
            }
        };

        return () => {
            ws.close();
        };
    }, [setIsConnected, onResults, setEmergencyTriggered]);

    // Frame Transmission Loop
    useEffect(() => {
        const interval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN && videoRef.current && canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                if (ctx) {
                    ctx.drawImage(videoRef.current, 0, 0, 640, 480);
                    const base64 = canvasRef.current.toDataURL('image/jpeg', 0.8);
                    // Send plain base64 without prefix if backend expects it, or full data URL
                    // Backend code seemed to handle "split(',')", so sending full data URL is safe.
                    wsRef.current.send(base64);
                }
            }
        }, 200); // 5 FPS (200ms interval) to allow Azure breathing room

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex-1 min-h-[400px] flex flex-col relative bg-black/40 border border-gray-800 rounded-lg overflow-hidden backdrop-blur-sm">
            {/* Camera Feed */}
            <div className="relative flex-1 flex items-center justify-center overflow-hidden">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover opacity-80"
                />
                <canvas ref={canvasRef} width="640" height="480" className="hidden" />

                {/* Scanning Overlay */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="w-full h-1 bg-alert-red/50 shadow-[0_0_15px_rgba(255,59,48,0.8)] animate-scan absolute top-0"></div>
                    <div className="absolute inset-0 border-2 border-white/10 m-4 rounded-lg"></div>

                    {/* Target Reticle */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 border border-white/20 rounded-full flex items-center justify-center">
                        <Scan className="w-8 h-8 text-white/40 animate-pulse" />
                    </div>
                </div>
            </div>

            {/* Ticker Footer */}
            <div className="absolute bottom-0 left-0 right-0 h-10 bg-black/80 border-t border-gray-800 flex items-center px-4 overflow-hidden">
                <AlertCircle className="w-4 h-4 text-alert-red mr-3 animate-pulse" />
                <div className="overflow-hidden whitespace-nowrap w-full">
                    <div className="inline-block animate-marquee pl-4">
                        <span className="font-mono text-sm tracking-widest text-gray-300">
                            {caption}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
