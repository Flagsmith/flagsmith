// eslint-disable-next-line @typescript-eslint/no-empty-interface
export type EdgePagedResponse<T> = PagedResponse<T> & {last_evaluated_key?:string, pages?:(string|undefined)[]}
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
export type Project =  {
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

export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: "ADMIN" | "USER"
}

export type UserGroup = {
  external_id: string|null
  id: number
  is_default: boolean
  name:string
  users: User[]
}

export type UserPermission = {
  user: User
  permissions: string[]
  admin: boolean
  id:number
}

export type AuditLogItem = {
  id: number;
  created_date: string;
  log: string;
  author?: User;
  environment?: Environment;
  project: Omit<Project, 'environments'>;
  related_object_id: number;
  related_object_type: string;
  is_system_event: boolean;
}

export type Identity = {
  id?: string
  identifier: string
  identity_uuid?: string
}

export type Res = {
  segments: PagedResponse<Segment>;
  segment: {id:string};
  auditLogs: PagedResponse<AuditLogItem>;
  identity: {id:string} //todo: we don't consider this until we migrate identity-store
  identities: EdgePagedResponse<Identity>
  permission: Record<string, boolean>
  availablePermissions: {id:string}
  // END OF TYPES
}
