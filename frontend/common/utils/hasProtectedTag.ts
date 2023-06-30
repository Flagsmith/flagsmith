import { getStore } from 'common/store'
import { ProjectFlag, Tag } from 'common/types/responses'
import { tagService } from 'common/services/useTag'

export const hasProtectedTag = (
  projectFlag: ProjectFlag,
  projectId: string,
) => {
  const store = getStore()
  const tags: Tag[] =
    tagService.endpoints.getTags.select({ projectId: `${projectId}` })(
      store.getState(),
    ).data || []
  return !!projectFlag.tags?.find((id) => {
    const tag = tags.find((tag) => tag.id === id)
    if (tag) {
      const label = tag.label.toLowerCase().replace(/[ _]/g, '')
      return (
        label === 'protected' ||
        label === 'donotdelete' ||
        label === 'permanent'
      )
    }
  })
}
