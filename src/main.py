from src.listener import listen
from src.claims import extract_claims
from src.verifier import verify_claim
from src.report import print_report


def run_once():
    transcript = listen()
    if not transcript:
        return

    print("\nheard:", transcript)
    claims = extract_claims(transcript)
    print(f"found {len(claims)} claim(s)")

    results = []
    for c in claims:
        print("checking:", c)
        results.append(verify_claim(c))

    print_report(transcript, results)


def main():
    print("AI fact checker. Speak, and I'll check what you say.")
    print("Ctrl+C to quit.\n")
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            print("\nbye")
            break
        except Exception as e:
            # don't kill the whole loop for one bad request
            print("something went wrong:", e)


if __name__ == "__main__":
    main()