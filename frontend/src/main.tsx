import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import App from "./App.tsx";

const rootElement = document.querySelector("#root");
// 非 null アサーションで握りつぶすと、index.html と食い違ったときに原因の分かりにくい React のエラーになるので、先に明示的に落とす。
if (rootElement === null) {
  throw new Error("index.html に #root の要素がありません");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
