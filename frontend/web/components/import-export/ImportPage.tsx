import React, { FC, useEffect, useState } from 'react'
import _data from 'common/data/base/_data'
import {
  useCreateLaunchDarklyProjectImportMutation,
  useGetLaunchDarklyProjectImportQuery,
} from 'common/services/useLaunchDarklyProjectImport'
import AppLoader from 'components/AppLoader'
import InfoMessage from 'components/InfoMessage'
import Tabs from 'components/navigation/TabMenu/Tabs'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import PanelSearch from 'components/PanelSearch'
import TabItem from 'components/navigation/TabMenu/TabItem'
import FeatureImport from './FeatureImport'
import AccountStore from 'common/stores/account-store'
import Constants from 'common/constants'
import { useHistory } from 'react-router-dom'

type ImportPageType = {
  projectId: string
  projectName: string
}

const ImportPage: FC<ImportPageType> = ({ projectId, projectName }) => {
  const history = useHistory()
  const [LDKey, setLDKey] = useState<string>('')
  const [importId, setImportId] = useState<number>()
  const [importSource, setImportSource] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [projects, setProjects] = useState<{ key: string; name: string }[]>([])
  const [createLaunchDarklyProjectImport, { data, isSuccess }] =
    useCreateLaunchDarklyProjectImportMutation()

  const { data: status } = useGetLaunchDarklyProjectImportQuery(
    {
      import_id: `${importId}`,
      project_id: projectId,
    },
    {
      pollingInterval: importId ? 1000 : 0,
      skip: !importId,
    },
  )

  // Set importId when mutation succeeds
  useEffect(() => {
    if (isSuccess && data?.id) {
      setImportId(data.id)
      setImportSource('LaunchDarkly')
    }
  }, [isSuccess, data])

  // Navigate away on import success
  useEffect(() => {
    if (status?.status?.result === 'success') {
      const params = new URLSearchParams()
      params.set('import_success', '1')
      params.set('import_source', importSource)
      params.set('import_count', String(status.status.requested_flag_count))
      params.set(
        'import_deprecated',
        String(status.status.deprecated_flag_count ?? 0),
      )
      history.push(`/project/${projectId}?${params.toString()}`)
    }
  }, [status, projectId, history, importSource])

  const getProjectList = (LDKey: string) => {
    setIsLoading(true)
    _data
      .get(`https://app.launchdarkly.com/api/v2/projects`, '', {
        'Authorization': LDKey,
      })
      .then((res: { items: { key: string; name: string }[] }) => {
        setIsLoading(false)
        setProjects(res.items)
      })
  }

  const createImportLDProjects = (
    LDKey: string,
    key: string,
    projectId: string,
  ) => {
    createLaunchDarklyProjectImport({
      body: { project_key: key, token: LDKey },
      project_id: projectId,
    })
  }

  const isAdmin = AccountStore.isAdmin()

  if (!isAdmin) {
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: Constants.organisationPermissions('Administrator'),
        }}
        className='mt-4'
      />
    )
  }

  const launchDarklyImport = (
    <>
      <InfoMessage>
        Import operations will overwrite existing environments and flags in your
        project.
      </InfoMessage>
      <h5>Import LaunchDarkly Projects</h5>
      <label>Set LaunchDarkly key</label>
      <FormGroup>
        <Row className='align-items-start col-md-8'>
          <Flex className='ml-0'>
            <Input
              value={LDKey}
              name='ldkey'
              onChange={(e: InputEvent) =>
                setLDKey(Utils.safeParseEventValue(e))
              }
              type='text'
              placeholder='My LaunchDarkly key'
            />
          </Flex>
          <Button
            id='save-proj-btn'
            disabled={!LDKey}
            className='ml-3'
            onClick={() => getProjectList(LDKey)}
          >
            {'Next'}
          </Button>
        </Row>
      </FormGroup>
      {isLoading ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        projects.length > 0 && (
          <div>
            <FormGroup>
              <PanelSearch
                id='projects-list'
                className='no-pad panel-projects'
                listClassName='row mt-n2 gy-3'
                title='LaunchDarkly Projects'
                items={projects}
                renderRow={({ key, name }, i) => {
                  return (
                    <>
                      <Button
                        className='btn-project'
                        onClick={() =>
                          openConfirm({
                            body: (
                              <span>
                                Flagsmith will import {<strong>{name}</strong>}{' '}
                                to {<strong>{projectName}</strong>}. Are you
                                sure?
                              </span>
                            ),
                            onNo: () => {
                              return
                            },
                            onYes: () => {
                              createImportLDProjects(LDKey, key, projectId)
                            },
                            title: 'Import LaunchDarkly project',
                          })
                        }
                      >
                        <Row className='flex-nowrap'>
                          <h2
                            style={{
                              backgroundColor: Utils.getProjectColour(i),
                            }}
                            className='btn-project-letter mb-0'
                          >
                            {name[0]}
                          </h2>
                          <div className='font-weight-medium btn-project-title'>
                            {name}
                          </div>
                        </Row>
                      </Button>
                    </>
                  )
                }}
                renderNoResults={
                  <div>
                    <Row>
                      <div className='font-weight-medium'>No Projects</div>
                    </Row>
                  </div>
                }
              />
            </FormGroup>
          </div>
        )
      )}
    </>
  )

  const isImporting = !!importId && status?.status?.result !== 'success'

  return (
    <>
      {isImporting && (
        <div className='overlay'>
          <div className='title'>Importing from {importSource}...</div>
          <AppLoader />
        </div>
      )}
      <div className='mt-4'>
        <Tabs urlParam={'import'} theme='pill' history={history}>
          <TabItem tabLabel={'Flagsmith'}>
            <div className='mt-4'>
              <FeatureImport projectId={projectId} />
            </div>
          </TabItem>
          <TabItem tabLabel={'LaunchDarkly'}>
            <div className='mt-4'>{launchDarklyImport}</div>
          </TabItem>
        </Tabs>
      </div>
    </>
  )
}
export default ImportPage
