export interface Stop {
  lat: number;
  lng: number;
  name: string;
}

export interface OrderedStop {
  sequence: number;
  index: number;
  name: string;
  lat: number;
  lng: number;
}

export interface Leg {
  from_index: number;
  to_index: number;
  distance_m: number;
  duration_s: number;
}

export interface OptimizeResponse {
  order: number[];
  ordered_stops: OrderedStop[];
  total_distance_m: number;
  total_duration_s: number;
  legs: Leg[];
  mode: string;
  round_trip: boolean;
  solver?: string;
}

export interface OptimizeRequest {
  stops: Stop[];
  start_fixed?: boolean;
  end_fixed?: boolean;
  round_trip?: boolean;
  mode?: string;
}
