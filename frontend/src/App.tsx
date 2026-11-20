import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// 画面の枠と API 呼び出しは #90 で作るので、ここは Tailwind と shadcn/ui の動作確認用のダミー画面に留める。
export default function App() {
  const [count, setCount] = useState(0);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 p-8">
      <h1 className="text-3xl font-bold tracking-tight">video-cli</h1>
      <Card>
        <CardHeader>
          <CardTitle>準備中</CardTitle>
          <CardDescription>新しい GUI の雛形です。操作画面はこれから作ります。</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => setCount((c) => c + 1)}>クリック: {count}</Button>
        </CardContent>
      </Card>
    </main>
  );
}
