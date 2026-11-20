"""Form の検証で各操作が共通に使う部品。

validation/ の validator は「どの Form のどの項目か」を知らないので、
ここで ValidationError に Form のフィールド名（field）を付ける。
"""

from collections.abc import Iterator
from contextlib import contextmanager

from shared.errors import ValidationError
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import require_non_empty


@contextmanager
def form_field(field: str) -> Iterator[None]:
    # validator 側に field 引数を足さないのは、validation/ は Form を知らない層で、
    # 同じ validator が操作ごとに別の項目名（fps_raw / crf_raw など）で使われるため。
    try:
        yield
    except ValidationError as exc:
        if exc.field is not None:
            raise
        raise ValidationError(str(exc), field=field) from exc


def require_field(value: str, label: str, field: str) -> str:
    with form_field(field):
        return require_non_empty(value, label)


def validate_video_input_path(input_file: str, field: str = "input_file") -> None:
    require_field(input_file, "入力ファイル", field)
    with form_field(field):
        validate_input_file_exists(input_file)
        validate_video_file_extension(input_file)


def validate_output_path(output_file: str, field: str = "output_file") -> None:
    require_field(output_file, "出力ファイル", field)
    with form_field(field):
        validate_output_directory_exists(output_file)
