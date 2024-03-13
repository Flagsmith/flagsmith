import React, { FC } from 'react'
import { useGetAuditLogItemQuery } from 'common/services/useAuditLogItem'
import ErrorMessage from 'components/ErrorMessage'
import Breadcrumb from 'components/Breadcrumb'
import PageTitle from 'components/PageTitle'
import Panel from 'components/base/grid/Panel'
import moment from 'moment'
import ProjectStore from 'common/stores/project-store'
import Utils from 'common/utils/utils'
import Tag from 'components/tags/Tag'
import DiffString from 'components/diff/DiffString'
import DiffEnabled from 'components/diff/DiffEnabled'
import Format from 'common/utils/format'
import { Environment } from 'common/types/responses'
type AuditLogItemPageType = {
  match: {
    params: {
      environmentId: string
      projectId: string
      id: string
    }
  }
}

const AuditLogItemPage: FC<AuditLogItemPageType> = ({ match }) => {
  const { data, error, isLoading } = useGetAuditLogItemQuery({
    id: match.params.id,
    projectId: match.params.projectId,
  })

  const index = (ProjectStore.getEnvs() as Environment[] | null)?.findIndex(
    (v) => {
      return v.id === data?.environment?.id
    },
  )
  const colour = index === -1 ? 0 : index

  return (
    <div className='app-container container-fluid mt-1'>
      <Breadcrumb
        items={[
          {
            title: 'Audit Log',
            url: `/project/${match.params.projectId}/environment/${match.params.environmentId}/audit-log`,
          },
        ]}
        currentPage={match.params.id}
      />
      <PageTitle
        title={
          <Row>
            Log #{match.params.id}
            {!!data?.environment && (
              <div className='ms-2'>
                <Tag
                  tag={{
                    color: Utils.getTagColour(colour),
                    label: data.environment?.name,
                  }}
                  className='chip--sm'
                />
              </div>
            )}
          </Row>
        }
      >
        {!!data &&
          `Created ${moment(data.created_date).format('Do MMM YYYY HH:mma')}${
            data.author
              ? ` by ${data.author.first_name || ''} ${
                  data.author.last_name || ''
                }`
              : ''
          }`}
      </PageTitle>
      {isLoading ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <div>
          <ErrorMessage>{error}</ErrorMessage>
          {!!data && (
            <>
              <Panel title={'Details'} className='no-pad mb-2'>
                <p>{data.log}</p>
              </Panel>
              {!!data?.change_details?.length && (
                <Panel title={'Changes'} className='no-pad mb-2'>
                  <div className='search-list'>
                    <div className='flex-row table-header'>
                      <div className='flex-fill px-2'>Field</div>
                      <div className='px-2'>Value</div>
                    </div>
                    {data?.change_details?.map((v) => (
                      <Row key={v.field} className='list-item'>
                        <div className='flex-fill font-weight-medium px-2'>
                          {Format.camelCase(Format.enumeration.get(v.field))}
                        </div>
                        <div className='px-2'>
                          {v.field === 'enabled' ? (
                            <DiffEnabled
                              oldValue={!!v.old}
                              newValue={!!v.new}
                            />
                          ) : (
                            <DiffString oldValue={v.old} newValue={v.new} />
                          )}
                        </div>
                      </Row>
                    ))}
                  </div>
                </Panel>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default AuditLogItemPage
