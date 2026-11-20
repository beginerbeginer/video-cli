import { withThemeByClassName } from "@storybook/addon-themes";
import type { Preview } from "@storybook/react-vite";
import "../src/index.css";

// 画面幅の候補を増やしすぎると「どの幅で確認したか」がばらつくので、
// 実際に想定している PC 幅とスマホ幅の 2 つだけに絞る。
export const viewports = {
  pc: { name: "PC 幅", styles: { width: "1280px", height: "800px" }, type: "desktop" },
  mobile: { name: "スマホ幅", styles: { width: "375px", height: "667px" }, type: "mobile" },
} as const;

const preview: Preview = {
  parameters: {
    layout: "padded",
    viewport: { options: viewports },
    a11y: {
      // "todo" だと違反があっても見落とすので、a11y パネルで違反をエラーとして目立たせる。
      test: "error",
    },
  },
  decorators: [
    // shadcn/ui のダークは <html class="dark"> 前提（index.css の @custom-variant）なので、
    // data 属性で切り替える方式ではなく class 方式を使う。
    withThemeByClassName({
      themes: { ライト: "", ダーク: "dark" },
      defaultTheme: "ライト",
    }),
    (Story) => (
      <div className="bg-background text-foreground p-4">
        <Story />
      </div>
    ),
  ],
};

export default preview;
