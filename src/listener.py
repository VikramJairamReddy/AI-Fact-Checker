import os

import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENGINE = "groq"  # or "google" if groq acts up

r = sr.Recognizer()
r.pause_threshold = 0.8
r.non_speaking_duration = 0.5
r.dynamic_energy_threshold = False

_client = None
calibrated = False


def get_client():
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("no GROQ_API_KEY found, check your .env")
        _client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    return _client


def calibrate():
    # only do this once, it was adding a second to every listen
    global calibrated
    with sr.Microphone() as source:
        print("calibrating, stay quiet...")
        r.adjust_for_ambient_noise(source, duration=1)
    calibrated = True


def groq_transcribe(audio):
    wav = audio.get_wav_data(convert_rate=16000, convert_width=2)
    res = get_client().audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=("speech.wav", wav, "audio/wav"),
        response_format="text",
    )
    text = res if isinstance(res, str) else res.text
    return text.strip()


def listen():
    if not calibrated:
        calibrate()

    with sr.Microphone() as source:
        print("listening...")
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=60)
        except sr.WaitTimeoutError:
            print("didn't hear anything")
            return ""

    print("transcribing...")
    try:
        if ENGINE == "groq":
            return groq_transcribe(audio)
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        print("couldn't understand that")
        return ""
    except Exception as e:
        print("transcription failed:", e)
        return ""


if __name__ == "__main__":
    while True:
        print("\n>>", listen())