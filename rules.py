import re
from urllib.parse import urlparse
import tldextract

# suffix_list_urls=() -> internet se live suffix list fetch karne ki koshish
# nahi karega, bundled offline snapshot use karega. Isse faster hai aur
# koi network warning bhi nahi aayegi.
_TLD_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=())

# Known URL shortening services jo phishing mein misuse hote hain
SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "is.gd", "buff.ly", "adf.ly", "shorte.st", "rb.gy"
}

# Suspicious keywords jo phishing URLs/pages mein common hote hain
SUSPICIOUS_KEYWORDS = [
    "verify", "secure", "account", "update", "confirm", "login",
    "signin", "banking", "suspend", "locked", "urgent", "validate",
    "password", "billing", "webscr", "ebayisapi", "recover"
]

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)$"
)


def extract_lexical_features(url: str) -> dict:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url  # parsing ke liye scheme zaroori hai

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    ext = _TLD_EXTRACTOR(url)
    registered_domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain

    features = {}

    # 1. Basic length checks
    features["url_length"] = len(url)
    features["hostname_length"] = len(hostname)

    # 2. Special character counts
    features["count_dots"] = hostname.count(".")
    features["count_hyphens"] = hostname.count("-")
    features["has_at_symbol"] = "@" in url

    # 3. IP address instead of domain name (bada red flag)
    features["has_ip_address"] = bool(IP_PATTERN.match(hostname))

    # 4. HTTPS check
    features["uses_https"] = parsed.scheme == "https"

    # 5. URL shortener check
    features["is_shortened"] = registered_domain.lower() in SHORTENER_DOMAINS

    # 6. Subdomain count (zyada subdomains = suspicious)
    subdomain_parts = ext.subdomain.split(".") if ext.subdomain else []
    features["subdomain_count"] = len([s for s in subdomain_parts if s])

    # 7. Suspicious keyword match (URL ke andar hi keyword dhoondo)
    url_lower = url.lower()
    matched_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in url_lower]
    features["suspicious_keyword_count"] = len(matched_keywords)
    features["matched_keywords"] = matched_keywords

    # 8. Digit-to-length ratio (algorithmically generated domains me digits zyada hote hain)
    digit_count = sum(c.isdigit() for c in hostname)
    features["digit_ratio"] = round(digit_count / len(hostname), 3) if hostname else 0

    return features


def rule_based_score(features: dict) -> dict:
    score = 0
    reasons = []

    if features["has_ip_address"]:
        score += 30
        reasons.append("URL uses a raw IP address instead of a domain name")

    if features["has_at_symbol"]:
        score += 20
        reasons.append("URL contains an '@' symbol, often used to hide the real destination")

    if not features["uses_https"]:
        score += 10
        reasons.append("Site does not use HTTPS")

    if features["is_shortened"]:
        score += 15
        reasons.append("This is a shortened URL, the real destination may be hidden")

    if features["subdomain_count"] >= 3:
        score += 15
        reasons.append("URL has an unusually high number of subdomains")

    if features["suspicious_keyword_count"] >= 2:
        score += 20
        reasons.append(f"Suspicious keywords found: {', '.join(features['matched_keywords'])}")

    if features["url_length"] > 75:
        score += 10
        reasons.append("URL is unusually long")

    if features["digit_ratio"] > 0.3:
        score += 10
        reasons.append("Hostname has a high ratio of digits")

    score = min(score, 100)

    return {"rule_score": score, "rule_reasons": reasons}