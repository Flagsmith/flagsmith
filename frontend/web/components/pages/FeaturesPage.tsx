import { FC, useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import Format from 'common/utils/format'
import { useGetTagsQuery } from 'common/services/useTag'
import { Req } from 'common/types/requests'
import { AsyncStorage } from 'polyfill-react-native'
import AccountStore from 'common/stores/account-store'
import CreateFlag from 'components/modals/CreateFlag'
import { RouterChildContext } from 'react-router'

type FeaturesPageType = {
  match: {
    params: {
      projectId: string
      environmentId: string
    }
  }
  router: RouterChildContext['router']
}

const FeaturesPage: FC<FeaturesPageType> = ({ match, router }) => {
  const { environmentId, projectId } = match.params
  const params = Utils.fromParam()
  const [is_enabled, setIsEnabled] = useState(
    params.is_enabled === 'true'
      ? true
      : params.is_enabled === 'false'
      ? false
      : null,
  )
  const [owners, setOwners] = useState<string[]>(
    params.owners ? params.owners.split(',') : [],
  )
  const [group_owners, setGroupOwners] = useState<string[]>(
    params.group_owners ? params.group_owners.split(',') : [],
  )
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [is_archived, setIsArchived] = useState(
    params.is_enabled === 'true'
      ? true
      : params.is_enabled === 'false'
      ? false
      : null,
  )
  const [sort, setSort] = useState({
    label: Format.camelCase(params.sortBy || 'Name'),
    sortBy: params.sortBy || 'name',
    sortOrder: params.sortOrder || 'asc',
  })
  const [tag_strategy, setTagStrategy] = useState(
    params.tag_strategy || 'INTERSECTION',
  )
  const [tags, setTags] = useState(
    typeof params.tags === 'string'
      ? params.tags.split(',').map((v: string) => parseInt(v))
      : [],
  )
  const [value_search, setValueSearch] = useState()

  const { data: tags } = useGetTagsQuery({ projectId })
  useEffect(() => {
    AsyncStorage.setItem(
      'lastEnv',
      JSON.stringify({
        environmentId: environmentId,
        orgId: AccountStore.getOrganisation().id,
        projectId: projectId,
      }),
    )
  }, [environmentId, projectId])
  const newFlag = () => {
    openModal(
      'New Feature',
      <CreateFlag
        history={router.history}
        environmentId={environmentId}
        projectId={projectId}
      />,
      'side-modal create-feature-modal',
    )
  }
  const getURLParams = () => ({
    ...getFilter(),
    group_owners: (group_owners || [])?.join(',') || undefined,
    owners: (owners || [])?.join(',') || undefined,
    page: page || 1,
    search: search || '',
    sortBy: sort.sortBy,
    sortOrder: sort.sortOrder,
    tags: (tags || [])?.join(',') || undefined,
  })

  const getFilter = () => ({
    group_owners: group_owners?.length ? group_owners : undefined,
    is_archived,
    is_enabled: is_enabled === null ? undefined : is_enabled,
    owners: owners?.length ? owners : undefined,
    tag_strategy,
    tags: !tags || !tags.length ? undefined : tags.join(','),
    value_search: value_search ? value_search : undefined,
  })
  return <></>
}

export default FeaturesPage
