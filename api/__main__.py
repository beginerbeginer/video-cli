import argparse
from collections.abc import Sequence

import uvicorn

from api.app import create_app

# Why not --host を受け付ける: PC 内のファイルを扱う API なので、外部に公開できる口を作らない。
HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="video-gui", description="video-cli の GUI 用 API サーバーを起動する")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)

    uvicorn.run(create_app(), host=HOST, port=args.port)


if __name__ == "__main__":
    main()
