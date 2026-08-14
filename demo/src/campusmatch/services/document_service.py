class DocumentError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def normalize_markdown(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and not lines[-1]:
        lines.pop()

    if not any(line.strip() for line in lines):
        raise DocumentError("DOCUMENT_EMPTY", "材料为空，请上传文件或粘贴文字。")

    return "\n".join(lines)
