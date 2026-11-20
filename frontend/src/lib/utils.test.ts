import { cn } from "./utils";

describe("cn", () => {
  it("条件付きのクラスを渡すと真のものだけが残る", () => {
    // Arrange / Act
    const result = cn("p-2", { "font-bold": false, "text-sm": true });

    // Assert
    expect(result).toBe("p-2 text-sm");
  });

  it("Tailwind のクラスが衝突すると後から渡したものが勝つ", () => {
    // Arrange / Act
    const result = cn("px-2 py-1", "px-4");

    // Assert
    expect(result).toBe("py-1 px-4");
  });
});
