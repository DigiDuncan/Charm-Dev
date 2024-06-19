"""
This type stub file was generated by pyright.
"""

from pyglet.media.devices.base import DeviceFlow
from pyglet.libs.win32.types import *

_debug = ...
def create_xa2_buffer(audio_data): # -> XAUDIO2_BUFFER:
    """Creates a XAUDIO2_BUFFER to be used with a source voice.
        Audio data cannot be purged until the source voice has played it; doing so will cause glitches."""
    ...

def create_xa2_waveformat(audio_format): # -> WAVEFORMATEX:
    ...

class _VoiceResetter:
    """Manage a voice during its reset period."""
    def __init__(self, driver, voice, voice_key, remaining_data) -> None:
        ...
    
    def run(self): # -> None:
        ...
    
    def flush_on_buffer_end(self, *_): # -> None:
        ...
    
    def destroy(self): # -> None:
        ...
    


class XA2EngineCallback(com.COMObject):
    _interfaces_ = ...
    def __init__(self, lock) -> None:
        ...
    
    def OnProcessingPassStart(self): # -> None:
        ...
    
    def OnProcessingPassEnd(self): # -> None:
        ...
    
    def OnCriticalError(self, hresult):
        ...
    


class XAudio2VoiceCallback(com.COMObject):
    """Callback class used to trigger when buffers or streams end.
           WARNING: Whenever a callback is running, XAudio2 cannot generate audio.
           Make sure these functions run as fast as possible and do not block/delay more than a few milliseconds.
           MS Recommendation:
           At a minimum, callback functions must not do the following:
                - Access the hard disk or other permanent storage
                - Make expensive or blocking API calls
                - Synchronize with other parts of client code
                - Require significant CPU usage
    """
    _interfaces_ = ...
    def __init__(self) -> None:
        ...
    
    def OnBufferEnd(self, pBufferContext): # -> None:
        ...
    
    def OnVoiceError(self, pBufferContext, hresult):
        ...
    


class XAudio2Driver:
    allow_3d = ...
    processor = ...
    category = ...
    restart_on_error = ...
    max_frequency_ratio = ...
    def __init__(self) -> None:
        """Creates an XAudio2 master voice and sets up 3D audio if specified. This attaches to the default audio
        device and will create a virtual audio endpoint that changes with the system. It will not recover if a
        critical error is encountered such as no more audio devices are present.
        """
        ...
    
    def on_default_changed(self, device, flow: DeviceFlow): # -> None:
        ...
    
    @property
    def active_voices(self): # -> dict_keys[Any, Any]:
        ...
    
    def set_device(self, device): # -> None:
        """Attach XA2 with a specific device rather than the virtual device."""
        ...
    
    def enable_3d(self): # -> None:
        """Initializes the prerequisites for 3D positional audio and initializes with default DSP settings."""
        ...
    
    @property
    def volume(self): # -> float:
        ...
    
    @volume.setter
    def volume(self, value): # -> None:
        """Sets global volume of the master voice."""
        ...
    
    def apply3d(self, source_voice): # -> None:
        """Apply and immediately commit positional audio effects for the given voice."""
        ...
    
    def delete(self): # -> None:
        ...
    
    def get_performance(self): # -> XAUDIO2_PERFORMANCE_DATA:
        """Retrieve some basic XAudio2 performance data such as memory usage and source counts."""
        ...
    
    def create_listener(self): # -> XAudio2Listener:
        ...
    
    def return_voice(self, voice, remaining_data): # -> None:
        """Reset a voice and eventually return it to the pool. The voice must be stopped.
        `remaining_data` should contain the data this voice's remaining
        buffers point to.
        It will be `.clear()`ed shortly after as soon as the flush initiated
        by the driver completes in order to not have theoretical dangling
        pointers.
        """
        ...
    
    def get_source_voice(self, audio_format, player): # -> XA2SourceVoice:
        """Get a source voice from the pool. Source voice creation can be slow to create/destroy.
        So pooling is recommended. We pool based on audio channels.
        A source voice handles all of the audio playing and state for a single source."""
        ...
    


class XA2SourceVoice:
    def __init__(self, voice, callback, channel_count, sample_size) -> None:
        ...
    
    def destroy(self): # -> None:
        """Completely destroy the voice."""
        ...
    
    def acquired(self, on_buffer_end_cb, sample_rate): # -> None:
        """A voice has been acquired. Set the callback as well as its new sample
        rate.
        """
        ...
    
    @property
    def buffers_queued(self): # -> Any:
        """Get the amount of buffers in the current voice. Adding flag for no samples played is 3x faster."""
        ...
    
    @property
    def samples_played(self): # -> Any:
        """Get the amount of samples played by the voice."""
        ...
    
    @property
    def volume(self): # -> float:
        ...
    
    @volume.setter
    def volume(self, value): # -> None:
        ...
    
    @property
    def is_emitter(self): # -> bool:
        ...
    
    @property
    def position(self): # -> tuple[Any, Any, Any] | tuple[Literal[0], Literal[0], Literal[0]]:
        ...
    
    @position.setter
    def position(self, position): # -> None:
        ...
    
    @property
    def min_distance(self): # -> Any | Literal[0]:
        """Curve distance scaler that is used to scale normalized distance curves to user-defined world units,
        and/or to exaggerate their effect."""
        ...
    
    @min_distance.setter
    def min_distance(self, value): # -> None:
        ...
    
    @property
    def frequency(self): # -> float:
        """The actual frequency ratio. If voice is 3d enabled, will be overwritten next apply3d cycle."""
        ...
    
    @frequency.setter
    def frequency(self, value): # -> None:
        ...
    
    @property
    def cone_orientation(self): # -> tuple[Any, Any, Any] | tuple[Literal[0], Literal[0], Literal[0]]:
        """The orientation of the sound emitter."""
        ...
    
    @cone_orientation.setter
    def cone_orientation(self, value): # -> None:
        ...
    
    _ConeAngles = ...
    @property
    def cone_angles(self): # -> _ConeAngles:
        """The inside and outside angles of the sound projection cone."""
        ...
    
    def set_cone_angles(self, inside, outside): # -> None:
        """The inside and outside angles of the sound projection cone."""
        ...
    
    @property
    def cone_outside_volume(self): # -> Any | Literal[0]:
        """The volume scaler of the sound beyond the outer cone."""
        ...
    
    @cone_outside_volume.setter
    def cone_outside_volume(self, value): # -> None:
        ...
    
    @property
    def cone_inside_volume(self): # -> Any | Literal[0]:
        """The volume scaler of the sound within the inner cone."""
        ...
    
    @cone_inside_volume.setter
    def cone_inside_volume(self, value): # -> None:
        ...
    
    def flush(self): # -> None:
        """Stop and removes all buffers already queued. OnBufferEnd is called for each."""
        ...
    
    def play(self): # -> None:
        ...
    
    def stop(self): # -> None:
        ...
    
    def submit_buffer(self, x2_buffer): # -> None:
        ...
    


class XAudio2Listener:
    def __init__(self, driver) -> None:
        ...
    
    def delete(self): # -> None:
        ...
    
    @property
    def position(self): # -> tuple[Any, Any, Any]:
        ...
    
    @position.setter
    def position(self, value): # -> None:
        ...
    
    @property
    def orientation(self): # -> tuple[Any, Any, Any, Any, Any, Any]:
        ...
    
    @orientation.setter
    def orientation(self, orientation): # -> None:
        ...
    

