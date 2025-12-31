import { useState } from 'react';
import { GuardianLayout } from './components/layout/GuardianLayout';
import { VisionPanel } from './components/vision/VisionPanel';
import { SbarSidebar } from './components/alerts/SbarSidebar';
import { EmergencyModal } from './components/alerts/EmergencyModal';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [emergencyTriggered, setEmergencyTriggered] = useState(false);
  const [sbarData, setSbarData] = useState<any>(null);

  const handleVisionResults = (data: any) => {
    // Update SBAR data if present (it comes as a string, sidebar expects object, wait, let's check sidebar)
    // Sidebar code: interface SbarData { situation?: string ... }
    // Backend sends "sbar": "string....."
    // We need to parse or adjust sidebar.
    // Actually, looking at backend code: result["sbar_preview"] which is a string.
    // The previous code in Agent Protocol returned a string.
    // But SbarSidebar.tsx expects an object with situation, background...
    // Let's modify SbarSidebar to just take a string, OR parse it here.
    // For now, let's parse it here if possible, or simpler: adjust data structure.

    // Actually, the prompt said "sbar": "..." (string).
    // Let's check SbarSidebar.tsx again.

    // ...Checking sidebar logic in my head...
    // SbarSidebar takes `data: SbarData | null`.
    // It constructs `fullText` using `data.situation`, etc.
    // If I pass a simple object `{ situation: data.sbar }` it might work if sbar is just one block.

    if (data.sbar) {
      setSbarData(data.sbar);
    }

    // Check for critical alerts
    if (data.status === "alert") {
      setEmergencyTriggered(true);
    }
  };

  return (
    <GuardianLayout isConnected={isConnected} emergencyTriggered={emergencyTriggered}>
      <VisionPanel
        onResults={handleVisionResults}
        isConnected={isConnected}
        setIsConnected={setIsConnected}
        setEmergencyTriggered={setEmergencyTriggered}
      />

      <SbarSidebar data={sbarData} />

      <EmergencyModal
        isOpen={emergencyTriggered}
        onCancel={() => setEmergencyTriggered(false)}
      />
    </GuardianLayout>
  );
}

export default App;
