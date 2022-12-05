import {Segment} from "./responses";

export type PagedRequest<T> =  T & {
  page?:number
  q?:string
  page_size?: number
}

export type Req = {
  getSegments: PagedRequest<{
    projectId: string
  }>
  deleteSegment: {projectId:string, id:number}
  updateSegment: {projectId:string, id:number, segment: Segment}
  createSegment: {projectId:string, id:number, segment: Omit<Segment,"id">}
  // END OF TYPES
}
