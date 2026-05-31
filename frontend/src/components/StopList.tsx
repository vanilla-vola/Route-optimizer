import type { Stop } from "../types";

interface StopListProps {
  stops: Stop[];
  onRemove: (index: number) => void;
  onRename: (index: number, name: string) => void;
}

export function StopList({ stops, onRemove, onRename }: StopListProps) {
  return (
    <div className="stop-list">
      <h2>Selected spots ({stops.length})</h2>
      {stops.length === 0 ? (
        <p className="muted">Click the map to place stops. No route line until you optimize.</p>
      ) : (
        <ul className="spots-list">
          {stops.map((stop, index) => (
            <li key={`${index}-${stop.lat}-${stop.lng}`}>
              <input
                type="text"
                className="stop-name-input"
                value={stop.name}
                onChange={(e) => onRename(index, e.target.value)}
                aria-label={`Name for stop ${index + 1}`}
              />
              <span className="coords">
                {stop.lat.toFixed(5)}, {stop.lng.toFixed(5)}
              </span>
              <button type="button" onClick={() => onRemove(index)} aria-label="Remove stop">
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
