import re
from typing import Dict, List


def remove_repetitive_hallucinations(text: str) -> str:
    """Strip Whisper silence/noise hallucinations like 'ॐ' loops and repeated phrases."""
    if not text:
        return ""
    # Strip chant loops like ॐ ॐ
    text = re.sub(r"[ॐ \t]{2,}", " ", text)
    # Deduplicate repeated identical words (e.g. 'test test test' -> 'test')
    text = re.sub(r"(\b\w+\b[,.?!]?)(?:\s+\1){2,}", r"\1", text, flags=re.IGNORECASE)
    # Deduplicate repeated phrases (e.g. 'what is, what is, what is' -> 'what is')
    text = re.sub(r"(\b\w+\s+\w+\b[,.?!]?)(?:\s+\1){2,}", r"\1", text, flags=re.IGNORECASE)
    # Normalize multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# Spoken commands mapping to punctuation / whitespace
SPOKEN_COMMANDS: List[tuple[re.Pattern, str]] = [
    # New paragraph and new line
    (re.compile(r"\b(?:new paragraph|next paragraph)\b", re.IGNORECASE), "\n\n"),
    (re.compile(r"\b(?:new line|newline|next line)\b", re.IGNORECASE), "\n"),

    # Punctuation commands
    (re.compile(r"\b(?:full stop|period)\b", re.IGNORECASE), "."),
    (re.compile(r"\b(?:question mark)\b", re.IGNORECASE), "?"),
    (re.compile(r"\b(?:exclamation mark|exclamation point)\b", re.IGNORECASE), "!"),
    (re.compile(r"\b(?:comma)\b", re.IGNORECASE), ","),
    (re.compile(r"\b(?:colon)\b", re.IGNORECASE), ":"),
    (re.compile(r"\b(?:semicolon)\b", re.IGNORECASE), ";"),
    (re.compile(r"\b(?:open quote|start quote)\b", re.IGNORECASE), '"'),
    (re.compile(r"\b(?:close quote|end quote)\b", re.IGNORECASE), '"'),
    (re.compile(r"\b(?:open parenthesis|open paren)\b", re.IGNORECASE), "("),
    (re.compile(r"\b(?:close parenthesis|close paren)\b", re.IGNORECASE), ")"),
    (re.compile(r"\b(?:dash|hyphen)\b", re.IGNORECASE), "-"),
]

# Filler words / phrases
FILLER_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:um+|uh+|uhm+|umm+|er+|ah+|erm+)\b[,.]?", re.IGNORECASE),
    re.compile(r"\b(?:you know what i mean|you know|i mean to say|i mean)\b[,.]?", re.IGNORECASE),
]


def remove_filler_words(text: str) -> str:
    """Remove hesitations and common filler words/sounds."""
    cleaned = text
    for pattern in FILLER_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    # Handle standalone "like" when used as filler: e.g. ", like," or "I was like um"
    cleaned = re.sub(r"(?<=[,\s])like(?=[,\s])", "", cleaned, flags=re.IGNORECASE)
    # Normalize spaces after removing filler words
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned


def apply_spoken_commands(text: str) -> str:
    """Convert spoken commands like 'new line' or 'period' into actual characters."""
    result = text
    for pattern, replacement in SPOKEN_COMMANDS:
        result = pattern.sub(replacement, result)
    return result


def fix_punctuation_and_capitalization(text: str) -> str:
    """Fix spacing around punctuation and capitalize sentences."""
    if not text:
        return ""

    # Fix space before punctuation (e.g. "word ." -> "word.")
    text = re.sub(r"\s+([.,!?:;])", r"\1", text)

    # Ensure space after punctuation if followed by a letter (e.g. "word.word" -> "word. word")
    text = re.sub(r"([.,!?:;])([A-Za-z])", r"\1 \2", text)

    # Fix quotes spacing: '" word "' -> '"word"'
    text = re.sub(r'"\s+', '"', text)
    text = re.sub(r'\s+"', '"', text)

    # Clean whitespace around newlines
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Capitalize the start of sentences
    def capitalize_match(match: re.Match) -> str:
        prefix = match.group(1)
        char = match.group(2)
        return prefix + char.upper()

    text = re.sub(r"(^|[.!?\n]\s*)([a-z])", capitalize_match, text)

    return text.strip()


def apply_writing_style(text: str, style: str = "casual") -> str:
    """Format text based on Wispr Flow writing style modes."""
    if not text or style == "casual":
        return text

    if style == "bullet_points":
        lines = re.split(r"\b(?:bullet point|bullet|point|item|next|firstly|secondly|thirdly)\b", text, flags=re.IGNORECASE)
        bullets = [f"  {line.strip()}" for line in lines if line.strip()]
        if len(bullets) > 1:
            return "\n".join(bullets)
        return text

    if style == "professional":
        replacements = [
            (r"\bgonna\b", "going to"),
            (r"\bwanna\b", "want to"),
            (r"\bkinda\b", "somewhat"),
            (r"\bya\b", "yes"),
            (r"\byep\b", "yes"),
            (r"\bnope\b", "no"),
            (r"\bbtw\b", "by the way"),
            (r"\basap\b", "as soon as possible"),
        ]
        res = text
        for pat, rep in replacements:
            res = re.sub(pat, rep, res, flags=re.IGNORECASE)
        return res

    if style == "code":
        res = re.sub(r"\bcamel case (\w+)\s+(\w+)\b", lambda m: m.group(1).lower() + m.group(2).capitalize(), text, flags=re.IGNORECASE)
        res = re.sub(r"\bsnake case (\w+)\s+(\w+)\b", lambda m: f"{m.group(1).lower()}_{m.group(2).lower()}", res, flags=re.IGNORECASE)
        res = re.sub(r"\b(?:const|let|var|def|class|function|import|return|await|async)\b", lambda m: f"`{m.group(0)}`", res)
        return res

    return text


def clean_transcript(
    text: str,
    cleanup_filler: bool = True,
    spoken_commands: bool = True,
    style: str = "casual"
) -> str:
    """Full transcript cleanup pipeline with customizable writing style."""
    if not text:
        return ""

    result = text

    if spoken_commands:
        result = apply_spoken_commands(result)

    if cleanup_filler:
        result = remove_filler_words(result)

    result = remove_repetitive_hallucinations(result)
    result = fix_punctuation_and_capitalization(result)
    result = apply_writing_style(result, style=style)
    return result
