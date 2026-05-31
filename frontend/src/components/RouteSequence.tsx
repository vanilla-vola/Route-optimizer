import type { OrderedStop } from "../types";
import { TRANSPORT_MODES } from "../transportModes";

interface RouteSequenceProps {
  orderedStops: OrderedStop[];
  totalDistanceM: number;
  totalDurationS: number;
  mode: string;
  roundTrip: boolean;
  solver?: string;
  profileSource?: string | null;
}

function formatDuration(seconds: number): string {
  const minutes = seconds / 60;
  return minutes >= 60 ? `${(minutes / 60).toFixed(1)} hr` : `${minutes.toFixed(1)} min`;
}

function formatDistance(meters: number): string {
  return meters >= 1000 ? `${(meters / 1000).toFixed(2)} km` : `${meters} m`;
}

function formatProfileSource(source: string): string {
  if (source === "mapbox-depart-at") return "Mapbox traffic profiles (8am / 1pm / 6pm)";
  if (source === "synthetic") return "Synthetic traffic profiles";
  return source;
}

export function RouteSequence({
  orderedStops,
  totalDistanceM,
  totalDurationS,
  mode,
  roundTrip,
  solver,
  profileSource,
}: RouteSequenceProps) {
  const modeLabel = TRANSPORT_MODES.find((m) => m.id === mode)?.label ?? mode;

  return (
    <div className="route-sequence">
      <h2>
        Best route ({modeLabel}
        {roundTrip ? ", cyclic" : ", one-way"})
      </h2>
      <p className="route-stats">
        {formatDistance(totalDistanceM)} · {formatDuration(totalDurationS)}
      </p>
      {solver && (
        <p className="route-meta muted">
          Solver: <strong>{solver}</strong>
          {profileSource ? (
            <>
              {" "}
              · {formatProfileSource(profileSource)}
            </>
          ) : null}
        </p>
      )}
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
