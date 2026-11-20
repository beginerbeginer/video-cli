export const COMPONENT_STATUSES = ["予定", "作成済み", "画面で使用中"] as const;

export type ComponentStatus = (typeof COMPONENT_STATUSES)[number];

export type ComponentCatalogEntry = {
  name: string;
  summary: string;
  /** 部品を Storybook で作る issue */
  issue: number;
  /** 部品を画面に組み込み、API とつなぐ issue */
  usedIn: number[];
  status: ComponentStatus;
};

// MDX に表を直書きする案もあるが、状態の書き間違いや部品の載せ忘れをテストで防げるよう、
// 一覧はデータとして持ち、MDX はそれを表示するだけにする。
// 部品を作ったら status を「作成済み」に、画面に組み込んだら「画面で使用中」に変える。
export const componentCatalog: ComponentCatalogEntry[] = [
  // #86 雛形で入った shadcn/ui の部品
  { name: "Button", summary: "ボタン（shadcn/ui）", issue: 86, usedIn: [90], status: "作成済み" },
  { name: "Card", summary: "カード（shadcn/ui）", issue: 86, usedIn: [90], status: "作成済み" },

  // #106 画面の枠とファイル選択
  {
    name: "AppShell",
    summary: "ヘッダー・サイドバー・メイン領域の枠。スマホ幅ではサイドバーを開閉",
    issue: 106,
    usedIn: [90],
    status: "予定",
  },
  {
    name: "OperationSidebar",
    summary: "操作の一覧。選んでいる操作が分かる",
    issue: 106,
    usedIn: [90],
    status: "予定",
  },
  {
    name: "HealthBanner",
    summary: "ffmpeg / ffprobe が無いときの警告",
    issue: 106,
    usedIn: [90],
    status: "予定",
  },
  {
    name: "ThemeToggle",
    summary: "ライト / ダーク / システムに合わせる、の切り替え",
    issue: 106,
    usedIn: [90],
    status: "予定",
  },
  {
    name: "PathField",
    summary: "パスの入力欄と「参照」ボタン。エラー表示つき",
    issue: 106,
    usedIn: [94],
    status: "予定",
  },
  {
    name: "FileBrowserDialog",
    summary: "フォルダ移動・パンくず。開く / 保存 / 複数選択のモード",
    issue: 106,
    usedIn: [94],
    status: "予定",
  },
  {
    name: "MediaInfoPanel",
    summary: "長さ・解像度・コーデック・fps の表示",
    issue: 106,
    usedIn: [94],
    status: "予定",
  },

  // #107 フォーム部品
  {
    name: "FormField",
    summary: "ラベル・説明・エラーメッセージ。API の 422 の field と対応",
    issue: 107,
    usedIn: [96, 97],
    status: "予定",
  },
  {
    name: "TimeInput",
    summary: "秒 または HH:MM:SS の時間入力",
    issue: 107,
    usedIn: [96, 97],
    status: "予定",
  },
  {
    name: "NumberField",
    summary: "単位・範囲・プリセットつきの数値入力",
    issue: 107,
    usedIn: [96, 97],
    status: "予定",
  },
  {
    name: "CrfField",
    summary: "CRF の入力と、画質・ファイルサイズの目安",
    issue: 107,
    usedIn: [96],
    status: "予定",
  },
  {
    name: "RotateDirectionPicker",
    summary: "回転・反転の向きをアイコンボタンで選ぶ",
    issue: 107,
    usedIn: [97],
    status: "予定",
  },
  {
    name: "CommandPreview",
    summary: "生成される ffmpeg コマンドの表示とコピー",
    issue: 107,
    usedIn: [96, 97],
    status: "予定",
  },
  {
    name: "OutputExistsWarning",
    summary: "出力ファイルがすでにあるときの警告",
    issue: 107,
    usedIn: [96, 97],
    status: "予定",
  },
  {
    name: "OperationFormLayout",
    summary: "入力・パラメータ・出力・実行ボタンの区画のレイアウト",
    issue: 107,
    usedIn: [96, 97],
    status: "予定",
  },

  // #108 実行パネルと concat
  {
    name: "JobPanel",
    summary: "ジョブの状態（待機中・実行中・完了・失敗・キャンセル済み）とキャンセル",
    issue: 108,
    usedIn: [95],
    status: "予定",
  },
  {
    name: "LogViewer",
    summary: "ffmpeg のログ。折りたたみと自動スクロール",
    issue: 108,
    usedIn: [95],
    status: "予定",
  },
  {
    name: "ConcatFileList",
    summary: "結合するファイルの追加・削除・並べ替え",
    issue: 108,
    usedIn: [98],
    status: "予定",
  },
  {
    name: "ConcatCompatibility",
    summary: "結合方法（コピー / 再エンコード）と理由の表示",
    issue: 108,
    usedIn: [98],
    status: "予定",
  },
];
