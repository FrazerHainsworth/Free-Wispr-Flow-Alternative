# Free Wispr Flow Alternative

Hold a key, speak, and the words land at your cursor. Transcription runs on your own computer. A cloud rewrite is optional, and it uses a key you add yourself.

This is a public build of [whisper-local](https://github.com/drajb/whisper-local), which is itself a fork of [whisper-key-local](https://github.com/PinW/whisper-key-local) by Pin Wang. The MIT license and those credits stay in [LICENSE](LICENSE). The long feature list from the upstream project is in [docs/upstream-readme.md](docs/upstream-readme.md).

Plain setup steps are in [INSTRUCTIONS.txt](INSTRUCTIONS.txt).

## What stays on your machine

- Your microphone audio is transcribed locally with Whisper. It is not uploaded for transcription.
- API keys, learned corrections, and a rewrite style guide are saved under `%APPDATA%\whisperkey` on Windows, or `~/.whisperkey` on macOS.
- This repository does not contain anyone's API key or personal writing guide. You add those after you install it.

## Install on Windows

You need Python 3.11 or newer.

```powershell
py -3 -m pip install -e .
py -3 -m whisper_key.main
```

Run those from this project folder.

The first launch downloads the Base speech model. That takes a few minutes once.

On macOS the same install works with `python3` instead of `py -3`.

## Choose a transcription model

Open the tray icon and choose **Settings...**. The **AI** tab is the first one.

| Model | Rough size | When to use it |
| --- | --- | --- |
| tiny | 75 MB | Fastest, more mistakes |
| base | 141 MB | Default. A good balance |
| small | 464 MB | Clearer, slower on CPU |
| medium | 1.4 GB | Better still. A GPU helps |
| large | several GB | Most accurate. Use a GPU |

Restart the app after you change the model. The new model downloads the first time you dictate with it.

Under the same **AI** tab you can set **Compute device** from the General tab to `cuda` if you have a supported GPU. CPU works without one.

## Add your own API key

Dictation does not need a key.

A key is only for the rewrite shortcuts: speak and have the sentence cleaned up, or highlight text and rewrite it. On the **AI** tab:

1. Paste an OpenAI API key. Use **Show** if you want to check it. The field is hidden by default.
2. Pick a rewrite model, such as `gpt-4.1-mini`.
3. Optional: a short style note, or **Edit full style guide** for a longer private file.
4. Save.

The key is written to `user_settings.yaml` on your PC. Do not commit that file, and do not paste the key into an issue.

If you would rather not use OpenAI, install [Ollama](https://ollama.com), run a model, and turn on **Use Ollama for local cleanup** on the same tab. That path does not need an API key.

## Learned corrections

If you fix a word by hand just after it is pasted, the app can remember that swap and apply it next time. A card appears at the top right of the screen when a new rule is saved.

Rules run from top to bottom. A later rule can undo an earlier one. That is how "send" can end up pasted as "save" if both directions get saved.

Open the list from the tray: **Learned corrections...**

Or:

```powershell
py -3 -m whisper_key.main --corrections
```

Delete a rule there if it is wrong. The change applies on the next dictation. You can also turn learning off under **Post-process** with **Remember words you fix by hand**.

## Everyday controls

- Hold or tap the record hotkey (see the tray cheat sheet) and speak into any text field.
- **Settings...** changes the model, key, and hotkeys.
- **Learned corrections...** reviews automatic word swaps.
- **Transcript history...** shows what was dictated.

Hotkey changes need a restart. Formatting changes apply on the next dictation.

## Credits

Copyright (c) 2025 Pin Wang, original whisper-key-local.
Copyright (c) 2026 Rohit Burani, whisper-local fork.
This public packaging adds a setup screen for models and API keys, and it ships without a private rewrite guide.
