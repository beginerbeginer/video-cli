import { render, screen, within } from "@testing-library/react";

import { ComponentCatalogTable } from "./ComponentCatalogTable";

import type { ComponentCatalogEntry } from "./component-catalog";

const entries: ComponentCatalogEntry[] = [
  { name: "PathField", summary: "パス入力", issue: 106, usedIn: [94], status: "予定" },
  { name: "JobPanel", summary: "ジョブ表示", issue: 108, usedIn: [95, 98], status: "作成済み" },
];

describe("ComponentCatalogTable", () => {
  it("部品ごとに 1 行あり、名前・担当 issue・状態が並ぶ", () => {
    // Arrange / Act
    render(<ComponentCatalogTable entries={entries} />);

    // Assert
    const row = screen.getByRole("row", { name: /PathField/ });
    expect(within(row).getByRole("link", { name: "#106" })).toHaveAttribute(
      "href",
      "https://github.com/beginerbeginer/video-cli/issues/106",
    );
    expect(within(row).getByText("予定")).toBeInTheDocument();
  });

  it("画面で使う issue が複数あるときはすべてリンクになる", () => {
    render(<ComponentCatalogTable entries={entries} />);

    const row = screen.getByRole("row", { name: /JobPanel/ });
    expect(within(row).getByRole("link", { name: "#95" })).toBeInTheDocument();
    expect(within(row).getByRole("link", { name: "#98" })).toBeInTheDocument();
  });

  it("状態ごとの件数を表示する", () => {
    render(<ComponentCatalogTable entries={entries} />);

    expect(screen.getByText("予定: 1 / 作成済み: 1 / 画面で使用中: 0")).toBeInTheDocument();
  });
});
