// TypeScript types mirroring backend Pydantic schemas

export interface Company {
  id: string;
  name: string;
  short_name: string;
  tax_id: string | null;
  is_holding: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BankAccount {
  id: string;
  company_id: string;
  company_name?: string | null;
  company_short_name?: string | null;
  bank_name: string;
  account_name: string;
  iban: string;
  currency: string;
  is_internal: boolean;
  is_active: boolean;
}

export interface ImportBatch {
  id: string;
  company_id: string;
  bank_account_id: string;
  filename: string;
  file_hash: string;
  file_format: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "DUPLICATE";
  row_count: number | null;
  imported_count: number;
  error_count: number;
  error_log: unknown[];
  imported_by: string;
  imported_at: string;
  processed_at: string | null;
  notes: string | null;
}

export type CashFlowSection = "OPERATING" | "INVESTING" | "FINANCING" | "INTERNAL" | "UNCLASSIFIED";
export type ClassificationSource = "RULE" | "MANUAL" | "AI_SUGGESTION";

// Embedded classification returned by the movements API
export interface ClassificationInfo {
  category_code: string;
  category_name: string | null;
  cash_flow_section: CashFlowSection | null;
  subcategory_code: string | null;
  source: ClassificationSource;
  is_confirmed: boolean;
  classified_at: string;
  override_reason: string | null;
}

export interface Movement {
  id: string;
  company_id: string;
  company_short_name: string | null;
  bank_account_id: string;
  bank_name: string | null;
  import_batch_id: string;
  value_date: string;
  accounting_date: string | null;
  amount: string;
  currency: string;
  balance_after: string | null;
  description: string;
  counterpart_name: string | null;
  counterpart_iban: string | null;
  reference: string | null;
  is_intercompany: boolean;
  created_at: string;
  is_deleted: boolean;
  classification: ClassificationInfo | null;
}

// Full classification row (used by classification engine pages)
export interface MovementClassification {
  id: string;
  movement_id: string;
  category_code: string;
  subcategory_code: string | null;
  source: ClassificationSource;
  rule_id: string | null;
  confidence: string | null;
  is_confirmed: boolean;
  classified_by: string;
  classified_at: string;
  override_reason: string | null;
  previous_category_code: string | null;
}

export interface CategoryTaxonomy {
  code: string;
  parent_code: string | null;
  name: string;
  description: string;
  cash_flow_section: CashFlowSection;
  level: number;
  is_active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type MatchType = "KEYWORD" | "REGEX" | "COUNTERPART_NAME" | "AMOUNT_RANGE" | "COMPOSITE";

export interface ClassificationRule {
  id: string;
  name: string;
  priority: number;
  is_active: boolean;
  match_type: MatchType;
  match_field: string;
  match_pattern: string;
  category_code: string;
  subcategory_code: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BatchClassifyResponse {
  processed: number;
  classified: number;
  unclassified: number;
  overrides_preserved: number;
}

export interface ApiError {
  error: string;
  message: string;
  details: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Intercompany
// ---------------------------------------------------------------------------

export type MatchStatus = "IN_TRANSIT" | "PROPOSED" | "CONFIRMED" | "REJECTED" | "UNRESOLVED";
export type MatchMethod = "AUTOMATIC" | "MANUAL";

export interface MovementSummary {
  id: string;
  company_id: string;
  company_short_name: string | null;
  bank_account_id: string;
  bank_name: string | null;
  value_date: string;
  amount: string;
  description: string;
  counterpart_name: string | null;
  counterpart_iban: string | null;
}

export interface IntercompanyMatch {
  id: string;
  movement_out_id: string;
  movement_in_id: string | null;
  company_from_id: string;
  company_from_name: string | null;
  company_to_id: string | null;
  company_to_name: string | null;
  amount: string;
  match_date: string;
  status: MatchStatus;
  match_method: MatchMethod;
  score: string | null;
  transit_expires_at: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
  rejection_reason: string | null;
  notes: string | null;
  created_at: string;
  movement_out: MovementSummary | null;
  movement_in: MovementSummary | null;
}

export interface CompanyPairSummary {
  company_from_id: string;
  company_from_name: string | null;
  company_to_id: string;
  company_to_name: string | null;
  total_out: string;
  total_in: string;
  net: string;
  confirmed_count: number;
}

export interface IntercomparySummary {
  pairs: CompanyPairSummary[];
  pending_proposed: number;
  in_transit: number;
  unresolved: number;
}

export interface ScanResponse {
  new_transit: number;
  new_proposed: number;
  escalated: number;
}

export interface ForeignEntity {
  id: string;
  name: string;
  country: string;
  known_ibans: string[];
  keyword_patterns: string[];
  is_active: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Analytics / Dashboard
// ---------------------------------------------------------------------------

export interface CompanyCashPosition {
  company_id: string;
  company_name: string;
  short_name: string;
  last_balance: string | null;  // null when no balance_after data
  net_flow: string;
  has_balance_data: boolean;
}

export interface WeeklyCashFlow {
  week_start: string;   // YYYY-MM-DD (Monday)
  week_label: string;   // "W20 2026"
  inflow: string;
  outflow: string;
  net: string;
}

export interface DashboardSummary {
  cash_by_company: CompanyCashPosition[];
  total_cash: string;
  net_flow_wtd: string;
  pending_ic_matches: number;
  in_transit_ic: number;
  unresolved_ic: number;
  weekly_cash_flow: WeeklyCashFlow[];
  as_of: string;
}

export type CashFlowGranularity = "weekly" | "monthly";

export interface CashFlowPeriod {
  key: string;
  label: string;
  start_date: string;
  end_date: string;
}

export interface CashFlowRow {
  section: CashFlowSection;
  category_code: string;
  category_name: string;
  values: string[];
  total: string;
}

export interface CashFlowSectionSummary {
  section: CashFlowSection;
  values: string[];
  total: string;
}

export interface CashFlowStatement {
  granularity: CashFlowGranularity;
  date_from: string;
  date_to: string;
  company_id: string | null;
  include_intercompany: boolean;
  periods: CashFlowPeriod[];
  sections: CashFlowSectionSummary[];
  rows: CashFlowRow[];
  net_cash_flow: string[];
  net_cash_flow_total: string;
  as_of: string;
}

// ---------------------------------------------------------------------------
// Consistency & Completeness Panel
// ---------------------------------------------------------------------------

export type ImportCoverageStatus = "OK" | "PARTIAL" | "MISSING";

export interface AccountImportStatus {
  bank_account_id: string;
  account_name: string;
  bank_name: string;
  company_name: string;
  short_name: string;
  iban_last4: string;
  movement_count: number;
  earliest_movement: string | null;
  latest_movement: string | null;
  last_batch_at: string | null;
  status: ImportCoverageStatus;
}

export type ReconciliationStatus = "OK" | "WARNING" | "ERROR" | "NO_DATA";

export interface BalanceReconciliation {
  bank_account_id: string;
  account_name: string;
  bank_name: string;
  company_name: string;
  period_label: string;
  opening_balance: string | null;
  closing_balance_bank: string | null;
  closing_balance_computed: string | null;
  delta: string | null;
  status: ReconciliationStatus;
}

export interface DataQualityWarning {
  rule: string;
  company_name: string;
  account_name: string | null;
  movement_id: string | null;
  movement_date: string | null;
  movement_amount: string | null;
  description: string;
}

export interface UnclassifiedRateWarning {
  company_name: string;
  total_movements: number;
  unclassified_count: number;
  unclassified_rate: number;
}

export interface ConsistencyReport {
  period_year: number;
  period_month: number;
  period_label: string;
  section_a: AccountImportStatus[];
  section_b: BalanceReconciliation[];
  holdco_revenue_warnings: DataQualityWarning[];
  high_unclassified_companies: UnclassifiedRateWarning[];
  unresolved_ic_count: number;
  in_transit_timeout_count: number;
  as_of: string;
}
