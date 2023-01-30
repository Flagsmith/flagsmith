import {Segment} from "./responses";

export type PagedRequest<T> =  T & {
  page?:number
  page_size?: number
}
export type PermissionLevel = "organisation" | "project" | "environment"
export type Req = {
  getSegments: PagedRequest<{
    q?:string
    projectId: string
  }>
  deleteSegment: {projectId:string, id:number}
  updateSegment: {projectId:string, id:number, segment: Segment}
  createSegment: {projectId:string, id:number, segment: Omit<Segment,"id">}
  getAuditLogs: PagedRequest<{
    search?:string
    project: string
    environments?: string
  }>
  getOrganisations: {}
  getProjects: {
    organisationId: string
  }
  getEnvironments: {
    projectId: string
  }
  getOrganisationUsage: {
    organisationId: string
    projectId?:string
    environmentId?:string
  }
  deleteIdentity: {
    id: string
    environmentId: string
    isEdge: boolean
  }
  createIdentities: {
    isEdge: boolean
    environmentId: string
    identifiers: string[]
  }
  getIdentities: PagedRequest<{
    environmentId: string
    pageType?: "NEXT" | "PREVIOUS"
    search?:string
    pages?: (string|undefined)[] // this is needed for edge since it returns no paging info other than a key
    isEdge: boolean
  }>
  getPermission: {id:string, level: PermissionLevel}
  getAvailablePermissions: {level:PermissionLevel}
  // END OF TYPES
}
