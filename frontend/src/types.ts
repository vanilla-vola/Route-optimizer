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
  provider_ids?: string[];
  algorithm_ids?: string[];
  time_limit_s?: number;
}

export interface AlgorithmInfo {
  id: string;
  label: string;
  paper: string;
  year: number;
  category: string;
}

export interface CompareProviderInfo {
  id: string;
  label: string;
  kind: string;
  max_stops?: number | null;
  requires_key?: string;
}

export interface CompareResultItem {
  provider_id: string;
  provider_label: string;
  status: string;
  order?: number[] | null;
  ordered_stops?: OrderedStop[] | null;
  total_duration_s?: number | null;
  total_distance_m?: number | null;
  vs_baseline_duration_pct?: number | null;
  message?: string;
  manual_url?: string | null;
  is_baseline?: boolean;
}

export interface CompareResponse {
  stop_count: number;
  mode: string;
  round_trip: boolean;
  profile_source: string;
  results: CompareResultItem[];
}

export interface BenchmarkResultItem {
  algorithm_id: string;
  algorithm_label: string;
  paper: string;
  year: number;
  category: string;
  status: string;
  order?: number[] | null;
  total_duration_s?: number | null;
  total_distance_m?: number | null;
  vs_best_duration_pct?: number | null;
  notes?: string;
  error?: string;
}

export interface BenchmarkResponse {
  stop_count: number;
  mode: string;
  round_trip: boolean;
  profile_source: string;
  results: BenchmarkResultItem[];
  best_algorithm_id?: string | null;
}
