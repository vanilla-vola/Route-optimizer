import type { TransportModeId } from "../transportModes";
import { TRANSPORT_MODES } from "../transportModes";

interface TransportModeBarProps {
  value: TransportModeId;
  onChange: (mode: TransportModeId) => void;
}

export function TransportModeBar({ value, onChange }: TransportModeBarProps) {
  return (
    <div className="mode-bar" role="toolbar" aria-label="Transport mode">
      {TRANSPORT_MODES.map((mode) => (
        <button
          key={mode.id}
          type="button"
          className={`mode-btn ${value === mode.id ? "active" : ""}`}
          title={mode.label}
          aria-label={mode.label}
          aria-pressed={value === mode.id}
          onClick={() => onChange(mode.id)}
        >
          <span className="mode-icon" aria-hidden>
            {mode.icon}
          </span>
          <span className="mode-label">{mode.label}</span>
        </button>
      ))}
    </div>
  );
}
