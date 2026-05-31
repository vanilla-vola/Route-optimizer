import type { OptimizeRequest, OptimizeResponse } from "../types";

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
      mode: payload.mode ?? "driving",
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
