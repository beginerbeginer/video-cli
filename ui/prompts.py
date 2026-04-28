from collections.abc import Sequence

from shared.errors import ValidationError


def ask_text(message: str, default: str | None = None) -> str:
    prompt = message
    if default is not None:
        prompt += f" [default: {default}]"
    prompt += "\n> "

    value = input(prompt).strip()
    if value == "" and default is not None:
        return default
    return value


def ask_menu(message: str, choices: Sequence[tuple[str, str]]) -> str:
    print(message)
    for index, (label, _) in enumerate(choices, start=1):
        print(f"{index}. {label}")

    while True:
        raw = input("> ").strip()
        try:
            selected = int(raw)
        except ValueError:
            print("番号で入力してください。")
            continue

        if 1 <= selected <= len(choices):
            return choices[selected - 1][1]

        print("選択肢の範囲内で入力してください。")


def require_non_empty(value: str, field_name: str) -> str:
    if value.strip() == "":
        raise ValidationError(f"{field_name}は空にできません。")
    return value
