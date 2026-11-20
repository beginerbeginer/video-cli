COMPRESS = "compress"
FPS = "fps"
TRIM = "trim"
CONCAT = "concat"
RESIZE = "resize"
VOLUME = "volume"
AUDIO_EXTRACT = "audio_extract"
THUMBNAIL = "thumbnail"
GIF = "gif"
SPEED = "speed"
MUTE = "mute"
CONVERT = "convert"
ROTATE = "rotate"
INFO = "info"
CROP = "crop"
EXIT = "exit"

# Why not ui/cli/main_menu.py に置く: API が ui/ を参照せずに表示名を使えるようにするため。
# 並び順は CLI メニューの表示順を兼ねる。
OPERATION_LABELS: dict[str, str] = {
    TRIM: "動画を切り出す",
    CONCAT: "動画を結合する",
    RESIZE: "動画サイズを変更する",
    VOLUME: "音量を調整する",
    AUDIO_EXTRACT: "音声を抽出する",
    THUMBNAIL: "サムネイルを抽出する",
    GIF: "GIFに変換する",
    SPEED: "速度を変更する",
    MUTE: "音声を削除する",
    CONVERT: "フォーマットを変換する",
    ROTATE: "回転・反転する",
    INFO: "動画情報を確認する",
    CROP: "動画をクロップする",
    COMPRESS: "動画を圧縮する",
    FPS: "フレームレートを変換する",
    EXIT: "終了する",
}
