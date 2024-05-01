import { FC, ReactNode, useEffect, useState } from 'react'
import OrganisationStore from 'common/stores/organisation-store'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import {
  Invite,
  InviteLink,
  Project,
  SubscriptionMeta,
  User,
  UserGroupSummary,
} from 'common/types/responses'
import { useGetGroupsQuery } from 'common/services/useGroup'

type OrganisationProviderType = {
  onRemoveProject?: () => void
  onSave?: (data: { environmentId: number; projectId: number }) => void
  id?: number | string
  children: (props: {
    createProject: typeof AppActions.createProject
    invalidateInviteLink: typeof AppActions.invalidateInviteLink
    inviteLinks: InviteLink[] | null
    invites: Invite[] | null
    error: any
    isLoading: boolean
    isSaving: boolean
    name: string
    project: Project | null
    groups: UserGroupSummary[] | null
    projects: Project[] | null
    subscriptionMeta: SubscriptionMeta | null
    users: User[]
  }) => ReactNode
}

const OrganisationProvider: FC<OrganisationProviderType> = ({
  children,
  id,
  onRemoveProject,
  onSave,
}) => {
  const [_, setUpdate] = useState(Date.now())
  const { data: groups } = useGetGroupsQuery(
    { orgId: id!, page: 1 },
    { skip: !id },
  )
  useEffect(() => {
    const _onRemoveProject = () => onRemoveProject?.()
    OrganisationStore.on('removed', _onRemoveProject)
    return () => {
      OrganisationStore.off('removed', _onRemoveProject)
    }
    //eslint-disable-next-line
  }, [])

  useEffect(() => {
    const _onSave = () => onSave?.(OrganisationStore.savedId)
    OrganisationStore.on('saved', _onSave)
    return () => {
      OrganisationStore.off('saved', _onSave)
    }
    //eslint-disable-next-line
  }, [])

  useEffect(() => {
    const onChange = () => {
      setUpdate(Date.now())
    }
    OrganisationStore.on('change', onChange)
    return () => {
      OrganisationStore.off('change', onChange)
    }
    //eslint-disable-next-line
  }, [])

  return (
    <>
      {children({
        createProject: AppActions.createProject,
        error: AccountStore.error,
        groups: groups?.results || [],
        invalidateInviteLink: AppActions.invalidateInviteLink,
        inviteLinks: OrganisationStore.getInviteLinks(),
        invites: OrganisationStore.getInvites(),
        isLoading: OrganisationStore.isLoading,
        isSaving: OrganisationStore.isSaving,
        name: AccountStore.getOrganisation()?.name || '',
        project: OrganisationStore.getProject(id),
        projects: OrganisationStore.getProjects(),
        subscriptionMeta: OrganisationStore.getSubscriptionMeta(),
        users: OrganisationStore.getUsers(),
      })}
    </>
  )
}

export default OrganisationProvider
