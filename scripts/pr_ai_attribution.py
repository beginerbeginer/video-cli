"""PR に含まれるコミットの Co-Authored-By から、使った AI ツール / モデルの区画を PR 本文に書き込む。
あわせて、Claude Code が本文に付けるセッションの URL の行を取り除く（issue #120）。

使い方: python scripts/pr_ai_attribution.py <git log -z の出力ファイル> <今の PR 本文ファイル>
新しい PR 本文を stdout に出す。GitHub への読み書きはワークフロー側の gh が行う。
"""

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

START_MARKER = "<!-- ai-attribution:start -->"
END_MARKER = "<!-- ai-attribution:end -->"

# Why not `git interpret-trailers --parse`: 1 コミットずつ git を呼ぶことになり、
# テストでも git リポジトリが要る。トレーラー 1 種類だけなら行単位の正規表現で足りる。
_COAUTHOR_RE = re.compile(r"^co-authored-by:\s*(?P<name>.+?)\s*<[^>]*>\s*$", re.IGNORECASE | re.MULTILINE)

# Why not str.find: 本文中で `<!-- ai-attribution:start -->` のようにマーカーを引用すると、
# その引用を区画の始まりと取り違えて本文を壊す。行頭から行末までマーカーだけの行に限る。
_SECTION_RE = re.compile(
    rf"^[ \t]*{re.escape(START_MARKER)}[ \t]*\r?$.*?^[ \t]*{re.escape(END_MARKER)}[ \t]*(?=\r?$)",
    re.MULTILINE | re.DOTALL,
)

# Why not 本文中の URL もすべて消す: ルールを説明する文などで URL に触れた箇所まで書き換えてしまう。
# Claude Code が末尾に付けるのは URL だけの行なので、その行（と直前の空行）だけを消す。
_SESSION_URL_LINE_RE = re.compile(
    r"(?:^[ \t]*\r?\n)*^[ \t]*https://claude\.ai/code/session_\S*[ \t]*(?:\r?\n|\Z)",
    re.MULTILINE,
)


@dataclass
class Attribution:
    counts: Counter = field(default_factory=Counter)
    commits_without_trailer: int = 0


def extract_coauthors(messages: list[str]) -> Attribution:
    attribution = Attribution()
    for message in messages:
        if not message.strip():
            continue
        # Why not Counter.update(findall): 1 コミット内の重複トレーラーを 2 件と数えてしまう
        names = dict.fromkeys(m.group("name") for m in _COAUTHOR_RE.finditer(message))
        if not names:
            attribution.commits_without_trailer += 1
        attribution.counts.update(names.keys())
    return attribution


def render_section(attribution: Attribution) -> str:
    lines = [
        START_MARKER,
        "## 使用した AI ツール / モデル",
        "",
        "_この区画は GitHub Actions が各コミットの `Co-Authored-By` から自動で書き込みます。"
        "手で編集しても次の更新で上書きされます。_",
        "",
    ]
    if attribution.counts:
        lines += [f"- {name}（{count} コミット）" for name, count in attribution.counts.items()]
    else:
        lines.append("- なし（どのコミットにも `Co-Authored-By` トレーラーがありません）")
    if attribution.counts and attribution.commits_without_trailer:
        lines += ["", f"トレーラーの無いコミット: {attribution.commits_without_trailer} 件"]
    lines.append(END_MARKER)
    return "\n".join(lines)


def replace_section(body: str, section: str) -> str:
    match = _SECTION_RE.search(body)
    if match:
        newline = "\r\n" if "\r\n" in match.group(0) else "\n"
        return body[: match.start()] + section.replace("\n", newline) + body[match.end() :]
    stripped = body.rstrip()
    return f"{stripped}\n\n{section}\n" if stripped else f"{section}\n"


def remove_session_urls(body: str) -> str:
    return _SESSION_URL_LINE_RE.sub("", body)


def build_new_body(git_log: str, body: str) -> str:
    section = render_section(extract_coauthors(git_log.split("\0")))
    return replace_section(remove_session_urls(body), section)


def main(argv: list[str]) -> int:
    git_log_path, body_path = argv
    git_log = Path(git_log_path).read_text(encoding="utf-8")
    body = Path(body_path).read_text(encoding="utf-8")
    sys.stdout.write(build_new_body(git_log, body))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
