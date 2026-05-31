export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const minutes = seconds / 60;
  return minutes >= 60 ? `${(minutes / 60).toFixed(1)} hr` : `${minutes.toFixed(1)} min`;
}

export function formatDistance(meters: number | null | undefined): string {
  if (meters == null) return "—";
  return meters >= 1000 ? `${(meters / 1000).toFixed(2)} km` : `${meters} m`;
}

export function formatPct(pct: number | null | undefined): string {
  if (pct == null) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

export function formatProfileSource(source: string | null | undefined): string {
  if (!source) return "—";
  if (source === "mapbox-depart-at") return "Mapbox traffic (8am / 1pm / 6pm)";
  if (source === "synthetic") return "Synthetic traffic profiles";
  return source;
}

export function nominalVsRealizedPct(
  nominal: number | null | undefined,
  realized: number | null | undefined,
): string | null {
  if (nominal == null || realized == null || nominal <= 0) return null;
  const pct = ((realized - nominal) / nominal) * 100;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}% vs nominal`;
}
