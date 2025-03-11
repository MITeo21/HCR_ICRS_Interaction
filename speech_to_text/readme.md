# Speech-To-Text

## How To Use

Obviously, start with setting up the python virtual environment:

```bash
python3 -m venv venv
pip3 install -r requirements.txt
```

Then modify the configurations in the [`real_time_transcription.py`](./real_time_transcription.py) file, by passing using different `kwarg` values into the instantiation of the STT object. The ones listed below are the defaults.

```python
if __name__ == "__main__":
    stt = SpeechToText(
        model="turbo",
        non_english=False,
        energy_threshold=1000,
        record_timeout=4.0,
        phrase_timeout=3.0,
        transcription_timeout=5.0,
        mic_name="ReSpeaker",
        dynamic_energy_threshold=False
    )
    stt.run()
```

Once you're happy with the configurations, you just need to run the script using this command:

```bash
python3 real_time_transcription.py
```

## How to Integrate

Import the `SpeechToText` class:

```python
from real_time_transcription import SpeechToText
```

And then follow the configuration instructions in [How To Use](#how-to-use), to instantiate an object with specific configurations.
