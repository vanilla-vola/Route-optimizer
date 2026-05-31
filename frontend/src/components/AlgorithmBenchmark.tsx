import type { BenchmarkResponse } from "../types";
import { formatDuration, formatPct, formatProfileSource } from "../utils/format";

interface AlgorithmBenchmarkProps {
  data: BenchmarkResponse;
}

export function AlgorithmBenchmark({ data }: AlgorithmBenchmarkProps) {
  const bestNominal = data.results.find((r) => r.algorithm_id === data.best_algorithm_id);
  const bestRealized = data.results.find(
    (r) => r.algorithm_id === data.best_realized_algorithm_id,
  );

  return (
    <div className="compare-panel">
      <h2>Research algorithm benchmark</h2>
      <p className="muted compare-subtitle">
        {data.stop_count} stops · {data.mode} · {formatProfileSource(data.profile_source)}
      </p>

      <div className="route-metrics route-metrics--compact">
        <div className="metric-card">
          <span className="metric-label">Best nominal</span>
          <strong className="metric-value">
            {formatDuration(bestNominal?.total_duration_s)}
          </strong>
          <span className="metric-hint">{data.best_algorithm_id ?? "—"}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Best realized</span>
          <strong className="metric-value">
            {formatDuration(bestRealized?.realized_duration_s)}
          </strong>
          <span className="metric-hint">{data.best_realized_algorithm_id ?? "—"}</span>
        </div>
      </div>

      {data.ranking_note && (
        <p className="muted compare-subtitle">{data.ranking_note}</p>
      )}

      <div className="table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Nominal</th>
              <th>vs Best (N)</th>
              <th>Realized</th>
              <th>vs Best (R)</th>
              <th>Distance</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((row) => {
              const nominalBest = row.algorithm_id === data.best_algorithm_id;
              const realizedBest = row.algorithm_id === data.best_realized_algorithm_id;
              return (
                <tr
                  key={row.algorithm_id}
                  className={nominalBest || realizedBest ? "baseline-row" : ""}
                >
                  <td>
                    <strong>{row.algorithm_label}</strong>
                    {nominalBest && <span className="badge">N</span>}
                    {realizedBest && <span className="badge badge--realized">R</span>}
                    <br />
                    <small className="muted">{row.category}</small>
                  </td>
                  <td>
                    {row.status === "ok" ? formatDuration(row.total_duration_s) : row.error}
                  </td>
                  <td>{formatPct(row.vs_best_duration_pct)}</td>
                  <td>{formatDuration(row.realized_duration_s)}</td>
                  <td>{formatPct(row.vs_best_realized_pct)}</td>
                  <td>
                    {row.total_distance_m != null
                      ? `${(row.total_distance_m / 1000).toFixed(2)} km`
                      : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
