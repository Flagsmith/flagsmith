import React, { FC, useEffect, useState } from 'react' // we need this to make JSX compile
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { useHistory } from 'react-router-dom'
import AuditLog from 'components/AuditLog'
import ProjectProvider from 'common/providers/ProjectProvider'
import PageTitle from 'components/PageTitle'
import Tag from 'components/tags/Tag'
import { featureDescriptions } from 'components/PlanBasedAccess'
import { useRouteContext } from 'components/providers/RouteContext'

interface RouteParams {
  environmentId: string
  projectId: string
}

const AuditLogPage: FC = () => {
  const history = useHistory()
  const { projectId } = useRouteContext()

  const [environment, setEnvironment] = useState(Utils.fromParam().env)
  useEffect(() => {
    const currentParams = Utils.fromParam()
    if (currentParams.env !== environment) {
      history.replace(
        `${document.location.pathname}?${Utils.toParam({
          env: environment,
          page: currentParams.page,
          search: currentParams.search,
        })}`,
      )
    }
  }, [environment, history])
  return (
    <div className='app-container container'>
      {Utils.getPlansPermission('AUDIT') && (
        <PageTitle title={featureDescriptions.AUDIT.title}>
          {featureDescriptions.AUDIT.description}
        </PageTitle>
      )}
      <div>
        <div>
          <FormGroup>
            <div>
              <div className='audit'>
                <FormGroup>
                  <AuditLog
                    onSearchChange={(search: string) => {
                      history.replace(
                        `${document.location.pathname}?${Utils.toParam({
                          env: environment,
                          page: Utils.fromParam().page,
                          search,
                        })}`,
                      )
                    }}
                    onPageChange={(page: number) => {
                      history.replace(
                        `${document.location.pathname}?${Utils.toParam({
                          env: environment,
                          page,
                          search: Utils.fromParam().search,
                        })}`,
                      )
                    }}
                    pageSize={10}
                    environmentId={environment}
                    projectId={projectId}
                    searchPanel={
                      <ProjectProvider>
                        {({ project }: { project: Project }) => (
                          <Row className='mb-2'>
                            {project &&
                              project.environments &&
                              project.environments.map((env, i) => (
                                <Tag
                                  tag={{
                                    color: Utils.getTagColour(i),
                                    label: env.name,
                                  }}
                                  key={env.id}
                                  selected={`${environment}` === `${env.id}`}
                                  onClick={() => {
                                    setEnvironment(
                                      `${environment}` === `${env.id}`
                                        ? undefined
                                        : env.id,
                                    )
                                  }}
                                  className='mr-2 mb-2'
                                />
                              ))}
                          </Row>
                        )}
                      </ProjectProvider>
                    }
                  />
                </FormGroup>
              </div>
            </div>
          </FormGroup>
        </div>
      </div>
    </div>
  )
}

export default ConfigProvider(AuditLogPage)
