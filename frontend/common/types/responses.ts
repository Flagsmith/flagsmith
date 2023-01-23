// eslint-disable-next-line @typescript-eslint/no-empty-interface
export type PagedResponse<T> = {
  count?: number;
  next?: string;
  previous?: string;
  results: T[];
}
export type FlagsmithValue = string | number | boolean | null
export type SegmentRule = {
  type: string;
  rules: SegmentRule[];
  conditions: {
    operator: string;
    property: string;
    value: FlagsmithValue;
  }[];
}
export type Segment = {
  id: number;
  rules: SegmentRule[];
  uuid: string;
  name: string;
  description: string;
  project: number;
  feature?: number;
}
export type Environment = {
  id: number;
  name: string;
  api_key: string;
  description?: string;
  project: number;
  minimum_change_request_approvals?: number;
  allow_client_traits: boolean;
}
export type Project = {
  id: number;
  uuid: string;
  name: string;
  organisation: number;
  hide_disabled_flags: boolean;
  enable_dynamo_db: boolean;
  migration_status: string;
  use_edge_identities: boolean;
  prevent_flag_defaults: boolean;
  enable_realtime_updates: boolean;
  environments: Environment[];
}
export type AuditLogItem = {
  id: number;
  created_date: string;
  log: string;
  author?: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  environment?: Environment;
  project: Omit<Project, 'environments'>;
  related_object_id: number;
  related_object_type: string;
  is_system_event: boolean;
}


export type Res = {
  segments: PagedResponse<Segment>;
  segment: {id:string};
  auditLogs: PagedResponse<AuditLogItem>;
  organisationUsage: {
    totals: {
      flags: number;
      environmentDocument: number;
      identities: number;
      traits: number;
      total: number;
    };
    events_list: {
      "Environment-document": number|null;
      Flags: number|null;
      Identities: number|null;
      Traits: number|null;
      name: string;
    }[]
  }
  // END OF TYPES
}
