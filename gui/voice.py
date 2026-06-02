import json
import queue
import threading

import sounddevice as sd
import vosk
from rapidfuzz import fuzz, process

from core.config import get as get_config

KNOWN_DESCRIPTIONS = [
    "refuel",
    "re-fuel",
    "fuel",
    "repair",
    "repairs",
    "rearm",
    "fee",
    "contract",
    "trade",
    "trading",
    "cargo",
    "bounty",
    "mercenary",
    "salvage",
    "mining",
    "delivery",
]

WAKE_WORD_VARIANTS = ["fin", "finn", "pin", "bin", "been", "then"]

FILLER_WORDS = {"a", "the", "an", "and", "of", "to", "my", "some"}

MATCH_THRESHOLD = 70

ONES = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def words_to_number(words):
    tokens = words.lower().split()
    total = 0
    current = 0
    for token in tokens:
        if token in ONES:
            current += ONES[token]
        elif token in TENS:
            current += TENS[token]
        elif token == "hundred":
            current *= 100
        elif token == "thousand":
            total += current * 1000
            current = 0
        elif token == "million":
            total += current * 1000000
            current = 0
        else:
            try:
                current += int(token)
            except ValueError:
                pass
    return total + current


def fuzzy_match_description(word):
    result = process.extractOne(word, KNOWN_DESCRIPTIONS, scorer=fuzz.ratio)
    if result and result[1] >= MATCH_THRESHOLD:
        return result[0]
    return word


def clean_description(words):
    filtered = [w for w in words if w not in FILLER_WORDS]
    result = []
    for w in filtered:
        match = process.extractOne(w, KNOWN_DESCRIPTIONS, scorer=fuzz.ratio)
        if match and match[1] >= MATCH_THRESHOLD:
            result.append(match[0])
        else:
            return None  # unknown word, reject the command
    return " ".join(result).strip() if result else None


def contains_wake_word(words):
    wake_word = get_config("wake_word")
    all_variants = WAKE_WORD_VARIANTS + [wake_word]
    for w in words:
        if process.extractOne(w, all_variants, scorer=fuzz.ratio)[1] >= MATCH_THRESHOLD:
            return True
    return False


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

        if not contains_wake_word(words):
            return None

        try:
            t_type = None
            type_idx = None
            for i, w in enumerate(words):
                if (
                    fuzz.ratio(w, "expense") >= MATCH_THRESHOLD
                    or fuzz.ratio(w, "expenses") >= MATCH_THRESHOLD
                    or fuzz.ratio(w, "expanse") >= MATCH_THRESHOLD
                ):
                    t_type = "expense"
                    type_idx = i
                    break
                elif fuzz.ratio(w, "income") >= MATCH_THRESHOLD:
                    t_type = "income"
                    type_idx = i
                    break

            if t_type is None or type_idx is None:
                return None

            rest = words[type_idx + 1 :]

            for_idx = None
            for i, w in enumerate(rest):
                if fuzz.ratio(w, "for") >= MATCH_THRESHOLD or w == "or":
                    for_idx = i
                    break

            if for_idx is not None:
                desc_words = rest[:for_idx]
                amount_words = rest[for_idx + 1 :]
            else:
                desc_words = rest[:-1]
                amount_words = rest[-1:]

            desc = clean_description(desc_words)
            amount = words_to_number(" ".join(amount_words))

            if not desc or not amount:
                return None

            return {"type": t_type, "desc": desc, "amount": amount}

        except (IndexError, ValueError):
            return None

    def _callback(self, indata, frames, time, status):
        self._q.put(bytes(indata))

    def _listen(self):
        print("_listen thread running")
        rec = vosk.KaldiRecognizer(self.model, 16000)
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):
            print("Microphone stream open")
            while self.active:
                data = self._q.get()
                if not data:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    print(f"Heard: '{text}'")
                    if text:
                        command = self._parse_command(text)
                        print(f"Parsed: {command}")
                        if command:
                            self.on_command(command)

            # flush final result when PTT released
            result = json.loads(rec.FinalResult())
            text = result.get("text", "")
            print(f"Final heard: '{text}'")
            if text:
                command = self._parse_command(text)
                print(f"Final parsed: {command}")
                if command:
                    self.on_command(command)

    def start(self):
        if self.active:
            return
        self.active = True
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        print("Voice listening started")

    def stop(self):
        if not self.active:
            return
        self.active = False
        self._q.put(b"")  # ← unblock the queue so the thread can exit cleanly
        print("Voice listening stopped")
