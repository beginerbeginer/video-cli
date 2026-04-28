from dataclasses import dataclass
from typing import Protocol

from ffmpeg.commands import (
    build_concat_copy_command,
    build_concat_reencode_command,
)


class ConcatCommandStrategy(Protocol):
    def build(self, concat_list_file: str, output_file: str) -> list[str]:
        ...


@dataclass(frozen=True)
class CopyConcatStrategy:
    def build(self, concat_list_file: str, output_file: str) -> list[str]:
        return build_concat_copy_command(concat_list_file, output_file)


@dataclass(frozen=True)
class ReencodeConcatStrategy:
    def build(self, concat_list_file: str, output_file: str) -> list[str]:
        return build_concat_reencode_command(concat_list_file, output_file)


def choose_concat_strategy(compatible: bool) -> ConcatCommandStrategy:
    return CopyConcatStrategy() if compatible else ReencodeConcatStrategy()
