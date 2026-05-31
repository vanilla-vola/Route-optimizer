import type { CompareResponse } from "../types";

interface RouteComparisonProps {
  data: CompareResponse;
}

function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const minutes = seconds / 60;
  return minutes >= 60 ? `${(minutes / 60).toFixed(1)} hr` : `${minutes.toFixed(1)} min`;
}

function formatDistance(meters: number | null | undefined): string {
  if (meters == null) return "—";
  return meters >= 1000 ? `${(meters / 1000).toFixed(2)} km` : `${meters} m`;
}

function formatPct(pct: number | null | undefined): string {
  if (pct == null) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

export function RouteComparison({ data }: RouteComparisonProps) {
  return (
    <div className="compare-panel">
      <h2>Compare apps & services</h2>
      <p className="muted compare-subtitle">
        Same {data.stop_count} stops · {data.mode}
        {data.round_trip ? " · round trip" : " · one-way"} · profiles: {data.profile_source}
      </p>
      <div className="table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Duration</th>
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
                  {row.is_baseline && <span className="badge">baseline</span>}
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
