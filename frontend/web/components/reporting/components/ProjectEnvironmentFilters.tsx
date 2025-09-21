import React, { FC, useState } from 'react'
import moment from 'moment'
import DateSelect from 'components/DateSelect'
import ProjectFilter from 'components/ProjectFilter'
import EnvironmentFilter from 'components/EnvironmentFilter'
import LabelWithTooltip from 'components/base/LabelWithTooltip'
import { Button } from 'components/base/forms/Button'

export type DateRange = {
  startDate: moment.Moment | null
  endDate: moment.Moment | null
}

interface Filters {
  timeRange: DateRange
  projectId?: string
  environmentId?: string
}

interface ProjectEnvironmentFiltersProps {
  context: 'organisation' | 'project'
  contextId: string
  filters: Filters
  onFiltersChange: (filters: Filters) => void
  className?: string
}

const ProjectEnvironmentFilters: FC<ProjectEnvironmentFiltersProps> = ({
  context,
  contextId,
  filters,
  onFiltersChange,
  className = ''
}) => {
  const [localFilters, setLocalFilters] = useState<Filters>(filters)

  const handleFilterChange = (key: keyof Filters, value: string | DateRange | undefined) => {
    const newFilters = { ...localFilters, [key]: value }
    setLocalFilters(newFilters)
    onFiltersChange(newFilters)
  }

  return (
    <div className={`mb-4 ${className}`}>
      {/* Clean Filter Layout */}
      <div className='row g-3 align-items-end'>
        {/* Time Range Filter - Full width */}
        <div className='col-12'>
          <div className='form-label mb-2 reporting-form-label'>
            <LabelWithTooltip 
              label="Time Range"
              tooltip="Select the time period for reporting data"
            />
          </div>
          <div className='row g-3'>
            <div className='col-6'>
              <div className='form-label mb-1 reporting-form-label-small'>
                <LabelWithTooltip 
                  label="From"
                  tooltip="Start date for the reporting period"
                />
              </div>
              <DateSelect
                selected={localFilters.timeRange.startDate ? localFilters.timeRange.startDate.toDate() : null}
                onChange={(date) => {
                  const newRange = {
                    ...localFilters.timeRange,
                    startDate: date ? moment(date) : null
                  }
                  handleFilterChange('timeRange', newRange)
                }}
                placeholder="Select start date"
                showTimeSelect={false}
                allowPastDates={true}
              />
            </div>
            <div className='col-6'>
              <div className='form-label mb-1 reporting-form-label-small'>
                <LabelWithTooltip 
                  label="To"
                  tooltip="End date for the reporting period"
                />
              </div>
              <DateSelect
                selected={localFilters.timeRange.endDate ? localFilters.timeRange.endDate.toDate() : null}
                onChange={(date) => {
                  const newRange = {
                    ...localFilters.timeRange,
                    endDate: date ? moment(date) : null
                  }
                  handleFilterChange('timeRange', newRange)
                }}
                placeholder="Select end date"
                showTimeSelect={false}
                allowPastDates={true}
              />
            </div>
          </div>
        </div>

        {/* Project Filter - Only for organization context */}
        {context === 'organisation' && (
          <div className='col-lg-6'>
            <div className='form-label mb-2 reporting-form-label'>
              <LabelWithTooltip 
                label="Project"
                tooltip="Filter metrics by specific project"
              />
            </div>
            <ProjectFilter
              organisationId={parseInt(contextId)}
              value={localFilters.projectId}
              onChange={(id, name) => handleFilterChange('projectId', id || undefined)}
              showAll
            />
          </div>
        )}

        {/* Environment Filter */}
        <div className={context === 'organisation' ? 'col-lg-6' : 'col-12'}>
          <div className='form-label mb-2 reporting-form-label'>
            <LabelWithTooltip 
              label="Environment" 
              tooltip="Filter metrics by specific environment"
            />
          </div>
          <div className={context === 'organisation' && !localFilters.projectId ? 'reporting-form-disabled-opacity' : ''}>
            <EnvironmentFilter
              projectId={context === 'organisation' ? (localFilters.projectId || '') : contextId}
              value={localFilters.environmentId}
              onChange={(id) => handleFilterChange('environmentId', id || undefined)}
              showAll
              disabled={context === 'organisation' && !localFilters.projectId}
            />
          </div>
        </div>
      </div>
      
      {/* Clear All Filters Button */}
      <div className='mt-3 d-flex justify-content-end'>
        <Button
          onClick={() => {
            const clearedFilters = {
              timeRange: { startDate: null, endDate: null },
              projectId: undefined,
              environmentId: undefined
            }
            setLocalFilters(clearedFilters)
            onFiltersChange(clearedFilters)
          }}
          theme="secondary"
          size="small"
        >
          Clear All Filters
        </Button>
      </div>
    </div>
  )
}

export default ProjectEnvironmentFilters
