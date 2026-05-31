export interface Stop {
  lat: number;
  lng: number;
  name: string;
}

export interface PlaceSuggestion {
  name: string;
  lat: number;
  lng: number;
  subtitle?: string;
}

export interface OrderedStop {
  sequence: number;
  index: number;
  name: string;
  lat: number;
  lng: number;
}

export interface OptimizeResponse {
  order: number[];
  ordered_stops: OrderedStop[];
  total_distance_m: number;
  total_duration_s: number;
  mode: string;
  round_trip: boolean;
  solver?: string;
  profile_source?: string | null;
}

export interface OptimizeRequest {
  stops: Stop[];
  start_fixed?: boolean;
  end_fixed?: boolean;
  round_trip?: boolean;
  mode?: string;
}
