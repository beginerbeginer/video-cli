import { COMPONENT_STATUSES } from "./component-catalog";

import type { ComponentCatalogEntry } from "./component-catalog";

const ISSUE_URL = "https://github.com/beginerbeginer/video-cli/issues";

function IssueLink({ issue }: { issue: number }) {
  return (
    <a href={`${ISSUE_URL}/${String(issue)}`} target="_blank" rel="noreferrer">
      #{issue}
    </a>
  );
}

function summarizeStatuses(entries: ComponentCatalogEntry[]) {
  return COMPONENT_STATUSES.map(
    (status) => `${status}: ${String(entries.filter((entry) => entry.status === status).length)}`,
  ).join(" / ");
}

export function ComponentCatalogTable({ entries }: { entries: ComponentCatalogEntry[] }) {
  return (
    <div>
      <p>{summarizeStatuses(entries)}</p>
      <table>
        <thead>
          <tr>
            <th scope="col">部品</th>
            <th scope="col">内容</th>
            <th scope="col">作る issue</th>
            <th scope="col">画面で使う issue</th>
            <th scope="col">状態</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.name}>
              <th scope="row">
                <code>{entry.name}</code>
              </th>
              <td>{entry.summary}</td>
              <td>
                <IssueLink issue={entry.issue} />
              </td>
              <td>
                {entry.usedIn.map((issue, index) => (
                  <span key={issue}>
                    {index > 0 && ", "}
                    <IssueLink issue={issue} />
                  </span>
                ))}
              </td>
              <td>{entry.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
