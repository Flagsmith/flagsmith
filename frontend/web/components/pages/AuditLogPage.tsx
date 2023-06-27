import React, { FC, useState } from 'react' // we need this to make JSX compile
import ConfigProvider from 'common/providers/ConfigProvider'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import AuditLog from 'components/AuditLog'

const ProjectProvider = require('common/providers/ProjectProvider')

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
      <div>
        <div>
          <h4>Audit Log</h4>
          <p>
            View all activity that occured generically across the project and
            specific to this environment.
          </p>
          <FormGroup>
            <div>
              <div className='audit'>
                <div className='font-weight-bold mb-2'>
                  Filter by environments:
                </div>
                <ProjectProvider>
                  {({ project }: { project: Project }) => (
                    <Row>
                      {project &&
                        project.environments &&
                        project.environments.map((env) => (
                          <ToggleChip
                            key={env.id}
                            active={`${environment}` === `${env.id}`}
                            onClick={() => {
                              setEnvironment(
                                `${environment}` === `${env.id}`
                                  ? undefined
                                  : env.id,
                              )
                            }}
                            className='mr-2 mb-4'
                          >
                            {env.name}
                          </ToggleChip>
                        ))}
                    </Row>
                  )}
                </ProjectProvider>
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
