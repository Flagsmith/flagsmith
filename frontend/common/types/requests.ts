export type PagedRequest<T> =  T & {
  page?:number
  q?:string
  page_size?: number
}

export type Req = {
  getSegments: PagedRequest<{
    projectId: string
  }>
  // END OF TYPES
}
