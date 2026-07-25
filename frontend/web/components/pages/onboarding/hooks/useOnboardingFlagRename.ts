import {
  useCreateProjectFlagMutation,
  useGetProjectFlagsQuery,
  useRemoveProjectFlagMutation,
} from 'common/services/useProjectFlag'
import { Environment } from 'common/types/responses'
import { Req } from 'common/types/requests'

type UseOnboardingFlagRenameArgs = {
  projectId: number | null
  environment: Environment | null
  featureName: string
}

// "Rename" the flag. Feature names are immutable (the API marks `name`
// read-only), so this is a delete + recreate: create first (no name conflict),
// then drop the old one, carrying over its tags/type/description so the
// Onboarding badge survives. Resolves true on success.
export const useOnboardingFlagRename = ({
  environment,
  featureName,
  projectId,
}: UseOnboardingFlagRenameArgs) => {
  const { data: projectFlags, refetch } = useGetProjectFlagsQuery(
    {
      environment: environment?.id,
      project: `${projectId}`,
    },
    { skip: !projectId || !environment },
  )
  const [createProjectFlag] = useCreateProjectFlagMutation()
  const [removeProjectFlag] = useRemoveProjectFlagMutation()

  const flag = projectFlags?.results?.find((f) => f.name === featureName)

  const rename = async (name: string): Promise<boolean> => {
    if (!flag || projectId === null || name === flag.name) {
      return false
    }
    try {
      await createProjectFlag({
        body: {
          description: flag.description,
          name,
          project: projectId,
          tags: flag.tags,
          type: flag.type,
        } as Req['createProjectFlag']['body'],
        project_id: projectId,
      }).unwrap()
      await removeProjectFlag({
        flag_id: flag.id,
        project_id: projectId,
      }).unwrap()
      refetch()
      return true
    } catch {
      return false
    }
  }

  // isReady lets the caller tell a real failure from a rename fired pre-load.
  return { isReady: !!flag, rename }
}
