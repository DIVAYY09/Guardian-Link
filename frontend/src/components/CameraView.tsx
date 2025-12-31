import React, { useEffect, useRef, useState } from 'react';
import { Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

interface AnalysisResult {
    captions: Array<{ text: string; confidence: number }>;
    objects: Array<{ tag: string; confidence: number }>;
    people: Array<{ confidence: number }>;
    gestures: Array<{ tag: string; probability: number }>;
    emergency_triggered?: boolean;
    sbar?: {
        situation: string;
        background: string;
        assessment: string;
        recommendation: string;
    };
    metadata?: { width: number; height: number; model_version: string };
}

interface CameraViewProps {
    onEmergencyTrigger: (data: AnalysisResult) => void;
    isSimulationMode: boolean;
}

const CameraView: React.FC<CameraViewProps> = ({ onEmergencyTrigger, isSimulationMode }) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [status, setStatus] = useState<'Connected' | 'Disconnected'>('Disconnected');
    const [error, setError] = useState<string | null>(null);
    const [isEmergency, setIsEmergency] = useState(false);

    // Initialize Video Stream
    useEffect(() => {
        const startVideo = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480, facingMode: 'user' }
                });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
            } catch (err: any) {
                console.error("Error accessing camera:", err);
                setError(`Camera Error: ${err.message}`);
            }
        };

        startVideo();

        return () => {
            if (videoRef.current && videoRef.current.srcObject) {
                const stream = videoRef.current.srcObject as MediaStream;
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // Initialize WebSocket with Robust Cleanup
    useEffect(() => {
        let isMounted = true;
        let heartbeatInterval: ReturnType<typeof setInterval>;
        let frameInterval: ReturnType<typeof setInterval>;
        let reconnectTimeout: ReturnType<typeof setTimeout>;

        const connectWebSocket = () => {
            if (!isMounted) return;

            // Use 127.0.0.1 to avoid localhost resolution lag
            console.log("WebSocket Attempting Connection...");
            const ws = new WebSocket('ws://127.0.0.1:8005/ws/stream');

            ws.onopen = () => {
                if (!isMounted) {
                    ws.close();
                    return;
                }
                console.log('WebSocket Connected!');
                setStatus('Connected');
                setError(null);
            };

            ws.onmessage = (event) => {
                if (!isMounted) return;
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'pong') return;

                    if (data.error) {
                        console.error("Backend Error:", data.error);
                    } else {
                        setResult(data);
                        if (data.emergency_triggered || (isSimulationMode && data.gestures?.some((g: any) => g.tag === 'Help' && g.probability > 0.8))) {
                            setIsEmergency(true);
                            onEmergencyTrigger(data);
                        }
                    }
                } catch (e) {
                    console.error("Error parsing WS message", e);
                }
            };

            ws.onclose = () => {
                if (!isMounted) return;
                console.log('Disconnected from WebSocket');
                setStatus('Disconnected');

                // Only attempt reconnect if we are still mounted
                reconnectTimeout = setTimeout(() => {
                    if (isMounted) {
                        console.log("Attempting reconnection...");
                        connectWebSocket();
                    }
                }, 2000);
            };

            ws.onerror = (err) => {
                console.error('WebSocket error:', err);
                if (isMounted) {
                    setStatus('Disconnected');
                    setError('Connection failed');
                }
            };

            wsRef.current = ws;
        };

        connectWebSocket();

        // Heartbeat Interval
        heartbeatInterval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: "ping" }));
            }
        }, 5000);

        // Frame Transmission Interval
        frameInterval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN && videoRef.current && canvasRef.current) {
                const context = canvasRef.current.getContext('2d');
                if (context) {
                    // Draw video to canvas
                    context.drawImage(videoRef.current, 0, 0, 640, 480);
                    // Send frame
                    const base64Data = canvasRef.current.toDataURL('image/jpeg', 0.6);
                    wsRef.current.send(base64Data);
                }
            }
        }, 1000);

        // CRITICAL: Cleanup Function
        return () => {
            isMounted = false;
            clearInterval(heartbeatInterval);
            clearInterval(frameInterval);
            clearTimeout(reconnectTimeout);

            if (wsRef.current) {
                // IMPORTANT: Remove onclose to prevent the "Zombie Reconnect" loop
                wsRef.current.onclose = null;
                wsRef.current.close();
            }
        };
    }, [isSimulationMode]);

    return (
        <div className={clsx(
            "relative w-full aspect-video rounded-3xl overflow-hidden border-4 transition-all duration-500",
            isEmergency ? "border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.6)] animate-pulse" : "border-white/10 shadow-2xl"
        )}>
            {/* Frosted Glass Overlay Effect */}
            <div className="absolute inset-0 pointer-events-none ring-1 ring-white/20 rounded-3xl z-10"></div>

            <video
                ref={videoRef}
                className="w-full h-full object-cover bg-black"
                autoPlay
                muted
                playsInline
            />

            {/* Status Indicator */}
            <div className={`absolute top-4 left-4 backdrop-blur-md border border-white/10 px-3 py-1.5 rounded-full flex items-center gap-2 z-20 ${error ? 'bg-red-500/20 border-red-500/50' : 'bg-black/40'}`}>
                {status === 'Connected' && !error ? <Wifi className="w-4 h-4 text-green-400" /> : <WifiOff className="w-4 h-4 text-red-400" />}
                <span className="text-xs font-medium text-white/90 uppercase tracking-wider">
                    {error ? `Error: ${error}` : status}
                </span>
            </div>

            {/* Emergency Overlay */}
            {isEmergency && (
                <div className="absolute inset-0 z-30 flex flex-col items-center justify-center pointer-events-none">
                    <div className="bg-red-600/20 backdrop-blur-sm border border-red-500/50 p-6 rounded-2xl animate-bounce">
                        <div className="flex items-center gap-3 text-red-500 mb-2">
                            <AlertTriangle className="w-8 h-8 fill-red-500 text-white" />
                            <h2 className="text-3xl font-black uppercase tracking-widest text-shadow-sm text-white">Emergency Triggered</h2>
                        </div>
                        <p className="text-white/90 text-center font-mono">Analyzing Situation... Generating SBAR...</p>
                    </div>
                </div>
            )}

            {/* Debug/Info Overlay */}
            {result && !isEmergency && (
                <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-md p-3 rounded-xl border border-white/10 z-20">
                    <p className="text-xs text-gray-300 font-mono">
                        {result.captions?.[0]?.text || "Scanning..."}
                    </p>
                </div>
            )}

            <canvas ref={canvasRef} width="640" height="480" className="hidden" />
        </div>
    );
};

export default CameraView;