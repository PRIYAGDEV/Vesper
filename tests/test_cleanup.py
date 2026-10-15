import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.cleanup import clean_transcript, remove_filler_words, apply_spoken_commands


def test_filler_removal():
    raw = "I was um thinking that uh maybe we should go."
    cleaned = clean_transcript(raw, cleanup_filler=True, spoken_commands=False)
    assert "um" not in cleaned and "uh" not in cleaned
    assert cleaned == "I was thinking that maybe we should go."
    print("[PASS] Filler words removal test passed.")


def test_spoken_commands():
    raw = "hello comma how are you question mark new line i am fine period"
    cleaned = clean_transcript(raw, cleanup_filler=False, spoken_commands=True)
    expected = "Hello, how are you?\nI am fine."
    assert cleaned == expected, f"Expected '{expected}', got '{cleaned}'"
    print("[PASS] Spoken commands test passed.")


def test_paragraph_and_capitalization():
    raw = "first paragraph new paragraph second paragraph with um filler words period"
    cleaned = clean_transcript(raw, cleanup_filler=True, spoken_commands=True)
    expected = "First paragraph\n\nSecond paragraph with filler words."
    assert cleaned == expected, f"Expected '{expected}', got '{cleaned}'"
    print("[PASS] Paragraph and capitalization test passed.")


if __name__ == "__main__":
    test_filler_removal()
    test_spoken_commands()
    test_paragraph_and_capitalization()
