// eslint-disable-next-line @typescript-eslint/no-empty-interface
export type PagedResponse<T> = {
  count?: number
  next?: string
  previous?: string
  results: T[]
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
  feature?: any;
}
export type Res = {
  segments: PagedResponse<Segment>
  segment: {id:string}
  // END OF TYPES
}
