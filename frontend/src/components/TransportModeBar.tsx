import type { TransportModeId } from "../transportModes";
import { TRANSPORT_MODES } from "../transportModes";

interface TransportModeBarProps {
  value: TransportModeId;
  onChange: (mode: TransportModeId) => void;
  availableModes?: TransportModeId[];
}

export function TransportModeBar({
  value,
  onChange,
  availableModes,
}: TransportModeBarProps) {
  const modes = availableModes?.length
    ? TRANSPORT_MODES.filter((mode) => availableModes.includes(mode.id))
    : TRANSPORT_MODES;

  return (
    <div className="mode-bar" role="toolbar" aria-label="Transport mode">
      {modes.map((mode) => (
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
