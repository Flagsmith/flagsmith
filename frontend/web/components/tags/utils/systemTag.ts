import { Tag as TTag } from 'common/types/responses'

export const isSystemTag = (tag: Partial<TTag>): boolean =>
  !!tag.type && tag.type !== 'NONE'
