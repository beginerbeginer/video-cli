# Changelog

## [0.4.0](https://github.com/beginerbeginer/video-cli/compare/v0.3.0...v0.4.0) (2026-11-20)


### 新機能

* **api:** FastAPI の雛形と video-gui 起動コマンドを作る ([a031725](https://github.com/beginerbeginer/video-cli/commit/a0317253791cd209cd4a5f4b854496e4dc92cf46))
* FFmpeg の処理進捗をプログレスバーで表示する ([#47](https://github.com/beginerbeginer/video-cli/issues/47)) ([e22cb27](https://github.com/beginerbeginer/video-cli/commit/e22cb27b385cb7a19203ceecbfd346d54563876a))
* Web GUI を追加する（Flask + シングルファイル SPA） ([9546e03](https://github.com/beginerbeginer/video-cli/commit/9546e034768f1270650eff899edfc9550696627b))


### 不具合の修正

* build_operation_handlers の引数型を CliUI から UIPort に変更する ([d4b7846](https://github.com/beginerbeginer/video-cli/commit/d4b7846291690f5daca126585e6028165b36a9bc))
* edit_crop_form の再入力ラベルを日本語化しコメントを修正する ([1e5cb73](https://github.com/beginerbeginer/video-cli/commit/1e5cb7314c9833d541bbcbe4486c16bcdd865030)), closes [#78](https://github.com/beginerbeginer/video-cli/issues/78)
* ruff エラーを修正する（isort・F401・E501・F841） ([ac5e694](https://github.com/beginerbeginer/video-cli/commit/ac5e6945ddde6c2a1b859bcf546e6a2eb7be780d))
* validate_volume_level でも NaN/Inf を弾く ([ffb2426](https://github.com/beginerbeginer/video-cli/commit/ffb24268554b07c471fca61e99977042e3d40c28))
* volume の NaN 入力と WebM→MP4 変換時の音声コーデック問題を修正する ([af5d8e1](https://github.com/beginerbeginer/video-cli/commit/af5d8e18c2917d7ab95fdd884180c749ed79f6ac))
* WebM→MKV変換で不要なAAC再エンコードを避けるため音声コーデック選択条件を絞り込む ([78f3fef](https://github.com/beginerbeginer/video-cli/commit/78f3fef9ee92d54004c47b6351fd2c21d0c2abe3))
* WebM音声コーデック不整合とNaN fps入力未検出を修正する ([e599e8f](https://github.com/beginerbeginer/video-cli/commit/e599e8f09d2bc2d63b486f09f5d4da9c94bec520))
* ライト/ダークモード切替を追加し、server.py のテストを補完する ([df6c932](https://github.com/beginerbeginer/video-cli/commit/df6c932eac3da1c4386131485619f0fba4e851f6))
* 本文中で引用されたマーカーを区画と取り違えないようにする ([52d3920](https://github.com/beginerbeginer/video-cli/commit/52d3920c8c172abc2dd01583deaa04e901d6d6bc))
