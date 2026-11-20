import { composeStories, setProjectAnnotations } from "@storybook/react-vite";
import * as previewAnnotations from "../.storybook/preview";

// Storybook と同じ decorator・parameters を効かせないと、「Storybook では見えるのにテストでは違う」状態が生まれる。
// 全テスト共通の setup に置かないのは、index.css が読み込まれて既存の部品テストの前提（CSS なし）が変わるため。
setProjectAnnotations([previewAnnotations]);

type StoryModule = Parameters<typeof composeStories>[0];

// 部品ごとに手でテストを書き足す方式だと、ストーリーを増やしてもテストに載せ忘れる。
// そこで *.stories.tsx を全部集め、各ストーリーの描画と play 関数をテストとして実行する。
const storyModules = import.meta.glob<StoryModule>("./**/*.stories.tsx", { eager: true });

const storyCases = Object.entries(storyModules).flatMap(([file, module]) =>
  // composeStories の戻り値はモジュールごとの型になるので、glob でまとめたあとは run() だけ使う型に寄せる。
  Object.entries(composeStories(module) as Record<string, { run: () => Promise<void> }>).map(
    ([name, Story]) => ({ file, name, Story }),
  ),
);

describe("ストーリー", () => {
  it("ストーリーが 1 つ以上ある", () => {
    expect(storyCases.length).toBeGreaterThan(0);
  });

  it.each(storyCases)("$file の $name が描画でき、play 関数が通る", async ({ Story }) => {
    await Story.run();
  });
});
