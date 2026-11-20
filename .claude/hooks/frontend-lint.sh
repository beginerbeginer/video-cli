#!/bin/bash
# Claude が frontend/ のファイルを編集した直後に整形と自動修正をかけ、直しきれない違反を Claude に返す。
# 後から lint をまとめて走らせる運用だと違反が積み上がってから気付くので、書いたその場で止める。
input=$(cat)
file=$(echo "$input" | jq -r '.tool_input.file_path // ""')
frontend="$CLAUDE_PROJECT_DIR/frontend"

case "$file" in
  "$frontend"/node_modules/* | "$frontend"/dist/*) exit 0 ;;
  "$frontend"/*) ;;
  *) exit 0 ;;
esac

# 削除されたファイルや、依存を入れる前（npm install 前）は何もしない
[ -f "$file" ] || exit 0
[ -d "$frontend/node_modules" ] || exit 0

cd "$frontend" || exit 0

npx --no-install prettier --write --ignore-unknown --log-level warn "$file" >/dev/null 2>&1

case "$file" in
  *.ts | *.tsx)
    # --no-warn-ignored: fixtures など lint 対象外のファイルで「無視しました」の警告を出さず、--max-warnings 0 に引っかけない
    if ! output=$(npx --no-install eslint --fix --max-warnings 0 --no-warn-ignored "$file" 2>&1); then
      echo "ESLint の自動修正で直しきれない違反があります。ルールを外さずにコードを直してください。" >&2
      echo "$output" >&2
      exit 2
    fi
    ;;
esac

exit 0
