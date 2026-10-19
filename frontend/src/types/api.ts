export type InvestigationStatus = 'draft' | 'active' | 'on_hold' | 'closed' | 'archived';
export type InvestigationPriority = 'low' | 'medium' | 'high' | 'critical';

export type EvidenceType =
  | 'blockchain_transaction'
  | 'wallet_address'
  | 'ip_address'
  | 'domain'
  | 'file_hash'
  | 'malware_sample'
  | 'threat_intel_indicator'
  | 'exchange_record'
  | 'network_artifact'
  | 'other';

export type EvidenceAssessment =
  | 'unverified'
  | 'provider_supplied'
  | 'corroborated'
  | 'contradicted'
  | 'analyst_confirmed'
  | 'analyst_rejected';

export interface Investigation {
  id: string;
  title: string;
  description: string | null;
  status: InvestigationStatus;
  priority: InvestigationPriority;
  tags: string[] | null;
  case_reference: string | null;
  is_archived: boolean;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
  evidence_count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CreateInvestigationRequest {
  title: string;
  description?: string;
  status?: InvestigationStatus;
  priority?: InvestigationPriority;
  tags?: string[];
  case_reference?: string;
}

export interface UpdateInvestigationRequest {
  title?: string;
  description?: string;
  status?: InvestigationStatus;
  priority?: InvestigationPriority;
  tags?: string[];
  case_reference?: string;
}

export interface HealthStatus {
  status: 'ok' | 'degraded';
  service: string;
  version: string;
  database: 'ok' | 'unavailable';
  details?: Record<string, unknown>;
}

export interface InvestigationSummary {
  status_counts: Record<string, number>;
}
