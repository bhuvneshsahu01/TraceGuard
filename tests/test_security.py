from traceguard.sanitizers import AudioSanitizerAgent
from traceguard.monitors.exfil import SemanticDLPEngine

def test_audio_sanitizer():
    sanitizer = AudioSanitizerAgent(ultrasonic_threshold_khz=20.0)
    
    class MockSafeAudio: peak_frequency_khz = 10.0
    class MockAttackAudio: peak_frequency_khz = 25.5
    
    res1 = sanitizer.sanitize_audio({"audio_data": MockSafeAudio()})
    assert res1["status"] == "CLEAN"
    
    res2 = sanitizer.sanitize_audio({"audio_data": MockAttackAudio()})
    assert res2["status"] == "BLOCKED"
    assert "ultrasonic" in res2["reason"].lower()

def test_differential_outlier():
    dlp = SemanticDLPEngine()
    
    # Normal ratio (1:10)
    assert dlp.check_differential_outlier(10, 100)
    
    # RAG Poison Exfil ratio (1:100)
    assert not dlp.check_differential_outlier(10, 1000)
