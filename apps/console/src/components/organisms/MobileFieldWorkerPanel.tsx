import { useState, useEffect } from 'react';
import { Card, Button } from '@/components/atoms';
import { Mic, Camera, MapPin, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ExposureReading {
  gas: string;
  value: string;
  limit: string;
  status: 'safe' | 'warning' | 'critical';
}

export function MobileFieldWorkerPanel() {
  const [isRecording, setIsRecording] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  const [photoCaptured, setPhotoCaptured] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsError, setGpsError] = useState<string | null>(null);

  // Exposure readings mock data
  const exposureReadings: ExposureReading[] = [
    { gas: 'CH4 Methane', value: '0.05% LEL', limit: '1.0% LEL', status: 'safe' },
    { gas: 'H2S Hydrogen Sulfide', value: '2.5 ppm', limit: '10 ppm', status: 'safe' },
    { gas: 'CO Carbon Monoxide', value: '12 ppm', limit: '25 ppm', status: 'safe' },
  ];

  // Geolocation API check
  useEffect(() => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your device.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      },
      (err) => {
        setGpsError(`GPS Access Denied: ${err.message}`);
      }
    );
  }, []);

  // Web Speech API reporting
  const handleVoiceReport = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceText('Voice recognition not supported on this browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsRecording(true);
      setVoiceText('Listening for hazard description...');
    };

    recognition.onerror = (e: any) => {
      console.error(e);
      setVoiceText('Voice capture error.');
      setIsRecording(false);
    };

    recognition.onresult = (event: any) => {
      const resultText = event.results[0][0].transcript;
      setVoiceText(`" ${resultText} "`);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
  };

  return (
    <div className="flex flex-col gap-4 text-ink select-none font-mono">
      {/* 1. Worker personal exposure panel */}
      <Card className="p-3 bg-panel border-line flex flex-col gap-2">
        <span className="text-micro font-bold text-ink-dim uppercase flex items-center gap-1.5 border-b border-line pb-1.5 select-none">
          <ShieldCheck className="h-3.5 w-3.5 text-ok" />
          Personal Gas Exposure
        </span>
        <div className="flex flex-col gap-2 select-text">
          {exposureReadings.map((r, idx) => (
            <div key={idx} className="flex justify-between items-center bg-panel-2/50 p-2 rounded border border-line">
              <div className="flex flex-col gap-0.5">
                <span className="text-micro font-bold text-ink">{r.gas}</span>
                <span className="text-[10px] text-ink-dim">LIMIT: {r.limit}</span>
              </div>
              <span className="text-xs font-bold text-ok tabular-nums">{r.value}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* 2. Geolocation Nearby observations */}
      <Card className="p-3 bg-panel border-line flex flex-col gap-2 select-text">
        <span className="text-micro font-bold text-ink-dim uppercase flex items-center gap-1.5 border-b border-line pb-1.5 select-none">
          <MapPin className="h-3.5 w-3.5 text-watch animate-bounce" />
          Nearby Safety Threats (&lt;50m)
        </span>
        {coords ? (
          <div className="text-xs flex flex-col gap-1.5">
            <div className="flex justify-between text-micro text-ink-dim">
              <span>LATITUDE: {coords.lat.toFixed(5)}</span>
              <span>LONGITUDE: {coords.lng.toFixed(5)}</span>
            </div>
            <div className="bg-panel-2/30 p-2 border border-line rounded flex items-start gap-2 text-micro leading-normal">
              <AlertTriangle className="h-3.5 w-3.5 text-near shrink-0" />
              <div>
                <span className="font-bold">Zone 4 Reformer (40m away)</span>: Active risk alert logged for gas concentration (CH4).
              </div>
            </div>
          </div>
        ) : (
          <span className="text-[10px] text-ink-dim italic">
            {gpsError ? gpsError : 'Fetching location coords...'}
          </span>
        )}
      </Card>

      {/* 3. Speech-to-Text Voice Observation reporter */}
      <Card className="p-3 bg-panel border-line flex flex-col gap-3">
        <span className="text-micro font-bold text-ink-dim uppercase flex items-center gap-1.5 border-b border-line pb-1.5 select-none">
          <Mic className="h-3.5 w-3.5 text-accent" />
          Voice Observation Reporter
        </span>
        
        <div className="flex gap-2">
          <Button
            variant={isRecording ? 'danger' : 'secondary'}
            size="sm"
            onClick={handleVoiceReport}
            icon={<Mic className="h-3.5 w-3.5" />}
            className="w-1/2 uppercase text-micro font-bold"
          >
            {isRecording ? 'Recording...' : 'Voice Report'}
          </Button>

          <Button
            variant={photoCaptured ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setPhotoCaptured(true)}
            icon={<Camera className="h-3.5 w-3.5" />}
            className="w-1/2 uppercase text-micro font-bold border-line"
          >
            {photoCaptured ? 'Photo Attached' : 'Attach Photo'}
          </Button>
        </div>

        {voiceText && (
          <div className="bg-bg border border-line p-2.5 rounded text-xs select-text leading-relaxed font-mono">
            {voiceText}
          </div>
        )}
      </Card>
    </div>
  );
}
