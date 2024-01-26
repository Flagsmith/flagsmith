import React, { FC, useState, useEffect } from 'react'
import OrganisationSelect from 'components/OrganisationSelect'
import ProjectFilter from 'components/ProjectFilter'
import Button from 'components/base/forms/Button'
import { useCreateExternalResourceMutation } from 'common/services/useExternalResource'

type GitHubSetupPageType = {}
const GitHubSetupPage: FC<GitHubSetupPageType> = (props) => {
  const [organisation, setOrganisation] = useState<number>()
  const [project, setProject] = useState<number>()
  const [externalResourceURL, setExternalResourceURL] = useState<string>('')

  const [createExternalResourceMutation, { isSuccess }] =
    useCreateExternalResourceMutation()

  useEffect(() => {
    toast('Saved')
  }, [isSuccess])

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
          showSettings={false}
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
      <InputGroup
        value={externalResourceURL}
        data-test='ExternalResourceURL'
        inputProps={{
          className: 'full-width',
          name: 'featureExternalResourceURL',
        }}
        onChange={(e) => setExternalResourceURL(Utils.safeParseEventValue(e))}
        ds
        type='text'
        title={'GitHub Issue/Pull Request URL'}
        placeholder="e.g. 'https://github.com/user/repo-example/issues/12' "
      />
      <Button
        className='mr-2 text-right'
        theme='primary'
        onClick={() => {
          createExternalResourceMutation({
            project: project,
            type: 'Github',
            url: externalResourceURL,
          })
        }}
      >
        Save
      </Button>
    </div>
  )
}

export default GitHubSetupPage
