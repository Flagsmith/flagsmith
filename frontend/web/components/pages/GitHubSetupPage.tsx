import React, { FC, useState } from 'react'
import OrganisationSelect from 'components/OrganisationSelect'
import ProjectFilter from 'components/ProjectFilter'
import Button from 'components/base/forms/Button'

// TOKEN="1e53bb7272aabf4ceea2b2f7f585f28f1a6926e0"
// PROYECT_ID=13042
// ORG_ID=11499
// ENV_KEY=f8eEr3XpYwHGdjTxfTNdLt
// onClick={closeModal}

type GitHubSetupPageType = {}
const GitHubSetupPage: FC<GitHubSetupPageType> = (props) => {
  const [organisation, setOrganisation] = useState<number>()
  const [project, setProject] = useState<number>()

  return (
    <div
      id='login-page'
      style={{ flexDirection: 'column' }}
      className='ml-4 bg-light200'
    >
      <h3>Configure your integration with GitHub</h3>
      <div className='mr-4 mb-4'>
        <p>Select your Organisation</p>
        <OrganisationSelect
          onChange={(organisationId) => {
            setOrganisation(organisationId)
          }}
        />
      </div>
      {organisation && (
        <div className='mr-4 mb-4' style={{ width: '500px' }}>
          <p>Select your Project</p>
          <ProjectFilter
            showAll
            organisationId={organisation}
            onChange={setProject}
            value={project}
          />
        </div>
      )}
      <Button className='mr-2 text-right' theme='primary'>
        Save
      </Button>
    </div>
  )
}

export default GitHubSetupPage
