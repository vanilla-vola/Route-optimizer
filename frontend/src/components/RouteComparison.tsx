import type { CompareResponse } from "../types";
import { formatDistance, formatDuration, formatPct, formatProfileSource } from "../utils/format";

interface RouteComparisonProps {
  data: CompareResponse;
}

export function RouteComparison({ data }: RouteComparisonProps) {
  const baseline = data.results.find((r) => r.is_baseline);

  return (
    <div className="compare-panel">
      <h2>Compare apps & services</h2>
      <p className="muted compare-subtitle">
        Same {data.stop_count} stops · {data.mode}
        {data.round_trip ? " · round trip" : " · one-way"} ·{" "}
        {formatProfileSource(data.profile_source)}
      </p>
      {data.metrics_note && (
        <p className="muted compare-subtitle">{data.metrics_note}</p>
      )}

      {baseline?.total_duration_s != null && (
        <div className="route-metrics route-metrics--compact">
          <div className="metric-card">
            <span className="metric-label">Our duration (nominal)</span>
            <strong className="metric-value">
              {formatDuration(baseline.total_duration_s)}
            </strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Our distance</span>
            <strong className="metric-value">
              {formatDistance(baseline.total_distance_m)}
            </strong>
          </div>
        </div>
      )}

      <div className="table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Nominal duration</th>
              <th>Distance</th>
              <th>vs Ours</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((row) => (
              <tr key={row.provider_id} className={row.is_baseline ? "baseline-row" : ""}>
                <td>
                  <strong>{row.provider_label}</strong>
                  {row.is_baseline && <span className="badge">ours</span>}
                </td>
                <td>{formatDuration(row.total_duration_s)}</td>
                <td>{formatDistance(row.total_distance_m)}</td>
                <td>{row.is_baseline ? "—" : formatPct(row.vs_baseline_duration_pct)}</td>
                <td>
                  {row.status === "manual" && row.manual_url ? (
                    <a href={row.manual_url} target="_blank" rel="noreferrer">
                      Open ↗
                    </a>
                  ) : (
                    row.status
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.results.some((r) => r.message) && (
        <ul className="compare-notes">
          {data.results.filter((r) => r.message).map((r) => (
            <li key={r.provider_id}>
              <strong>{r.provider_label}:</strong> {r.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
