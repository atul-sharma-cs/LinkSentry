import time

# Gemini kabhi kabhi temporarily overloaded ho jata hai (503 UNAVAILABLE) ya
# rate-limit lagata hai (429 RESOURCE_EXHAUSTED). Ye dono "transient" errors
# hain -- matlab thodi der baad retry karne se aksar sahi ho jate hain.
# Isliye hum turant user ko error dikhane ke bajaye, pehle 2-3 baar khud
# retry karte hain, har baar thoda zyada wait karke (exponential backoff).

TRANSIENT_MARKERS = ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded"]


def is_transient_error(error: Exception) -> bool:
    error_str = str(error)
    return any(marker in error_str for marker in TRANSIENT_MARKERS)


def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.5):
    """
    func: ek zero-argument callable jo actual API call karta hai.
    Transient errors (503/429) par exponential backoff ke saath retry karta hai.
    Agar sab retries fail ho jayein, to last exception raise kar deta hai.
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if is_transient_error(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 1.5s, 3s, 6s ...
                time.sleep(delay)
                continue
            raise

    raise last_exception