def format_id_number(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def verify_image_magic_bytes(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None