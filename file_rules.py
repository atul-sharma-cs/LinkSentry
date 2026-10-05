import re

# Extensions jo executable ya script files hoti hain - inhe email/download
# attachments mein dekhna hamesha extra suspicious hota hai
DANGEROUS_EXTENSIONS = {
    "exe", "scr", "bat", "cmd", "com", "pif", "vbs", "vbe", "js", "jse",
    "wsf", "wsh", "msi", "msp", "jar", "ps1", "ps1xml", "reg", "hta"
}

# Extensions jo commonly documents/media ke liye use hoti hain - agar inke
# saath ek dangerous extension bhi mile (jaise invoice.pdf.exe) to red flag hai
COMMON_DOCUMENT_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv",
    "jpg", "jpeg", "png", "gif", "mp3", "mp4", "zip", "rar"
}


def extract_file_features(filename: str, size: int, sha256: str) -> dict:
    parts = filename.rsplit(".", maxsplit=1)
    extension = parts[-1].lower() if len(parts) > 1 else ""

    # Double extension check: "invoice.pdf.exe" jaisa pattern dhoondo
    name_segments = filename.lower().split(".")
    has_double_extension = (
        len(name_segments) >= 3
        and name_segments[-1] in DANGEROUS_EXTENSIONS
        and any(seg in COMMON_DOCUMENT_EXTENSIONS for seg in name_segments[:-1])
    )

    features = {
        "filename": filename,
        "extension": extension,
        "size_bytes": size,
        "sha256": sha256,
        "is_dangerous_extension": extension in DANGEROUS_EXTENSIONS,
        "has_double_extension": has_double_extension,
        "has_suspicious_whitespace": bool(re.search(r"\s{2,}\.", filename)),
    }
    return features


def file_rule_based_score(features: dict) -> dict:
    score = 0
    reasons = []

    if features["is_dangerous_extension"]:
        score += 40
        reasons.append(f"File has an executable/script extension (.{features['extension']})")

    if features["has_double_extension"]:
        score += 40
        reasons.append("Filename uses a double extension to disguise its real type (e.g. invoice.pdf.exe)")

    if features["has_suspicious_whitespace"]:
        score += 10
        reasons.append("Filename uses unusual spacing before the extension, often used to hide the true file type")

    if features["size_bytes"] == 0:
        score += 5
        reasons.append("File is empty (0 bytes)")

    score = min(score, 100)
    return {"rule_score": score, "rule_reasons": reasons}