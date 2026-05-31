import type { BenchmarkResponse } from "../types";

interface AlgorithmBenchmarkProps {
  data: BenchmarkResponse;
}

function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const minutes = seconds / 60;
  return minutes >= 60 ? `${(minutes / 60).toFixed(1)} hr` : `${minutes.toFixed(1)} min`;
}

function formatPct(pct: number | null | undefined): string {
  if (pct == null) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

export function AlgorithmBenchmark({ data }: AlgorithmBenchmarkProps) {
  return (
    <div className="compare-panel">
      <h2>Research algorithm benchmark</h2>
      <p className="muted compare-subtitle">
        Same matrix · {data.stop_count} stops · best:{" "}
        <strong>{data.best_algorithm_id ?? "—"}</strong>
      </p>
      <div className="table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Year</th>
              <th>Duration</th>
              <th>vs Best</th>
              <th>Category</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((row) => (
              <tr
                key={row.algorithm_id}
                className={row.algorithm_id === data.best_algorithm_id ? "baseline-row" : ""}
              >
                <td>
                  <strong>{row.algorithm_label}</strong>
                  <br />
                  <small className="muted">{row.paper}</small>
                </td>
                <td>{row.year || "—"}</td>
                <td>{row.status === "ok" ? formatDuration(row.total_duration_s) : row.error}</td>
                <td>{formatPct(row.vs_best_duration_pct)}</td>
                <td>{row.category}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
