export interface Experiment {
  id: string;
  name: string;
  description: string | null;
  status: string
  created_at: string;
  updated_at: string;
}

export interface Variant {
  id: string;
  experiment_id: string;
  name: string;
  traffic_weight: number;
  created_at: string;
}

export interface VariantResult {
  variant_id: string;
  variant_name: string;
  users: number;
  conversions: number;
  conversion_rate: number;
}

export interface ExperimentResult {
  experiment_id: string;
  variants: VariantResult[];
  p_value: number | null;
  significant: boolean;
  winner: string | null; 
}
