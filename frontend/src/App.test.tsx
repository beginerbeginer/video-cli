import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

describe("App", () => {
  it("開くと video-cli のタイトルが表示される", () => {
    // Arrange / Act
    render(<App />);

    // Assert
    expect(screen.getByRole("heading", { level: 1, name: "video-cli" })).toBeInTheDocument();
  });

  it("ボタンを押すとクリック回数が 1 増える", async () => {
    // Arrange
    render(<App />);

    // Act
    await userEvent.click(screen.getByRole("button", { name: "クリック: 0" }));

    // Assert
    expect(screen.getByRole("button", { name: "クリック: 1" })).toBeInTheDocument();
  });
});
