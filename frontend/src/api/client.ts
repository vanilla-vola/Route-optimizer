import type {
  BenchmarkResponse,
  CompareResponse,
  OptimizeRequest,
  OptimizeResponse,
  PlaceSuggestion,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export async function optimizeRoute(
  payload: OptimizeRequest,
): Promise<OptimizeResponse> {
  const response = await fetch(`${API_BASE}/optimize-route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      stops: payload.stops,
      start_fixed: payload.start_fixed ?? false,
      end_fixed: payload.end_fixed ?? false,
      round_trip: payload.round_trip ?? true,
      mode: payload.mode ?? "driving-traffic",
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    let detail = `Request failed (${response.status})`;
    if (typeof body.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      detail = body.detail.map((e: { msg: string }) => e.msg).join("; ");
    }
    throw new Error(detail);
  }

  return response.json() as Promise<OptimizeResponse>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    let detail = `Request failed (${response.status})`;
    if (typeof data.detail === "string") {
      detail = data.detail;
    } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      detail = data.detail.map((e: { msg: string }) => e.msg).join("; ");
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export async function compareRoutes(
  payload: OptimizeRequest,
): Promise<CompareResponse> {
  return postJson<CompareResponse>("/compare-routes", {
    stops: payload.stops,
    start_fixed: payload.start_fixed ?? false,
    end_fixed: payload.end_fixed ?? false,
    round_trip: payload.round_trip ?? true,
    mode: payload.mode ?? "driving-traffic",
  });
}

export async function benchmarkAlgorithms(
  payload: OptimizeRequest & { time_limit_s?: number },
): Promise<BenchmarkResponse> {
  return postJson<BenchmarkResponse>("/benchmark-algorithms", {
    stops: payload.stops,
    start_fixed: payload.start_fixed ?? false,
    end_fixed: payload.end_fixed ?? false,
    round_trip: payload.round_trip ?? true,
    mode: payload.mode ?? "driving-traffic",
    time_limit_s: payload.time_limit_s ?? 8,
  });
}

export async function searchPlaces(
  query: string,
  options?: { limit?: number; signal?: AbortSignal },
): Promise<PlaceSuggestion[]> {
  const params = new URLSearchParams({ q: query });
  if (options?.limit != null) {
    params.set("limit", String(options.limit));
  }
  const response = await fetch(`${API_BASE}/search-places?${params}`, {
    signal: options?.signal,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string" ? body.detail : `Search failed (${response.status})`;
    throw new Error(detail);
  }
  return response.json() as Promise<PlaceSuggestion[]>;
}

export async function reverseGeocode(lat: number, lng: number): Promise<string> {
  const response = await fetch(
    `${API_BASE}/reverse-geocode?lat=${lat}&lng=${lng}`,
  );
  if (!response.ok) {
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  }
  const body = (await response.json()) as { name?: string };
  return body.name ?? `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
