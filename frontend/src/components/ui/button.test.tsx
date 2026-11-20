import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Button } from "./button";

describe("Button", () => {
  it("押すと onClick が呼ばれる", async () => {
    // Arrange
    const onClick = vi.fn();
    render(<Button onClick={onClick}>実行</Button>);

    // Act
    await userEvent.click(screen.getByRole("button", { name: "実行" }));

    // Assert
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("disabled にすると押しても onClick が呼ばれない", async () => {
    // Arrange
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        実行
      </Button>,
    );

    // Act
    await userEvent.click(screen.getByRole("button", { name: "実行" }));

    // Assert
    expect(onClick).not.toHaveBeenCalled();
  });

  it("variant に destructive を渡すと破壊的操作の色になる", () => {
    // Arrange / Act
    render(<Button variant="destructive">削除</Button>);

    // Assert
    expect(screen.getByRole("button", { name: "削除" })).toHaveClass("bg-destructive");
  });

  it("asChild を渡すと子要素をボタンの見た目で描画する", () => {
    // Arrange / Act
    render(
      <Button asChild>
        <a href="/docs">ドキュメント</a>
      </Button>,
    );

    // Assert
    const link = screen.getByRole("link", { name: "ドキュメント" });
    expect(link).toHaveClass("bg-primary");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
