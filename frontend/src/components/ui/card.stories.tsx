import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, within } from "storybook/test";
import { Button } from "./button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card";

type CardStoryArgs = { title: string; description: string; body: string };

function CardExample({ title, description, body }: CardStoryArgs) {
  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="break-words">{body}</p>
        <Button className="self-start">実行</Button>
      </CardContent>
    </Card>
  );
}

const meta = {
  title: "UI/Card",
  component: CardExample,
  args: {
    title: "トリム",
    description: "動画の一部を切り出します",
    body: "開始と終了の時間を指定してください。",
  },
} satisfies Meta<typeof CardExample>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "通常",
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("トリム")).toBeInTheDocument();
    await expect(canvas.getByText("動画の一部を切り出します")).toBeInTheDocument();
  },
};

export const LongText: Story = {
  name: "長い文字列",
  args: {
    title: "とても長いタイトル。複数のファイルをつなげて 1 本の動画にする操作の説明",
    body: "/Users/example/Movies/2026/family-trip/very-long-directory-name/very-long-file-name-without-spaces-0001.mp4",
  },
};

export const Dark: Story = {
  name: "ダーク",
  globals: { theme: "ダーク" },
};

export const Mobile: Story = {
  name: "スマホ幅",
  globals: { viewport: { value: "mobile", isRotated: false } },
};
