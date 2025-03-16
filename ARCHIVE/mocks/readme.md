# Mock Systems

These are systems that can be used for testing components without relying on other components.

## [`TextToTextServer`](./text_to_text.py)

This bypasses the [`speech_to_text`](../speech_to_text/) component.\
It provides a component with a similar API to that of the STT component, but is a text-based server.

After swapping out the STT import with:
```python
from mocks.text_to_text import TextToTextServer as SpeechToText
```

Start a client of some sort and connect to the server at `http://localhost:13245`, any strings sent in TCP packets will be accepted.

The easiest way to do this on a Linux distribution is probably to use [netcat](https://linux.die.net/man/1/nc):
```bash
nc localhost 13245
```
