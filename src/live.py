import json
import queue
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.listener import start_background, transcribe
from src.claims import extract_claims
from src.verifier import verify_claim
from src.report import print_report

# say corrections out loud (mac only). OFF by default, because the mic will
# hear the computer talking and try to fact check it. use headphones if you turn this on
SPEAK_ALERTS = False

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

# whisper makes these up when it hears silence or noise
JUNK = {"thank you", "thanks for watching", "you", "bye", "okay", "yeah"}

audio_q = queue.Queue()
text_q = queue.Queue()

all_results = []
heard = []      # every phrase, for the final report
seen = set()    # so the same claim isn't checked twice

# 3 workers max, more than that just hits the groq limit faster
pool = ThreadPoolExecutor(max_workers=3)
print_lock = threading.Lock()


def transcriber():
    while True:
        audio = audio_q.get()
        text = transcribe(audio)
        if len(text.split()) < 4:
            continue
        if text.lower().strip(" .!?,") in JUNK:
            continue
        print(f"\n[heard] {text}")
        text_q.put(text)


def show(res):
    verdict = res["verdict"]
    has_source = len(res["sources"]) > 0

    if verdict in ("false", "partially_true") and has_source:
        color = RED if verdict == "false" else YELLOW
        label = "FALSE" if verdict == "false" else "PARTLY TRUE"
        print(f"\n{color}!! {label}: {res['claim']}{RESET}")
        print(f"   {res['explanation']}")
        if res["correct_fact"]:
            print(f"   Truth: {res['correct_fact']}")
        print(f"   Source: {res['sources'][0]['title']} - {res['sources'][0]['url']}")
        if SPEAK_ALERTS and res["correct_fact"]:
            subprocess.Popen(["say", "Correction. " + res["correct_fact"]])
    elif verdict in ("false", "partially_true"):
        # model says wrong but pointed at no evidence, don't state it as fact
        print(f"\n{YELLOW}?? possibly wrong (no source): {res['claim']}{RESET}")
    elif verdict == "true":
        print(f"{GREEN}ok: {res['claim']}{RESET}")
    else:
        print(f"-- couldn't verify: {res['claim']}")


def check_one(claim):
    try:
        res = verify_claim(claim)
    except Exception as e:
        print("verify failed:", e)
        return
    with print_lock:
        all_results.append(res)
        show(res)


def checker():
    while True:
        text = text_q.get()
        context = " ".join(heard[-3:])
        heard.append(text)

        try:
            claims = extract_claims(text, context)
        except Exception as e:
            print("claim extraction failed:", e)
            continue

        for c in claims:
            key = c.lower().strip(". ")
            if key in seen:
                continue
            seen.add(key)
            pool.submit(check_one, c)  # runs in the background, don't wait


def main():
    print("LIVE fact checker. Ctrl+C to stop and get the summary.\n")
    stop = start_background(audio_q)

    threading.Thread(target=transcriber, daemon=True).start()
    threading.Thread(target=checker, daemon=True).start()

    print("listening...")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop(wait_for_stop=False)
        time.sleep(3)  # let checks that are still running finish
        print("\nstopped.")
        print_report(" ".join(heard), all_results)

        name = f"session_{int(time.time())}.json"
        with open(name, "w") as f:
            json.dump({"transcript": heard, "results": all_results}, f, indent=2)
        print("saved to", name)


if __name__ == "__main__":
    main()