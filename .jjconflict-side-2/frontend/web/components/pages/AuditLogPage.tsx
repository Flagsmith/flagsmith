import React, { FC, useEffect, useState } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import { useHistory } from 'react-router-dom'
import AuditLog from 'components/AuditLog'
import PageTitle from 'components/PageTitle'
import { featureDescriptions } from 'components/PlanBasedAccess'
import { useRouteContext } from 'components/providers/RouteContext'
import EnvironmentTagSelect from 'components/EnvironmentTagSelect'

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
                      <EnvironmentTagSelect
                        allowEmpty
                        value={environment}
                        onChange={setEnvironment}
                        idField='id'
                        projectId={projectId}
                      />
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
