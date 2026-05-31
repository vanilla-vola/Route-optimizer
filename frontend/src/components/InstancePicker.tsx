import { useEffect, useRef, useState } from "react";
import {
  fetchBenchmarkInstance,
  listBenchmarkInstances,
} from "../api/client";
import type {
  BenchmarkInstanceDetail,
  BenchmarkInstanceSummary,
} from "../types";

interface InstancePickerProps {
  value: string | null;
  onSelect: (instance: BenchmarkInstanceDetail) => void;
  disabled?: boolean;
}

export function InstancePicker({
  value,
  onSelect,
  disabled = false,
}: InstancePickerProps) {
  const [instances, setInstances] = useState<BenchmarkInstanceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [viewStopsId, setViewStopsId] = useState<string | null>(null);
  const [detail, setDetail] = useState<BenchmarkInstanceDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listBenchmarkInstances()
      .then((response) => setInstances(response.instances))
      .catch(() => setInstances([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setViewStopsId(null);
        setDetail(null);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  const selectedSummary = instances.find((item) => item.id === value);

  const openViewStops = async (instanceId: string) => {
    setViewStopsId(instanceId);
    setDetailLoading(true);
    try {
      const data = await fetchBenchmarkInstance(instanceId);
      setDetail(data);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const applyInstance = async (instanceId: string) => {
    const data = await fetchBenchmarkInstance(instanceId);
    onSelect(data);
    setOpen(false);
    setViewStopsId(null);
    setDetail(null);
  };

  const label = selectedSummary
    ? `${selectedSummary.city} · ${selectedSummary.stop_count} stops`
    : "Select benchmark instance";

  return (
    <div className="instance-picker" ref={rootRef}>
      <span className="instance-picker-label">Benchmark instance</span>
      <button
        type="button"
        className="instance-picker-trigger"
        disabled={disabled || loading}
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        {loading ? "Loading instances…" : label}
      </button>

      {open && (
        <div className="instance-picker-panel" role="listbox">
          {viewStopsId ? (
            <div className="instance-picker-detail">
              <button
                type="button"
                className="instance-picker-back"
                onClick={() => {
                  setViewStopsId(null);
                  setDetail(null);
                }}
              >
                ← Back to instances
              </button>
              {detailLoading && <p className="muted">Loading stops…</p>}
              {!detailLoading && detail && (
                <>
                  <h3 className="instance-picker-detail-title">{detail.id}</h3>
                  <p className="muted instance-picker-detail-desc">
                    {detail.description}
                  </p>
                  <ol className="instance-stops-list">
                    {detail.stops.map((stop, index) => (
                      <li key={`${stop.name}-${index}`}>
                        <strong>
                          {index + 1}. {stop.name}
                        </strong>
                        <span>
                          {stop.lat.toFixed(5)}, {stop.lng.toFixed(5)}
                        </span>
                      </li>
                    ))}
                  </ol>
                  <button
                    type="button"
                    className="primary instance-picker-load"
                    onClick={() => void applyInstance(detail.id)}
                  >
                    Load this instance
                  </button>
                </>
              )}
            </div>
          ) : (
            <ul className="instance-picker-list">
              {instances.map((item) => (
                <li
                  key={item.id}
                  className={
                    item.id === value ? "instance-picker-item selected" : "instance-picker-item"
                  }
                >
                  <button
                    type="button"
                    className="instance-picker-item-main"
                    onClick={() => void applyInstance(item.id)}
                  >
                    <span className="instance-picker-item-id">{item.id}</span>
                    <span className="instance-picker-item-meta">
                      {item.city} · {item.pattern} · {item.stop_count} stops
                    </span>
                    <span className="instance-picker-item-desc">{item.description}</span>
                  </button>
                  <button
                    type="button"
                    className="instance-picker-view-stops"
                    onClick={(event) => {
                      event.stopPropagation();
                      void openViewStops(item.id);
                    }}
                  >
                    View stops
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
