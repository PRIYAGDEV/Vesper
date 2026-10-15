import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.config import load_config
from src.transcriber import WhisperTranscriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WisprClone.Step2")


def main():
    parser = argparse.ArgumentParser(description="Step 2: Transcribe WAV audio file")
    parser.add_argument("wav_path", nargs="?", default="tests/output_test.wav", help="Path to WAV audio file")
    parser.add_argument("--model", default=None, help="Whisper model size (tiny.en, base.en, small.en)")
    parser.add_argument("--lang", default=None, help="Spoken language code (e.g. en)")
    args = parser.parse_args()

    wav_file = Path(args.wav_path)
    if not wav_file.exists():
        print(f"[ERROR] Audio file '{wav_file}' does not exist.")
        print("Please run 'step1_record.py' first or provide a valid WAV file path.")
        sys.exit(1)

    config = load_config()
    model_size = args.model or config.get("model_size", "base.en")
    language = args.lang or config.get("language", "en")
    vad_filter = config.get("vad_filter", True)

    print("=" * 60)
    print(f" Wispr Flow Clone - Step 2: Local Audio Transcription")
    print(f" File: {wav_file} | Model: {model_size} | Lang: {language}")
    print("=" * 60)

    transcriber = WhisperTranscriber(model_size=model_size)
    print("\n[INFO] Loading model and transcribing audio...")
    result = transcriber.transcribe(wav_file, language=language, vad_filter=vad_filter)

    print("\n" + "=" * 60)
    print(" TRANSCRIPTION RESULT:")
    print(f" '{result}'")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
