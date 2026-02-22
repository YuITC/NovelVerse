"""Translation service: OpenCC (Traditional→Simplified Chinese) and Gemini (Chinese→Vietnamese)."""


def translate_opencc(text: str) -> str:
    """Convert Traditional Chinese to Simplified Chinese using OpenCC.

    This is a fast, free, offline conversion — useful as a pre-processing step
    or as a quick (lower quality) option for uploaders.
    """
    try:
        import opencc
        converter = opencc.OpenCC("t2s")  # Traditional → Simplified
        return converter.convert(text)
    except ImportError:
        raise RuntimeError("opencc-python-reimplemented is not installed")


def translate_gemini(text: str, api_key: str) -> str:
    """Translate Chinese text to Vietnamese using Google Gemini API (sync)."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Translate the following Chinese web novel chapter to Vietnamese. "
            "Preserve the original formatting, paragraph breaks, and dialogue. "
            "Do not add any commentary or notes — output only the translated text.\n\n"
            f"{text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        raise RuntimeError("google-generativeai is not installed")
