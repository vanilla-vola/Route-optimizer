import {
  benchmarkAlgorithms,
  compareRoutes,
  listAlgorithms,
  listCompareProviders,
  optimizeRoute,
} from "./api/client";
import type {
  AlgorithmInfo,
  CompareProviderInfo,
  OptimizeRequest,
  OptimizeResponse,
  OrderedStop,
  Stop,
} from "./types";

export const DEFAULT_SOLVER_ID = "route-optimizer";

export type SolverKind = "default" | "compare" | "research";

export interface SolverOption {
  id: string;
  label: string;
  kind: SolverKind;
}

export interface SolverGroup {
  label: string;
  options: SolverOption[];
}

export function buildSolverGroups(
  providers: CompareProviderInfo[],
  algorithms: AlgorithmInfo[],
): SolverGroup[] {
  const ours = providers.find((p) => p.id === DEFAULT_SOLVER_ID);
  const compareApps = providers.filter(
    (p) => p.id !== DEFAULT_SOLVER_ID && (p.kind === "api" || p.kind === "manual"),
  );
  const compareInternal = providers.filter(
    (p) => p.id !== DEFAULT_SOLVER_ID && p.kind === "internal",
  );

  const kindOrder: Record<string, number> = { api: 0, manual: 1 };
  compareApps.sort(
    (a, b) => (kindOrder[a.kind] ?? 2) - (kindOrder[b.kind] ?? 2),
  );

  const compareOptions: SolverOption[] = [];
  if (ours) {
    compareOptions.push({ id: ours.id, label: ours.label, kind: "default" });
  }
  for (const provider of [...compareApps, ...compareInternal]) {
    compareOptions.push({
      id: provider.id,
      label: provider.label,
      kind: "compare",
    });
  }

  const researchOptions: SolverOption[] = algorithms.map((algorithm) => ({
    id: algorithm.id,
    label: algorithm.label,
    kind: "research",
  }));

  return [
    { label: "Compare", options: compareOptions },
    { label: "Research algorithms", options: researchOptions },
  ];
}

export async function fetchSolverGroups(): Promise<SolverGroup[]> {
  const [providers, algorithms] = await Promise.all([
    listCompareProviders(),
    listAlgorithms(),
  ]);
  return buildSolverGroups(providers, algorithms);
}

function buildOrderedStops(order: number[], stops: Stop[]): OrderedStop[] {
  return order.map((index, sequence) => {
    const stop = stops[index];
    return {
      sequence: sequence + 1,
      index,
      name: stop.name,
      lat: stop.lat,
      lng: stop.lng,
    };
  });
}

export async function runSolver(
  solverId: string,
  kind: SolverKind,
  payload: OptimizeRequest,
): Promise<OptimizeResponse> {
  if (kind === "default") {
    return optimizeRoute(payload);
  }

  if (kind === "compare") {
    const result = await compareRoutes({
      ...payload,
      provider_ids: [solverId],
    });
    const item = result.results.find((row) => row.provider_id === solverId);
    if (!item) {
      throw new Error("Compare provider did not return a result");
    }
    if (item.status === "manual") {
      if (item.manual_url) {
        window.open(item.manual_url, "_blank", "noopener,noreferrer");
      }
      throw new Error(
        item.message || "Open the external app to compare this route manually.",
      );
    }
    if (item.status !== "ok" || !item.order?.length) {
      throw new Error(item.message || `${item.provider_label} could not optimize this route`);
    }
    return {
      order: item.order,
      ordered_stops:
        item.ordered_stops ?? buildOrderedStops(item.order, payload.stops),
      total_distance_m: item.total_distance_m ?? 0,
      total_duration_s: item.total_duration_s ?? 0,
      mode: payload.mode ?? "driving-traffic",
      round_trip: payload.round_trip ?? true,
      solver: item.provider_label,
      profile_source: result.profile_source,
    };
  }

  const result = await benchmarkAlgorithms({
    ...payload,
    algorithm_ids: [solverId],
  });
  const item = result.results.find((row) => row.algorithm_id === solverId);
  if (!item || item.status !== "ok" || !item.order?.length) {
    throw new Error(item?.error || item?.notes || "Algorithm failed to optimize this route");
  }
  return {
    order: item.order,
    ordered_stops: buildOrderedStops(item.order, payload.stops),
    total_distance_m: item.total_distance_m ?? 0,
    total_duration_s: item.total_duration_s ?? 0,
    mode: payload.mode ?? "driving-traffic",
    round_trip: payload.round_trip ?? true,
    solver: item.algorithm_label,
    profile_source: result.profile_source,
  };
}

export function findSolverOption(
  groups: SolverGroup[],
  solverId: string,
): SolverOption | undefined {
  for (const group of groups) {
    const match = group.options.find((option) => option.id === solverId);
    if (match) return match;
  }
  return undefined;
}
