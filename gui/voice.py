import json
import queue
import threading

import sounddevice as sd
import vosk

from core.config import get as get_config


class VoiceListener:
    def __init__(self, on_command):
        self.on_command = on_command
        self.active = False
        self._thread = None
        self._q = queue.Queue()
        model_path = "vosk-model-small-en-us-0.15"
        self.model = vosk.Model(model_path)

    def _parse_command(self, text):
        words = text.lower().split()
        wake_word = get_config("wake_word")

        if wake_word not in words:
            return None

        try:
            wake_idx = words.index(wake_word)
            # expect: fin log expense/income <desc...> for <amount>
            if words[wake_idx + 1] != "log":
                return None

            t_type = words[wake_idx + 2]
            if t_type not in ("income", "expense"):
                return None

            # find "for" to split description and amount
            rest = words[wake_idx + 3 :]
            if "for" not in rest:
                return None

            for_idx = rest.index("for")
            desc = " ".join(rest[:for_idx]).strip()
            amount_str = rest[for_idx + 1]
            amount = int(float(amount_str))

            if not desc or not amount:
                return None

            return {"type": t_type, "desc": desc, "amount": amount}

        except (IndexError, ValueError):
            return None

    def _callback(self, indata, frames, time, status):
        self._q.put(bytes(indata))

    def _listen(self):
        rec = vosk.KaldiRecognizer(self.model, 16000)
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):
            while self.active:
                data = self._q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        command = self._parse_command(text)
                        if command:
                            self.on_command(command)

    def start(self):
        self.active = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self.active = False
