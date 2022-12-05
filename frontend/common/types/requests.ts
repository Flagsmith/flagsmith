export type PagedRequest<T> =  T & {
  page?:number
  q?:string
  page_size?: string
}

export type Req = {
  getSegments: PagedRequest<{
    projectId: string
  }>
  // END OF TYPES
}
