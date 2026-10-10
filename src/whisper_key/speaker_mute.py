# speaker_mute.py
# Mutes whatever is actually playing (every active speaker or headphone, and the
# apps making the sound) while the microphone is open, then restores only what
# this call muted. Already-muted devices are left alone. System-audio capture
# must not use this — muting the speakers would silence what it hears.

import logging
import sys
import time

logger = logging.getLogger(__name__)

_PEAK = 0.01


def mute_if_audible():
    # Returns a restore token when this call muted something, otherwise None.
    # None means "do not restore" (already quiet, already muted, or unavailable).
    if sys.platform != "win32":
        return None
    try:
        _coinit()
        devices = _render_devices()
        if not devices:
            logger.warning("Could not mute speakers: no playback device")
            return None

        audible = _something_playing(devices)
        if not audible:
            logger.info("Speakers already quiet — not muting")
            return None

        endpoints = []
        sessions = []
        for device in devices:
            try:
                volume = device.EndpointVolume
                if bool(volume.GetMute()):
                    continue
                volume.SetMute(1, None)
                endpoints.append(device.id)
                logger.info(f"Muted playback device: {device.FriendlyName}")
            except Exception as e:
                logger.warning(f"Could not mute {getattr(device, 'FriendlyName', '?')}: {e}")
            for session in _device_sessions(device):
                token = _mute_session(session)
                if token:
                    sessions.append(token)

        if not endpoints and not sessions:
            logger.info("Playback was already muted — leaving it muted")
            return None
        logger.info(f"Muted {len(endpoints)} device(s) and {len(sessions)} app session(s)")
        return {"endpoints": endpoints, "sessions": sessions}
    except Exception as e:
        logger.warning(f"Could not mute speakers: {e}")
        return None


def restore_mute(token):
    if not token or sys.platform != "win32":
        return
    try:
        _coinit()
        endpoint_ids = set(token.get("endpoints") or [])
        session_keys = set(token.get("sessions") or [])
        for device in _render_devices():
            if device.id in endpoint_ids:
                try:
                    device.EndpointVolume.SetMute(0, None)
                except Exception as e:
                    logger.warning(f"Could not unmute {device.FriendlyName}: {e}")
            for session in _device_sessions(device):
                key = _session_key(session)
                if key not in session_keys:
                    continue
                try:
                    session.SimpleAudioVolume.SetMute(0, None)
                except Exception as e:
                    logger.warning(f"Could not unmute an app session: {e}")
        logger.info("Restored speaker mute state")
    except Exception as e:
        logger.warning(f"Could not restore speaker mute: {e}")


def _coinit():
    import comtypes
    try:
        comtypes.CoInitialize()
    except OSError:
        pass


def _render_devices():
    from pycaw.constants import DEVICE_STATE, EDataFlow
    from pycaw.pycaw import AudioUtilities

    return AudioUtilities.GetAllDevices(
        EDataFlow.eRender.value, DEVICE_STATE.ACTIVE.value
    ) or []


def _something_playing(devices):
    peaks = []
    for device in devices:
        peaks.append(_device_peak(device))
        for session in _device_sessions(device):
            peaks.append(_session_peak(session))
    if any(peak is not None and peak > _PEAK for peak in peaks):
        return True
    # One sample can land in a gap. Check once more before deciding it is quiet.
    time.sleep(0.04)
    for device in devices:
        if (_device_peak(device) or 0) > _PEAK:
            return True
        for session in _device_sessions(device):
            if (_session_peak(session) or 0) > _PEAK:
                return True
    # Meters that all failed are not proof of silence. Mute anyway so the mic
    # does not pick YouTube up when Windows will not report a peak.
    if peaks and all(peak is None for peak in peaks):
        logger.info("Could not read playback level — muting output anyway")
        return True
    return False


def _device_peak(device):
    try:
        import comtypes
        from pycaw.pycaw import IAudioMeterInformation

        iface = device._dev.Activate(
            IAudioMeterInformation._iid_, comtypes.CLSCTX_ALL, None
        )
        meter = iface.QueryInterface(IAudioMeterInformation)
        return float(meter.GetPeakValue())
    except Exception:
        return None


def _device_sessions(device):
    sessions = []
    try:
        from pycaw.api.audiopolicy import IAudioSessionControl2
        from pycaw.pycaw import AudioSession

        enumerator = device.AudioSessionManager.GetSessionEnumerator()
        count = enumerator.GetCount()
    except Exception:
        return sessions
    for index in range(count):
        try:
            ctl = enumerator.GetSession(index)
            ctl2 = ctl.QueryInterface(IAudioSessionControl2)
            if ctl2 is not None:
                sessions.append(AudioSession(ctl2))
        except Exception:
            continue
    return sessions


def _session_peak(session):
    try:
        from pycaw.pycaw import IAudioMeterInformation

        meter = session._ctl.QueryInterface(IAudioMeterInformation)
        return float(meter.GetPeakValue())
    except Exception:
        return None


def _session_key(session):
    try:
        return (int(session.ProcessId), str(session.InstanceIdentifier))
    except Exception:
        return None


def _mute_session(session):
    key = _session_key(session)
    if key is None:
        return None
    try:
        volume = session.SimpleAudioVolume
        if volume is None or bool(volume.GetMute()):
            return None
        peak = _session_peak(session)
        # A silent app stays unmuted. An unreadable meter is muted with the device.
        if peak is not None and peak <= _PEAK:
            return None
        volume.SetMute(1, None)
        return key
    except Exception:
        return None
