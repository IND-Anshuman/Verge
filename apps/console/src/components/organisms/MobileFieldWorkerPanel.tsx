import { useState, useEffect } from 'react';
import { Card, Button } from '@/components/atoms';
import { Mic, Camera, MapPin, AlertTriangle, ShieldCheck, AlertCircle } from 'lucide-react';
import type { RiskFinding } from '@/types';
import { getSensorRibbon } from '@/api/sensors';
import { submitVoiceHandover, textToHandoverWav } from '@/api/voice';

interface MobileFieldWorkerPanelProps {
  findings?: RiskFinding[];
}

interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onerror: (() => void) | null;
  onresult: ((event: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
}

export function MobileFieldWorkerPanel({ findings = [] }: MobileFieldWorkerPanelProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  const [voiceStatus, setVoiceStatus] = useState<string | null>(null);
  const [photoCaptured, setPhotoCaptured] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [ribbonText, setRibbonText] = useState<string | null>(null);
  const [ribbonError, setRibbonError] = useState<string | null>(null);

  const activeFindings = findings.filter((f) => f.state !== 'resolved' && f.state !== 'closed');

  useEffect(() => {
    getSensorRibbon()
      .then((r) => {
        setRibbonText(r.text);
        setRibbonError(null);
      })
      .catch(() => {
        setRibbonText(null);
        setRibbonError('Sensor ribbon unavailable.');
      });
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your device.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => setGpsError(`GPS Access Denied: ${err.message}`),
    );
  }, []);

  const handleVoiceReport = () => {
    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition;
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
      setVoiceStatus(null);
    };

    recognition.onerror = () => {
      setVoiceText('Voice capture error.');
      setIsRecording(false);
    };

    recognition.onresult = (event) => {
      const resultText = event.results[0][0].transcript;
      setVoiceText(`"${resultText}"`);
      setIsRecording(false);
      void submitVoice(resultText);
    };

    recognition.onend = () => setIsRecording(false);
    recognition.start();
  };

  const submitVoice = async (transcript: string) => {
    setVoiceStatus('Submitting to Speechmatics…');
    try {
      const file = textToHandoverWav(transcript);
      const result = await submitVoiceHandover(file, 'field-worker');
      if (result.degraded) {
        setVoiceStatus(result.reason ?? 'Voice degraded — audit entry may still be recorded.');
      } else {
        setVoiceStatus(
          result.auditAppended
            ? 'Handover logged to audit chain.'
            : 'Transcript received.',
        );
      }
    } catch {
      setVoiceStatus('Voice API unavailable — start backend with `make dev`.');
    }
  };

  return (
    <div className="flex flex-col gap-4 text-ink select-none font-mono">
      <Card className="p-3 bg-panel border-line flex flex-col gap-2">
        <span className="text-micro font-bold text-ink-dim uppercase flex items-center gap-1.5 border-b border-line pb-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-ok" />
          Sensor Fleet Health
        </span>
        {ribbonError ? (
          <div className="text-xs text-imminent flex items-center gap-2">
            <AlertCircle className="h-3.5 w-3.5" />
            {ribbonError}
          </div>
        ) : ribbonText ? (
          <p className="text-xs text-ink leading-relaxed select-text">{ribbonText}</p>
        ) : (
          <p className="text-[10px] text-ink-dim italic">Loading ribbon…</p>
        )}
      </Card>

      <Card className="p-3 bg-panel border-line flex flex-col gap-2 select-text">
        <span className="text-micro font-bold text-ink-dim uppercase flex items-center gap-1.5 border-b border-line pb-1.5 select-none">
          <MapPin className="h-3.5 w-3.5 text-watch animate-bounce" />
          Active Zone Alerts
        </span>
        {activeFindings.length === 0 ? (
          <span className="text-[10px] text-ink-dim italic uppercase">No active findings on feed</span>
        ) : (
          activeFindings.slice(0, 4).map((f) => (
            <div
              key={f.findingId}
              className="bg-panel-2/30 p-2 border border-line rounded flex items-start gap-2 text-micro leading-normal"
            >
              <AlertTriangle className="h-3.5 w-3.5 text-near shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">{f.zoneId}</span>: {f.title}
              </div>
            </div>
          ))
        )}
        {coords && (
          <div className="flex justify-between text-micro text-ink-dim border-t border-line pt-2 mt-1">
            <span>LAT {coords.lat.toFixed(5)}</span>
            <span>LNG {coords.lng.toFixed(5)}</span>
          </div>
        )}
        {!coords && (
          <span className="text-[10px] text-ink-dim italic">
            {gpsError ?? 'Fetching location…'}
          </span>
        )}
      </Card>

      <Card className="p-3 bg-panel border-line flex flex-col gap-3">
        <span className="text-micro font-bold text-ink-dim uppercase flex items-center gap-1.5 border-b border-line pb-1.5">
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
            {isRecording ? 'Recording…' : 'Voice Report'}
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
          <div className="bg-bg border border-line p-2.5 rounded text-xs select-text leading-relaxed">
            {voiceText}
          </div>
        )}
        {voiceStatus && (
          <p className="text-[10px] text-ink-dim leading-relaxed select-text">{voiceStatus}</p>
        )}
      </Card>
    </div>
  );
}
