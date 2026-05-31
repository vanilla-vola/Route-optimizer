import type { OrderedStop } from "../types";
import { TRANSPORT_MODES } from "../transportModes";
import { RouteMetrics } from "./RouteMetrics";

interface RouteSequenceProps {
  orderedStops: OrderedStop[];
  totalDistanceM: number;
  totalDurationS: number;
  realizedDurationS?: number | null;
  mode: string;
  solver?: string;
  profileSource?: string | null;
}

export function RouteSequence({
  orderedStops,
  totalDistanceM,
  totalDurationS,
  realizedDurationS,
  mode,
  solver,
  profileSource,
}: RouteSequenceProps) {
  const modeLabel = TRANSPORT_MODES.find((m) => m.id === mode)?.label ?? mode;

  return (
    <div className="route-sequence">
      <h2>Best route ({modeLabel})</h2>
      <RouteMetrics
        nominalDurationS={totalDurationS}
        realizedDurationS={realizedDurationS}
        totalDistanceM={totalDistanceM}
        solver={solver}
        profileSource={profileSource}
      />
      <p className="route-sequence-label">Visit in this order:</p>
      <ol>
        {orderedStops.map((stop) => (
          <li key={`${stop.sequence}-${stop.index}`}>
            <strong>{stop.sequence}. {stop.name}</strong>
            <span className="coords">
              {stop.lat.toFixed(5)}, {stop.lng.toFixed(5)}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
