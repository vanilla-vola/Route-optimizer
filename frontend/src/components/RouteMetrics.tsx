import {
  formatDistance,
  formatDuration,
  formatProfileSource,
  nominalVsRealizedPct,
} from "../utils/format";

interface RouteMetricsProps {
  nominalDurationS: number;
  realizedDurationS?: number | null;
  totalDistanceM: number;
  solver?: string;
  profileSource?: string | null;
  compact?: boolean;
}

export function RouteMetrics({
  nominalDurationS,
  realizedDurationS,
  totalDistanceM,
  solver,
  profileSource,
  compact = false,
}: RouteMetricsProps) {
  const delta = nominalVsRealizedPct(nominalDurationS, realizedDurationS);

  return (
    <div className={`route-metrics${compact ? " route-metrics--compact" : ""}`}>
      <div className="metric-card">
        <span className="metric-label">Nominal duration</span>
        <strong className="metric-value">{formatDuration(nominalDurationS)}</strong>
        <span className="metric-hint">Static matrix snapshot</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Realized duration</span>
        <strong className="metric-value">{formatDuration(realizedDurationS)}</strong>
        <span className="metric-hint">
          {delta ?? "Departure-consistent traffic"}
        </span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Distance</span>
        <strong className="metric-value">{formatDistance(totalDistanceM)}</strong>
      </div>
      {!compact && solver && (
        <div className="metric-card metric-card--wide">
          <span className="metric-label">Solver</span>
          <strong className="metric-value metric-value--text">{solver}</strong>
          {profileSource && (
            <span className="metric-hint">{formatProfileSource(profileSource)}</span>
          )}
        </div>
      )}
    </div>
  );
}
