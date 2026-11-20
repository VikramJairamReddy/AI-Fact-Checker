import os

import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENGINE = "groq"  # or "google" if groq acts up
LANGUAGE = "en"  # stops whisper guessing spanish for short english phrases

r = sr.Recognizer()
r.pause_threshold = 0.8
r.non_speaking_duration = 0.5
r.dynamic_energy_threshold = False

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("no GROQ_API_KEY found, check your .env")
        _client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    return _client


def groq_transcribe(audio):
    wav = audio.get_wav_data(convert_rate=16000, convert_width=2)
    res = get_client().audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=("speech.wav", wav, "audio/wav"),
        language=LANGUAGE,
        response_format="text",
    )
    text = res if isinstance(res, str) else res.text
    return text.strip()


def transcribe(audio):
    try:
        if ENGINE == "groq":
            return groq_transcribe(audio)
        return r.recognize_google(audio, language=LANGUAGE)
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("transcription failed:", e)
        return ""


def start_background(audio_q):
    # keeps listening forever, every phrase (split on pauses) goes into the queue
    mic = sr.Microphone()
    with mic as source:
        print("calibrating, stay quiet...")
        r.adjust_for_ambient_noise(source, duration=1)

    def on_phrase(recognizer, audio):
        audio_q.put(audio)

    # phrase_time_limit so a long ramble still gets cut into chunks
    stop = r.listen_in_background(mic, on_phrase, phrase_time_limit=15)
    return stop


if __name__ == "__main__":
    # quick test: speak, see the text
    import queue
    q = queue.Queue()
    stop = start_background(q)
    print("listening, ctrl+c to quit")
    try:
        while True:
            print(">>", transcribe(q.get()))
    except KeyboardInterrupt:
        stop(wait_for_stop=False)