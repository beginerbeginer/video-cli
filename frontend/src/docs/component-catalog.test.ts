import { COMPONENT_STATUSES, componentCatalog } from "./component-catalog";

describe("componentCatalog", () => {
  it("#106・#107・#108 で作る予定の部品がすべて載っている", () => {
    // Arrange
    const expected = [
      // #106 画面の枠とファイル選択
      "AppShell",
      "OperationSidebar",
      "HealthBanner",
      "ThemeToggle",
      "PathField",
      "FileBrowserDialog",
      "MediaInfoPanel",
      // #107 フォーム部品
      "FormField",
      "TimeInput",
      "NumberField",
      "CrfField",
      "RotateDirectionPicker",
      "CommandPreview",
      "OutputExistsWarning",
      "OperationFormLayout",
      // #108 実行パネルと concat
      "JobPanel",
      "LogViewer",
      "ConcatFileList",
      "ConcatCompatibility",
    ];

    // Act
    const names = componentCatalog.map((entry) => entry.name);

    // Assert
    expect(names).toEqual(expect.arrayContaining(expected));
  });

  it("部品名が重複していない", () => {
    const names = componentCatalog.map((entry) => entry.name);

    expect(new Set(names).size).toBe(names.length);
  });

  it("どの部品にも担当 issue と、決められた状態のどれかが付いている", () => {
    for (const entry of componentCatalog) {
      expect(entry.issue).toBeGreaterThan(0);
      expect(COMPONENT_STATUSES).toContain(entry.status);
    }
  });

  it("画面で使う予定の issue が付いている", () => {
    for (const entry of componentCatalog) {
      expect(entry.usedIn.length).toBeGreaterThan(0);
    }
  });
});
