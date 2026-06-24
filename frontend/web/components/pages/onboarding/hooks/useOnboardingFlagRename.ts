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

// "Rename" the onboarding flag. Feature names are immutable once created
// (UpdateFeatureSerializer marks `name` read-only), so this is a delete +
// recreate under the hood - safe here because the flag is freshly bootstrapped
// and not yet depended on. Recreate first (names differ, so no unique conflict)
// and only then drop the old one, so a flag always exists even if the second
// call fails. The recreate carries over the old flag's tags/type/description so
// the Onboarding badge (and any other tag) survives the rename. Resolves true
// on success.
//
// The toggle that will also act on this flag lives in #7766 (the flags table);
// this hook is intentionally rename-only so the connect-panel issue doesn't pull
// in the feature-toggle path.
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

  // isReady distinguishes "rename failed" from "the flag hasn't loaded yet", so
  // the caller doesn't show an error for a rename fired before the query settles.
  return { isReady: !!flag, rename }
}
