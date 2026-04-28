#!/bin/bash
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // ""')

# eval/exec によるコード実行
if echo "$cmd" | grep -qE '\beval\b|\bexec\b'; then
  echo "eval/exec は禁止されています" >&2
  exit 2
fi

# curl/wget の結果をシェルに流す
if echo "$cmd" | grep -qE '(curl|wget).+\|\s*(bash|sh|zsh)'; then
  echo "curl/wget のパイプ実行は禁止されています" >&2
  exit 2
fi

exit 0
