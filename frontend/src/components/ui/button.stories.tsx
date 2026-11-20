import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, userEvent, within } from "storybook/test";
import { Button } from "./button";

const meta = {
  title: "UI/Button",
  component: Button,
  args: { children: "実行", onClick: fn() },
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "destructive", "outline", "secondary", "ghost", "link"],
    },
    size: { control: "select", options: ["default", "sm", "lg", "icon"] },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "通常",
  play: async ({ args, canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole("button", { name: "実行" }));
    await expect(args.onClick).toHaveBeenCalledTimes(1);
  },
};

export const Destructive: Story = {
  name: "破壊的操作",
  args: { variant: "destructive", children: "削除" },
};

export const Outline: Story = {
  name: "アウトライン",
  args: { variant: "outline", children: "参照" },
};

export const Disabled: Story = {
  name: "無効",
  args: { disabled: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "実行" })).toBeDisabled();
  },
};

export const LongText: Story = {
  name: "長い文字列",
  args: { children: "とても長いラベルのボタン。出力ファイルを上書きして実行する" },
};

export const Dark: Story = {
  name: "ダーク",
  globals: { theme: "ダーク" },
  play: async ({ canvasElement }) => {
    await expect(canvasElement.ownerDocument.documentElement).toHaveClass("dark");
  },
};

export const Mobile: Story = {
  name: "スマホ幅",
  globals: { viewport: { value: "mobile", isRotated: false } },
};
