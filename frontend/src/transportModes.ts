export const TRANSPORT_MODES = [
  { id: "driving-traffic", label: "Driving", icon: "🚗" },
  { id: "walking", label: "Walking", icon: "🚶" },
  { id: "cycling", label: "Cycling", icon: "🚴" },
] as const;

export type TransportModeId = (typeof TRANSPORT_MODES)[number]["id"];
