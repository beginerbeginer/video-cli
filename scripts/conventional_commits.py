"""PR タイトルとコミットの 1 行目が Conventional Commits の形（`種類: 要約`）かを確かめる。

使い方:
  python scripts/conventional_commits.py title "<PR タイトル>"   # 違えば終了コード 1
  python scripts/conventional_commits.py commits <git log -z の出力ファイル>  # 違っても警告だけ

結果は GitHub Actions の注釈（::error / ::warning）として stdout に出す。
"""

import re
import sys
from pathlib import Path

# 種類ごとのバージョンの上げ方は release-please の既定と同じ（CLAUDE.md の「リリースのルール」）。
ALLOWED_TYPES = ("feat", "fix", "perf", "refactor", "test", "docs", "ci", "build", "chore", "style", "revert")

# Why not commitlint（npm）: Python だけのリポジトリに Node の依存と設定ファイルを増やしたくない。
# 1 行目の形を見るだけなら正規表現 1 つで足りる。
_HEADER_RE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()\s][^()]*)\))?!?: (?P<subject>\S.*)$")

_FORMAT_HINT = "`種類: 要約` の形にしてください（例: `feat: 動画の分割機能を追加する`）。種類: " + ", ".join(
    ALLOWED_TYPES
)

# Why not 本文のどこかに文字列があれば警告: ルールを説明するコミットで `Claude-Session:` に触れただけでも
# 警告になる。トレーラーは行頭に書かれるので、行頭のものだけを見る。
_SESSION_TRAILER_RE = re.compile(r"^claude-session:", re.IGNORECASE | re.MULTILINE)

_SESSION_TRAILER_HINT = (
    "`Claude-Session:` のトレーラーは付けないでください（公開リポジトリにセッションの URL を残さないため。issue #120）"
)


def check_header(header: str) -> str | None:
    """形が正しければ None、違えば理由を返す。"""
    header = header.strip()
    match = _HEADER_RE.match(header)
    if not match:
        return f"Conventional Commits の形ではありません。{_FORMAT_HINT}"
    if match.group("type") not in ALLOWED_TYPES:
        return f"種類 `{match.group('type')}` は使えません。{_FORMAT_HINT}"
    return None


def check_commits(git_log: str) -> list[tuple[str, str]]:
    """git log -z の出力から、形の違うコミットの (1 行目, 理由) を返す。"""
    problems = []
    for message in git_log.split("\0"):
        if not message.strip():
            continue
        header = message.strip().splitlines()[0]
        error = check_header(header)
        if error:
            problems.append((header, error))
    return problems


def find_session_trailers(git_log: str) -> list[str]:
    """git log -z の出力から、`Claude-Session:` トレーラーのあるコミットの 1 行目を返す。"""
    return [
        message.strip().splitlines()[0]
        for message in git_log.split("\0")
        if message.strip() and _SESSION_TRAILER_RE.search(message)
    ]


def _check_title(title: str) -> int:
    error = check_header(title)
    if error:
        print(f"::error title=PR タイトル::{title} — {error}")
        return 1
    print(f"PR タイトル OK: {title}")
    return 0


def _check_commits(log_path: str) -> int:
    git_log = Path(log_path).read_text(encoding="utf-8")
    problems = check_commits(git_log)
    session_commits = find_session_trailers(git_log)
    # Why not 失敗にする: 既存の PR の古いコミットを書き換え（force-push）させたくない。
    # PR はマージコミットで取り込むので、release-please が読むのは PR タイトルではなく各コミット。
    # 形の違うコミットはリリースに載らないので、気づけるよう警告は出す。
    for header, error in problems:
        print(f"::warning title=コミットメッセージ::{header} — {error}")
    for header in session_commits:
        print(f"::warning title=Claude-Session トレーラー::{header} — {_SESSION_TRAILER_HINT}")
    if not problems and not session_commits:
        print("コミットメッセージ OK")
    return 0


def main(argv: list[str]) -> int:
    command, value = argv
    if command == "title":
        return _check_title(value)
    if command == "commits":
        return _check_commits(value)
    raise SystemExit(f"不明なサブコマンド: {command}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
