import type { SolverGroup } from "../solvers";

interface AlgorithmPickerProps {
  groups: SolverGroup[];
  value: string;
  onChange: (solverId: string) => void;
  disabled?: boolean;
  loading?: boolean;
}

export function AlgorithmPicker({
  groups,
  value,
  onChange,
  disabled = false,
  loading = false,
}: AlgorithmPickerProps) {
  return (
    <label className="algorithm-picker">
      <span className="algorithm-picker-label">Algorithm</span>
      <select
        className="algorithm-picker-select"
        value={value}
        disabled={disabled || loading || groups.length === 0}
        onChange={(event) => onChange(event.target.value)}
        aria-label="Route optimization algorithm"
      >
        {loading ? (
          <option value={value}>Loading algorithms…</option>
        ) : groups.length === 0 ? (
          <option value={value}>Algorithms unavailable</option>
        ) : (
          groups.map((group) => (
            <optgroup key={group.label} label={group.label}>
              {group.options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </optgroup>
          ))
        )}
      </select>
    </label>
  );
}
