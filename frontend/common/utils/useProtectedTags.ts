import { ProjectFlag, Tag } from 'common/types/responses'
import { useGetTagsQuery } from 'common/services/useTag'

export const useProtectedTags = (
  projectFlag: ProjectFlag,
  projectId: string,
  skip?: boolean,
): Tag[] | undefined => {
  const { data: tags } = useGetTagsQuery(
    { projectId },
    { skip: skip || !projectId },
  )

  if (!tags) {
    return undefined
  }

  const protectedFlags = projectFlag.tags.reduce<Tag[]>((acc, id) => {
    const tag = tags?.find((t) => t.id === id)
    if (tag?.is_permanent) {
      acc.push(tag)
    }
    return acc
  }, [])

  return protectedFlags
}
