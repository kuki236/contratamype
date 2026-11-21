export interface OpportunitySummary {
  ocid: string;
  title: string | null;
  description: string | null;
  category: string | null;
  method: string | null;
  amount_pen: number | null;
  currency: string | null;
  published_date: string | null;
  tender_start: string | null;
  tender_end: string | null;
  status: string | null;
  buyer_id: string | null;
  buyer_name: string | null;
  department: string | null;
  department_code: string | null;
  segmentation_id: string | null;
  segmentation_year: number | null;
  mype_fit: boolean | null;
  dates_valid: boolean | null;
  period_start_eq_end: boolean | null;
}

export interface Buyer {
  id: string | null;
  name: string | null;
  ruc: string | null;
  department: string | null;
}

export interface Supplier {
  id: string | null;
  name: string | null;
  ruc: string | null;
  department: string | null;
}

export interface Award {
  award_id: string | null;
  supplier: Supplier | null;
  supplier_name: string | null;
  amount_pen: number | null;
  award_date: string | null;
  status: string | null;
}

export interface Contract {
  contract_id: string | null;
  award_id: string | null;
  award_linked: boolean;
  amount_pen: number | null;
  signed_date: string | null;
  status: string | null;
}

export interface DataQuality {
  missing_description: boolean;
  amount_reported: boolean;
  start_eq_end: boolean;
  has_awards: boolean;
  has_contracts: boolean;
  awards_without_supplier: number;
  contracts_without_award: number;
  buyer_missing: boolean;
  department_missing: boolean;
}

export interface OpportunityDetail extends OpportunitySummary {
  buyer: Buyer | null;
  awards: Award[];
  contracts: Contract[];
  data_quality: DataQuality;
}

export interface OpportunityPage {
  items: OpportunitySummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Meta {
  cohort_year: number;
  departments: string[];
  categories: string[];
  methods: string[];
  statuses: string[];
  amount_min: number | null;
  amount_max: number | null;
  currency: string;
}

export interface DepartmentStat {
  department: string;
  total: number;
  mype: number;
}

export interface CategoryStat {
  category: string;
  total: number;
  mype: number;
}

export interface MethodStat {
  method: string;
  total: number;
  mype: number;
}

export interface Stats {
  year: number;
  total: number;
  mype_opportunities: number;
  missing_description: number;
  zero_amount: number;
  start_eq_end: number;
  amount: { min: number | null; max: number | null; median: number | null };
  by_department: DepartmentStat[];
  by_category: CategoryStat[];
  by_method: MethodStat[];
}

export interface ChecklistProcess {
  title: string | null;
  buyer_name: string | null;
  department: string | null;
  amount_pen: number | null;
  published_date: string | null;
  tender_start: string | null;
  tender_end: string | null;
  category: string | null;
  method: string | null;
  mype_fit: boolean | null;
}

export interface ChecklistItem {
  id: string;
  title: string;
  detail: string;
  source: string;
}

export interface ChecklistSource {
  name: string;
  url: string;
  license: string;
}

export interface Checklist {
  ocid: string;
  process: ChecklistProcess;
  source: ChecklistSource;
  items: ChecklistItem[];
  warnings: string[];
  disclaimer: string;
}
