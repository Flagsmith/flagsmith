import {Segment} from "./responses";

export type PagedRequest<T> =  T & {
  page?:number
  page_size?: number
}

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
  // END OF TYPES
}
