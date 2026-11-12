import { useSelector } from 'react-redux'
import { useGetOrganisationsQuery } from 'common/services/useOrganisation'
import { StoreStateType } from 'common/store'

const useSelectedOrganisation = () => {
  const selectedId = useSelector(
    (state: StoreStateType) => state.selectedOrganisation?.id,
  )
  const { data: organisationsData } = useGetOrganisationsQuery({})
  const organisation = organisationsData?.results?.find(
    (org) => org.id === selectedId,
  )

  return organisation
}

export default useSelectedOrganisation
