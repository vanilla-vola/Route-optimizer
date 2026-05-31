import { useEffect, useState } from "react";
import { checkHealth, optimizeRoute, reverseGeocode } from "./api/client";
import { MapPanel } from "./components/MapPanel";
import { RouteSequence } from "./components/RouteSequence";
import { StopList } from "./components/StopList";
import { TransportModeBar } from "./components/TransportModeBar";
import type { OrderedStop, Stop } from "./types";
import type { TransportModeId } from "./transportModes";

export default function App() {
  const [stops, setStops] = useState<Stop[]>([]);
  const [routeOrder, setRouteOrder] = useState<number[] | null>(null);
  const [orderedStops, setOrderedStops] = useState<OrderedStop[] | null>(null);
  const [summary, setSummary] = useState<{ distance: number; duration: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [roundTrip, setRoundTrip] = useState(true);
  const [transportMode, setTransportMode] = useState<TransportModeId>("driving");

  useEffect(() => {
    checkHealth().then(setApiOnline);
  }, []);

  const clearRoute = () => {
    setRouteOrder(null);
    setOrderedStops(null);
    setSummary(null);
  };

  const addStop = (stop: Stop) => {
    const index = stops.length;
    setStops((prev) => [...prev, { ...stop, name: "Finding place…" }]);
    clearRoute();
    setError(null);

    reverseGeocode(stop.lat, stop.lng).then((name) => {
      setStops((prev) => {
        if (index >= prev.length) return prev;
        const current = prev[index];
        if (current.lat !== stop.lat || current.lng !== stop.lng) return prev;
        return prev.map((s, i) => (i === index ? { ...s, name } : s));
      });
    });
  };

  const renameStop = (index: number, name: string) => {
    setStops((prev) => prev.map((s, i) => (i === index ? { ...s, name } : s)));
    clearRoute();
  };

  const removeStop = (index: number) => {
    setStops((prev) => prev.filter((_, i) => i !== index));
    clearRoute();
  };

  const clearStops = () => {
    setStops([]);
    clearRoute();
    setError(null);
  };

  const handleOptimize = async () => {
    if (stops.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const result = await optimizeRoute({
        stops,
        round_trip: roundTrip,
        mode: transportMode,
      });
      setRouteOrder(result.order);
      setOrderedStops(result.ordered_stops);
      setSummary({
        distance: result.total_distance_m,
        duration: result.total_duration_s,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization failed");
      clearRoute();
    } finally {
      setLoading(false);
    }
  };

  const onModeChange = (mode: TransportModeId) => {
    setTransportMode(mode);
    clearRoute();
  };

  const onRoundTripChange = (value: boolean) => {
    setRoundTrip(value);
    clearRoute();
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Route Optimizer</h1>
          <p>Place stops on the map, choose transport, then optimize.</p>
        </div>
        <div className={`status ${apiOnline ? "online" : "offline"}`}>
          API {apiOnline === null ? "checking…" : apiOnline ? "online" : "offline"}
        </div>
      </header>

      <TransportModeBar value={transportMode} onChange={onModeChange} />

      <main className="layout">
        <section className="map-section">
          <MapPanel stops={stops} routeOrder={routeOrder} onAddStop={addStop} />
        </section>

        <aside className="sidebar">
          <StopList stops={stops} onRemove={removeStop} onRename={renameStop} />

          <label className="toggle">
            <input
              type="checkbox"
              checked={roundTrip}
              onChange={(e) => onRoundTripChange(e.target.checked)}
            />
            <span>
              <strong>Return to start (cyclic route)</strong>
              <br />
              <small>First stop is both start and end</small>
            </span>
          </label>

          {orderedStops && summary && (
            <RouteSequence
              orderedStops={orderedStops}
              totalDistanceM={summary.distance}
              totalDurationS={summary.duration}
              mode={transportMode}
              roundTrip={roundTrip}
            />
          )}

          {error && <p className="error">{error}</p>}

          <div className="actions">
            <button
              type="button"
              className="primary"
              disabled={stops.length < 2 || loading}
              onClick={handleOptimize}
            >
              {loading ? "Optimizing…" : "Optimize route"}
            </button>
            <button type="button" onClick={clearStops} disabled={stops.length === 0}>
              Clear
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}
