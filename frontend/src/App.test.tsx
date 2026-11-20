import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

describe("App", () => {
  it("video-cli のタイトルを表示する", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: "video-cli" })).toBeInTheDocument();
  });

  it("shadcn/ui の Button が押せる", async () => {
    render(<App />);
    const button = screen.getByRole("button", { name: "クリック: 0" });
    await userEvent.click(button);
    expect(screen.getByRole("button", { name: "クリック: 1" })).toBeInTheDocument();
  });
});
