import React, { FC, useState } from 'react' // we need this to make JSX compile
import ConfigProvider from 'common/providers/ConfigProvider'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import { Project, SplitTestResult } from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import AuditLog from 'components/AuditLog'
import ProjectProvider from 'common/providers/ProjectProvider'
import PageTitle from 'components/PageTitle'
import Tag from 'components/tags/Tag'
import Select from 'react-select'
import ConversionEventSelect from 'components/ConversionEventSelect'
import { useGetConversionEventsQuery } from 'common/services/useConversionEvent'
import InfoMessage from 'components/InfoMessage'
import PanelSearch from 'components/PanelSearch'
import ErrorMessage from 'components/ErrorMessage'
import useSearchThrottle from 'common/useSearchThrottle'
import { useGetSplitTestQuery } from 'common/services/useSplitTest'

type AuditLogType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const pageSize = 10
const widths = [200, 100]
const AuditLogPage: FC<AuditLogType> = (props) => {
  const projectId = props.match.params.projectId
  const { search, searchInput, setSearchInput } = useSearchThrottle()
  const [conversion_event_type_id, setConversionEvent] = useState<
    number | null
  >(null)

  const [page, setPage] = useState(1)
  const { data, error, isLoading } = useGetSplitTestQuery(
    {
      conversion_event_type_id: `${conversion_event_type_id}`,
      page,
      page_size: pageSize,
    },
    { skip: !conversion_event_type_id },
  )

  const renderRow = (item: SplitTestResult) => (
    <tr>
      <td>{item.feature.name}</td>
      <td>{item.max_conversion}</td>
      <td>{item.value_data}</td>
    </tr>
  )
  return (
    <div className='app-container container'>
      <PageTitle title={'Split Tests'}>
        Monitor conversion events against your multivariate feature flags.
      </PageTitle>
      <div className='flex-row my-4'>
        Conversion Event{' '}
        <div className={'ms-2'} style={{ width: 200 }}>
          <ConversionEventSelect onChange={setConversionEvent} />
        </div>
      </div>
      {!conversion_event_type_id ? (
        <InfoMessage className='mt-2'>
          Select a conversion event to view split test results
        </InfoMessage>
      ) : (
        <>
          <ErrorMessage>{error}</ErrorMessage>
          <PanelSearch
            title='Split Tests'
            isLoading={isLoading}
            className='no-pad'
            items={data?.results}
            search={searchInput}
            onChange={(e: InputEvent) => {
              setSearchInput(Utils.safeParseEventValue(e))
            }}
            paging={{
              ...(data || {}),
              page,
              pageSize,
            }}
            nextPage={() => {
              setPage(page + 1)
            }}
            prevPage={() => {
              setPage(page - 1)
            }}
            goToPage={(page: number) => {
              setPage(page)
            }}
            filterRow={() => true}
            renderRow={renderRow}
            header={
              <Row className='table-header'>
                <div className='table-column flex-fill'>Feature</div>
                <div className='table-column' style={{ width: widths[1] }}>
                  Conversion Variance
                </div>
                <div className='table-column' style={{ width: widths[2] }}>
                  Confidence
                </div>
              </Row>
            }
          />
        </>
      )}
    </div>
  )
}

export default ConfigProvider(AuditLogPage)
