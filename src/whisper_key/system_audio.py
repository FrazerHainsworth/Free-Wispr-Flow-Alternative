# system_audio.py
# Optional system-audio (loopback) capture — transcribe what you HEAR (meetings,
# videos, calls), not just the microphone. Deliberately isolated from
# AudioRecorder's always-on mic stream so it cannot affect normal dictation.
#
# Backed by the optional `soundcard` package (WASAPI loopback on Windows,
# CoreAudio on macOS), installed via `pip install whisper-local[loopback]`.
# soundcard is imported lazily so the base install never depends on it.
#
# EXPERIMENTAL: the actual capture path depends on OS loopback support and needs
# real-hardware verification — it can't be exercised in CI (no audio device).

import logging
import threading
import time

import numpy as np

logger = logging.getLogger(__name__)

WHISPER_SAMPLE_RATE = 16000

_INSTALL_HINT = (
    "System-audio capture needs the optional 'loopback' extra:\n"
    "    pip install whisper-local[loopback]"
)


# True when the soundcard backend is importable. Cheap enough to call before
# offering the feature in a menu / CLI.
def is_available() -> bool:
    try:
        import soundcard  # noqa: F401
        return True
    except Exception:
        return False


# Record `seconds` of the default speaker's output as a mono float32 array at
# 16 kHz (the rate the Whisper pipeline expects). Returns None — never raises —
# if soundcard is missing or no loopback endpoint is available, so callers can
# degrade gracefully.
def capture_loopback(seconds: float, samplerate: int = WHISPER_SAMPLE_RATE):
    try:
        import soundcard as sc
    except Exception:
        logger.warning("soundcard not installed; cannot capture system audio")
        print(_INSTALL_HINT)
        return None

    try:
        speaker = sc.default_speaker()
        # A loopback "microphone" mirrors what the speaker is playing.
        loopback = sc.get_microphone(id=str(speaker.name), include_loopback=True)
        frames = int(samplerate * max(0.1, float(seconds)))
        with loopback.recorder(samplerate=samplerate, channels=1) as rec:
            data = rec.record(numframes=frames)
    except Exception as e:
        logger.error(f"System-audio capture failed: {e}")
        print(f"System-audio capture failed: {e}")
        return None

    arr = np.asarray(data, dtype=np.float32)
    if arr.ndim > 1:  # collapse any stray channel dimension to mono
        arr = arr.mean(axis=1)
    return arr


class LoopbackCapture:
    # Records the default speaker in short chunks until stop() or max_seconds.
    # Headphones and speakers are the same thing here: whatever Windows is
    # playing. The microphone is not used.

    def __init__(self, max_seconds: float = 900):
        self.max_seconds = max(1.0, float(max_seconds))
        self._stop = threading.Event()
        self._user_stopped = False
        self._thread = None
        self._chunks = []
        self._buckets = []
        self._rate = 48000
        self.recording = False
        self.error = None
        self.on_auto_stop = None

    def start(self) -> bool:
        if not is_available():
            self.error = _INSTALL_HINT
            return False
        self._stop.clear()
        self._user_stopped = False
        self._chunks = []
        self._buckets = []
        self.error = None
        self._thread = threading.Thread(target=self._run, daemon=True, name='loopback-capture')
        self._thread.start()
        deadline = time.time() + 1.5
        while time.time() < deadline and not self.recording and not self.error:
            time.sleep(0.05)
        return self.recording and not self.error

    def stop(self):
        self._user_stopped = True
        self._stop.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=5)
        self.recording = False
        return self._assemble()

    def _run(self):
        try:
            import soundcard as sc
            speakers = list(sc.all_speakers())
            if not speakers:
                self.error = "No playback device found."
                return
            threads = []
            started = time.time()
            for speaker in speakers:
                bucket = []
                self._buckets.append(bucket)
                thread = threading.Thread(
                    target=self._record_one,
                    args=(speaker, bucket, started),
                    daemon=True,
                    name=f"loopback-{speaker.name}",
                )
                thread.start()
                threads.append(thread)
            # _record_one sets recording once a device opens.
            for thread in threads:
                thread.join()
        except Exception as e:
            self.error = str(e)
            logger.error(f"System-audio capture failed: {e}")
        finally:
            self.recording = False
            if not self._user_stopped and self.on_auto_stop:
                threading.Thread(target=self.on_auto_stop, daemon=True).start()

    def _record_one(self, speaker, bucket, started):
        try:
            import soundcard as sc
            loopback = sc.get_microphone(id=str(speaker.name), include_loopback=True)
            with loopback.recorder(samplerate=self._rate, channels=1) as rec:
                self.recording = True
                logger.info(f"Listening to {speaker.name}")
                while not self._stop.is_set():
                    if time.time() - started >= self.max_seconds:
                        break
                    data = rec.record(numframes=self._rate // 2)
                    arr = np.asarray(data, dtype=np.float32)
                    if arr.ndim > 1:
                        arr = arr.mean(axis=1)
                    if len(arr):
                        bucket.append(arr)
        except Exception as e:
            logger.warning(f"Could not listen to {speaker.name}: {e}")

    def _assemble(self):
        tracks = []
        for bucket in self._buckets or []:
            if bucket:
                tracks.append(np.concatenate(bucket))
        if not tracks and self._chunks:
            tracks.append(np.concatenate(self._chunks))
        if not tracks:
            return None
        length = max(len(track) for track in tracks)
        mixed = np.zeros(length, dtype=np.float32)
        for track in tracks:
            mixed[:len(track)] += track
        peak = float(np.max(np.abs(mixed))) if len(mixed) else 0.0
        if peak > 1.0:
            mixed = mixed / peak
        audio = mixed
        if self._rate != WHISPER_SAMPLE_RATE:
            import soxr
            audio = soxr.resample(audio, self._rate, WHISPER_SAMPLE_RATE)
        return np.asarray(audio, dtype=np.float32)


# Capture then transcribe in one step, reusing the app's existing Whisper engine
# and its transcribe_audio contract (mono float32 @ 16 kHz). Returns '' on any
# failure or silence.
def record_and_transcribe(seconds: float, whisper_engine,
                          samplerate: int = WHISPER_SAMPLE_RATE) -> str:
    audio = capture_loopback(seconds, samplerate)
    if audio is None or len(audio) == 0:
        return ''
    return whisper_engine.transcribe_audio(audio) or ''


# CLI entry point for `whisper-local --transcribe-system [SECONDS]`. Records that
# many seconds of system audio, transcribes with the configured model, prints the
# text and copies it to the clipboard. Self-contained: bootstraps its own engine
# (mirrors selftest) so it doesn't require the full app to be running. Returns a
# process exit code.
def run_cli(seconds: int = 10) -> int:
    if not is_available():
        print(_INSTALL_HINT)
        return 1

    try:
        from .config_manager import ConfigManager
        from .model_registry import ModelRegistry
        from .voice_activity_detection import VadManager
        from .whisper_engine import WhisperEngine

        cm = ConfigManager(quiet=True)
        whisper_cfg = cm.get_whisper_config()
        registry = ModelRegistry(
            whisper_models_config=whisper_cfg.get('models', {}),
            streaming_models_config={},
        )
        vad_manager = VadManager(
            vad_precheck_enabled=False, vad_realtime_enabled=False,
            vad_onset_threshold=0.5, vad_offset_threshold=0.5,
            vad_min_speech_duration=0.1, vad_silence_timeout_seconds=999.0,
        )
        # Honour the configured backend so we don't silently transcribe with
        # faster-whisper (and trigger a redundant model download) when the user
        # chose whisper_cpp — mirrors selftest's end-to-end bootstrap.
        engine_kwargs = dict(
            model_key=whisper_cfg['model'], device=whisper_cfg['device'],
            compute_type=whisper_cfg['compute_type'],
            language=whisper_cfg.get('language', 'auto'),
            beam_size=whisper_cfg.get('beam_size', 5), initial_prompt='',
            hotwords=[], task='transcribe', vad_manager=vad_manager,
            model_registry=registry,
        )
        if whisper_cfg.get('backend', 'faster_whisper') == 'whisper_cpp':
            from .whisper_engine_cpp import WhisperEngineCpp
            engine = WhisperEngineCpp(**engine_kwargs)
        else:
            engine = WhisperEngine(**engine_kwargs)
    except Exception as e:
        print(f"Could not initialise transcription engine: {e}")
        return 1

    print(f"🔊 Capturing {seconds}s of system audio — play the audio now...")
    text = record_and_transcribe(seconds, engine)
    if not text:
        print("No speech detected in the captured system audio.")
        return 1

    print("\n--- Transcription ---")
    print(text)
    try:
        import pyperclip
        pyperclip.copy(text)
        print("\n(Copied to clipboard.)")
    except Exception:
        pass
    return 0
