# Mock Systems

These are substitute systems that maintain all the same APIs and similar call behaviour to their counterparts, except that they don't do any heavy computation or make expensive API calls. This makes them ideal for testing and faster iteration loops when testing and debugging other components.

All calls are designed to slot in exactly where their counterparts would, so nothing needs to be rewritten to be able to use these mock components (but, of course, they don't implement full library functionality, so I didn't see while writing these systems will need to be added).

## [Text To Text Mock](./text_to_text.py)

This bypasses the text-to-speech component from [`TTS`](../TTS/tts_class.py).\
It provides a component with a similar API to that of the TTS component, including the async behaviours, but no external API calls are made.

### How To Use

Using this component is as simple as replacing it in the import:
```python
# from TTS.tts_class import TTS
from mocks.text_to_text import TTT as TTS
```

## [Input Server](./text_to_text.py)

This bypasses the `AudioToTextRecorder` from `RealtimeSTT`.\
It provides a component with a similar API and behaviour to the ATT component, but it's neither recording sound nor processing any audio.

The Input Server receives its input via a simple TCP socket that a client can connect to, and adds any received text input to a queue, which is handled by the usual pipeline.

### How To Use

Firstly, as above, replace it in the import:
```python
# from RealtimeSTT import AudioToTextRecorder
from mocks.text_to_text import InputServer as AudioToTextRecorder
```

Then, start a client of some sort and connect to the server at `http://localhost:13245`, any strings sent in TCP packets will be accepted.

The easiest way to do this on a Linux distribution is probably to use [netcat](https://linux.die.net/man/1/nc):
```bash
nc localhost 13245
```

#### `OSError: [Errno 98] Address already in use`

If the port number is already in use, the `ITTS_PORT` environment variable can be set, to shift the port number to a free port:

```bash
export ITTS_PORT=13246
```

When you're done, or would like to switch the port back to its default, just unset the environment variable you have set above, like this:

```bash
unset ITTS_PORT
```