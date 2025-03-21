# HCR-ICRS Interaction

This repository contains the software components and hardware designs for the interaction side of the ICRSBot project.

Below are the high-level component responsibilities. Important files not referred to here (e.g. `interaction.py`) were the combined work of multiple group members at different times.

## INTERACTION

### LLM

Written by David. Generates natural-language responses and calls functions based on user input.

#### Installation

- Install Ollama from [here](https://ollama.com/)
- Run `ollama pull llama3.2` in terminal

#### Usage

- Run `ollama serve` in terminal

### Logistics

Written by Kevin and Ryusei. Tracks stock of project boxes and components using the database and runs the discord bot. Also runs the control loop for the dispenser and forklift.

### mocks

Written by Pierce. Stand-ins for system components for testing (e.g. using text input to test the LLM while bypassing speech recognition). More detail in the [mocks README](./INTERACTION/mocks/).

### SLAM

Written by Ryusei. Deprecated system for precise navigation.

### TTS

Written by Yomna. Performs speech synthesis and sentiment analysis using ElevenLabs. Saves audio files for `Visuals` to access.

### Visuals

Written by Meigan, with captions implemented by Pierce. The visuals system takes inputs from `interaction.py`, but can be run alone by `run_visuals.py`.

## HARDWARE

More detail available in [the Hardware README](./HARDWARE/Chassis_Documentation.md), along with links to OnShape, which contains the remaining 3D models.

### Frame_Documentation

Designed by Meigan. Design pages accessed by the team during the intial stage.

### Gantry

Designed by Albi. The model for the gantry/forklift system.

### Micro_Controller_Code

Written by James. Code to control the dispenser and gantry/forklift.

## ARCHIVE
### Logistics

Hosted Discord bot on GUI during testing.

### speech_to_text

Written by Monika. Deprecated system for transcription before moving to RealtimeSTT. More detail available in [the Speech to Test README](./ARCHIVE/speech_to_text/readme.md).