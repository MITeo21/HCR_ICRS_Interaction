# Mock Systems

These are systems that can be used for testing components without relying on other components.

## [Text To Text Mock](./text_to_text.py)

This bypasses the `AudioToTextRecorder` from `RealtimeSTT`.\
It provides a component with a similar API to that of the STT component, including the async behaviours, but no external API calls are made.

Using this component is as simple as replacing it in the import:
```python
# from TTS.tts_class import TTS
from mocks.text_to_text import TTT as TTS
```
