import React, { ComponentType } from 'react'
import { Organisation } from 'common/types/responses'
import { useCurrentOrganisation } from './useCurrentOrganisation'

export type CurrentOrganisationProps = {
  organisation: Organisation | undefined
}

// For class components, which cannot call the hook.
const withCurrentOrganisation = <P extends object>(
  Component: ComponentType<P & CurrentOrganisationProps>,
) => {
  const WithCurrentOrganisation = (props: P) => {
    const organisation = useCurrentOrganisation()
    return <Component {...props} organisation={organisation} />
  }
  return WithCurrentOrganisation
}

export default withCurrentOrganisation
