import httpx
from verge_schema.enums import FindingState
from verge_schema.findings import RiskFinding
from verge_voice.alert_preview import alert_preview
from verge_voice.near_miss import near_miss_from_transcript
from verge_voice.transcribe import SpeechmaticsSettings, structure_handover, transcribe_audio


def test_missing_key_degrades() -> None:
    body = transcribe_audio(b"audio", env={}).to_dict()
    assert body["degraded"] is True
    assert body["transcript"] == ""
    assert body["structured"]["hazards"] == []


def test_structure_handover_extracts_basic_evidence() -> None:
    structured = structure_handover(
        "B-04 has rising LEL gas during hot work. Pause the permit and escalate."
    )
    assert "gas" in structured["hazards"]
    assert "hot-work" in structured["hazards"]
    assert "B-04" in structured["zones"]
    assert "pause" in structured["actions"]
    assert "escalate" in structured["actions"]


def test_speechmatics_flow_is_mocked() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.method == "POST" and request.url.path == "/v2/jobs":
            return httpx.Response(201, json={"id": "job-1"})
        if request.url.path == "/v2/jobs/job-1":
            return httpx.Response(200, json={"job": {"status": "done"}})
        if request.url.path == "/v2/jobs/job-1/transcript":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {"alternatives": [{"content": "B-04"}]},
                        {"alternatives": [{"content": "gas"}]},
                        {"alternatives": [{"content": "pause"}]},
                    ]
                },
            )
        return httpx.Response(404)

    client = httpx.Client(
        base_url="https://eu1.asr.api.speechmatics.com/v2",
        transport=httpx.MockTransport(handler),
    )
    result = transcribe_audio(
        b"audio",
        filename="handover.wav",
        client=client,
        settings=SpeechmaticsSettings(api_key="key", poll_interval_s=0, max_polls=1),
    ).to_dict()

    assert result["degraded"] is False
    assert result["jobId"] == "job-1"
    assert result["transcript"] == "B-04 gas pause"
    assert calls == ["/v2/jobs", "/v2/jobs/job-1", "/v2/jobs/job-1/transcript"]


def test_near_miss_from_transcript_links_finding() -> None:
    body = near_miss_from_transcript("B-04 gas near miss, pause work", finding_id="F-1")
    assert body["kind"] == "voice-near-miss"
    assert body["findingId"] == "F-1"
    assert "gas" in body["structured"]["hazards"]


def test_alert_preview_degrades_with_template() -> None:
    finding = RiskFinding(
        finding_id="F-1",
        created_at="2025-01-13T06:44:00Z",
        zone_id="B-04",
        title="Hot work + rising gas",
        state=FindingState.NEW,
        confidence=0.85,
    )
    body = alert_preview(finding)
    assert body["degraded"] is True
    assert "B-04" in body["languages"]["en"]
