import React, { FC, useEffect, useState } from 'react' // we need this to make JSX compile
import ConfigProvider from 'common/providers/ConfigProvider'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import AuditLog from 'components/AuditLog'
import ProjectProvider from 'common/providers/ProjectProvider'
import PageTitle from 'components/PageTitle'
import Tag from 'components/tags/Tag'

type AuditLogType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const AuditLogPage: FC<AuditLogType> = (props) => {
  const projectId = props.match.params.projectId

  const [environment, setEnvironment] = useState(Utils.fromParam().env)
  useEffect(() => {
    const currentParams = Utils.fromParam()
    if (currentParams.env !== environment) {
      props.router.history.replace(
        `${document.location.pathname}?${Utils.toParam({
          env: environment,
          search: currentParams.search,
        })}`,
      )
    }
  }, [environment])
  const hasRbacPermission = Utils.getPlansPermission('AUDIT')
  if (!hasRbacPermission) {
    return (
      <div>
        <div className='text-center'>
          To access this feature please upgrade your account to scaleup or
          higher.
        </div>
      </div>
    )
  }
  return (
    <div className='app-container container'>
      <PageTitle title={'Audit Log'}>
        View all activity that occured generically across the project and
        specific to this environment.
      </PageTitle>
      <div>
        <div>
          <FormGroup>
            <div>
              <div className='audit'>
                <FormGroup>
                  <AuditLog
                    onSearchChange={(search: string) => {
                      props.router.history.replace(
                        `${document.location.pathname}?${Utils.toParam({
                          env: environment,
                          search,
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
