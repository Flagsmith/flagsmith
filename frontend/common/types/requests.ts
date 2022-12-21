import {Segment, Tag} from "./responses";

export type PagedRequest<T> =  T & {
  page?:number
  page_size?: number
}
export type PermissionLevel = "organisation" | "project" | "environment"
export type Req = {
  getSegments: PagedRequest<{
    q?:string
    projectId: string
    identity?:number
  }>
  deleteSegment: {projectId:string, id:number}
  updateSegment: {projectId:string, segment: Segment}
  createSegment: {projectId:string, segment: Omit<Segment,"id"|"uuid"|"project">}
  getAuditLogs: PagedRequest<{
    search?:string
    project: string
    environments?: string
  }>
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
  getTag: {id:string}
  updateTag: {projectId: string, tag:Tag}
  deleteTag: {
    id: number
    projectId: string
  }
  getTags: {
    projectId: string
  }
  createTag: {projectId: string, tag:Omit<Tag,"id">}
  getSegment: {projectId: string, id:string}
  // END OF TYPES
}
