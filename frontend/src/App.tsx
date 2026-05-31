import { useEffect, useState } from "react";
import {
  benchmarkAlgorithms,
  checkHealth,
  compareRoutes,
  reverseGeocode,
} from "./api/client";
import { AlgorithmBenchmark } from "./components/AlgorithmBenchmark";
import { AlgorithmPicker } from "./components/AlgorithmPicker";
import { MapPanel } from "./components/MapPanel";
import { RouteComparison } from "./components/RouteComparison";
import { RouteSequence } from "./components/RouteSequence";
import { StopList } from "./components/StopList";
import { StopSearchBar } from "./components/StopSearchBar";
import { TransportModeBar } from "./components/TransportModeBar";
import {
  DEFAULT_SOLVER_ID,
  fetchSolverGroups,
  findSolverOption,
  runSolver,
  type SolverGroup,
} from "./solvers";
import type { BenchmarkResponse, CompareResponse, OrderedStop, Stop } from "./types";
import type { TransportModeId } from "./transportModes";

export default function App() {
  const [stops, setStops] = useState<Stop[]>([]);
  const [routeOrder, setRouteOrder] = useState<number[] | null>(null);
  const [orderedStops, setOrderedStops] = useState<OrderedStop[] | null>(null);
  const [summary, setSummary] = useState<{
    distance: number;
    duration: number;
    solver?: string;
    profileSource?: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [solverGroups, setSolverGroups] = useState<SolverGroup[]>([]);
  const [solversLoading, setSolversLoading] = useState(true);
  const [selectedSolverId, setSelectedSolverId] = useState(DEFAULT_SOLVER_ID);
  const [roundTrip, setRoundTrip] = useState(true);
  const [transportMode, setTransportMode] = useState<TransportModeId>("driving-traffic");
  const [mapFocus, setMapFocus] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    checkHealth().then(setApiOnline);
    fetchSolverGroups()
      .then(setSolverGroups)
      .catch(() => setSolverGroups([]))
      .finally(() => setSolversLoading(false));
  }, []);

  const clearRoute = () => {
    setRouteOrder(null);
    setOrderedStops(null);
    setSummary(null);
    setCompareResult(null);
    setBenchmarkResult(null);
  };

  const addStop = (stop: Stop) => {
    const hasName = stop.name.trim().length > 0;
    const index = stops.length;
    setStops((prev) => [
      ...prev,
      { ...stop, name: hasName ? stop.name.trim() : "Finding place…" },
    ]);
    clearRoute();
    setError(null);

    if (hasName) {
      setMapFocus({ lat: stop.lat, lng: stop.lng });
      return;
    }

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

  const handleOptimize = async (modeOverride?: TransportModeId) => {
    if (stops.length < 2) return;
    const mode = modeOverride ?? transportMode;
    const solver = findSolverOption(solverGroups, selectedSolverId);
    if (!solver) return;

    setLoading(true);
    setError(null);
    try {
      const result = await runSolver(solver.id, solver.kind, {
        stops,
        round_trip: roundTrip,
        mode,
      });
      setRouteOrder(result.order);
      setOrderedStops(result.ordered_stops);
      setSummary({
        distance: result.total_distance_m,
        duration: result.total_duration_s,
        solver: result.solver,
        profileSource: result.profile_source,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization failed");
      clearRoute();
    } finally {
      setLoading(false);
    }
  };

  const onModeChange = (mode: TransportModeId) => {
    const hadResult = orderedStops !== null && summary !== null;
    setTransportMode(mode);
    if (hadResult && stops.length >= 2) {
      void handleOptimize(mode);
    }
  };

  const onSolverChange = (solverId: string) => {
    const hadResult = orderedStops !== null && summary !== null;
    setSelectedSolverId(solverId);
    if (hadResult && stops.length >= 2) {
      void handleOptimize();
    }
  };

  const handleCompare = async () => {
    if (stops.length < 2) return;
    setCompareLoading(true);
    setError(null);
    try {
      const result = await compareRoutes({
        stops,
        round_trip: roundTrip,
        mode: transportMode,
      });
      setCompareResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setCompareLoading(false);
    }
  };

  const handleBenchmark = async () => {
    if (stops.length < 2) return;
    setBenchmarkLoading(true);
    setError(null);
    try {
      const result = await benchmarkAlgorithms({
        stops,
        round_trip: roundTrip,
        mode: transportMode,
        time_limit_s: 8,
      });
      setBenchmarkResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark failed");
    } finally {
      setBenchmarkLoading(false);
    }
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
          <p>Search for stops or click the map, then optimize.</p>
        </div>
        <AlgorithmPicker
          groups={solverGroups}
          value={selectedSolverId}
          onChange={onSolverChange}
          loading={solversLoading}
          disabled={apiOnline === false}
        />
      </header>

      <TransportModeBar value={transportMode} onChange={onModeChange} />

      <main className="layout">
        <section className="map-section">
          <MapPanel
            stops={stops}
            routeOrder={routeOrder}
            onAddStop={addStop}
            focus={mapFocus}
          />
        </section>

        <aside className="sidebar">
          <StopSearchBar onSelectStop={addStop} disabled={apiOnline === false} />
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
              solver={summary.solver}
              profileSource={summary.profileSource}
            />
          )}

          {compareResult && <RouteComparison data={compareResult} />}

          {benchmarkResult && <AlgorithmBenchmark data={benchmarkResult} />}

          {error && <p className="error">{error}</p>}

          <div className="actions">
            <button
              type="button"
              className="primary"
              disabled={stops.length < 2 || loading}
              onClick={() => void handleOptimize()}
            >
              {loading ? "Optimizing…" : "Optimize route"}
            </button>
            <button
              type="button"
              disabled={stops.length < 2 || compareLoading}
              onClick={() => void handleCompare()}
            >
              {compareLoading ? "Comparing…" : "Compare apps"}
            </button>
            <button
              type="button"
              disabled={stops.length < 2 || benchmarkLoading}
              onClick={() => void handleBenchmark()}
            >
              {benchmarkLoading ? "Benchmarking…" : "Benchmark algorithms"}
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
