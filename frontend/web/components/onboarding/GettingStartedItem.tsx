import React, { FC } from 'react'
import { useGetProfileQuery } from 'common/services/useProfile'
import { useUpdateOnboardingMutation } from 'common/services/useOnboarding'
import API from 'project/api'
import classNames from 'classnames'
import Icon, { IconName } from 'components/Icon'
import Tooltip from 'components/Tooltip'
import { Link } from 'react-router-dom'

export type GettingStartedItemType = {
  duration: number
  title: string
  testId?: string
  description: string
  link: string
  icon?: IconName
  complete?: boolean
  disabledMessage?: string | null
  name?: string
}
const GettingStartedItem: FC<GettingStartedItemType> = (data) => {
  const { data: profile } = useGetProfileQuery({})
  const [updateProfile] = useUpdateOnboardingMutation({})
  const { complete: _complete, description, duration, link, title } = data
  const complete = data.name
    ? profile?.onboarding?.tasks?.find((v) => v.name === data.name)
    : _complete

  const onCTAClick = () => {
    if (data.disabledMessage) {
      return
    }

    API.trackEvent({ 'category': 'GettingStarted', 'event': data.name })

    if (data.name && profile) {
      updateProfile({
        tasks: (profile.onboarding?.tasks || []).concat({
          name: data.name,
        }),
      })
    }
  }

  const inner = (
    <div
      data-test={data.testId}
      onClick={onCTAClick}
      className='cursor-pointer'
    >
      <div
        className={classNames('card h-100 bg-card border-1 rounded', {
          'border-primary': complete,
        })}
      >
        <div
          className={classNames('h-100', {
            'bg-primary-opacity-5': complete,
          })}
        >
          <div
            className={classNames(
              'p-3 fs-small py-2 d-flex h-100 flex-column mx-0',
            )}
          >
            <div className='d-flex justify-content-between align-items-center'>
              <div className='d-flex align-items-center gap-3'>
                <div
                  style={{ height: 34, width: 34 }}
                  className={
                    'd-flex rounded border-1 align-items-center justify-content-center flex-shrink-0'
                  }
                >
                  {complete ? (
                    <Icon fill='#6837fc' name={'checkmark-circle'} />
                  ) : (
                    <Icon
                      name={data.icon || 'file-text'}
                      className='text-body'
                    />
                  )}
                </div>
                <div>
                  <span
                    className={`d-flex fw-bold fs-small align-items-center mb-0 gap-1`}
                  >
                    {title}
                  </span>

                  <h6 className='fw-normal d-flex fs-small text-muted flex-1 mb-0'>
                    {description}
                  </h6>
                </div>
              </div>

              <div className='d-flex'>
                <span className='chip chip-secondary d-flex gap-1  align-items-center lh-1 chip chip--xs'>
                  <Icon className='chip-svg-icon' width={14} name={'clock'} />
                  <span>{duration} Min</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
  if (data.disabledMessage) {
    return <Tooltip title={inner}>{data.disabledMessage}</Tooltip>
  }
  return link?.startsWith('http') ? (
    <a href={link} target={'_blank'} onClick={onCTAClick} rel='noreferrer'>
      {inner}
    </a>
  ) : (
    <Link onClick={onCTAClick} to={link}>
      {inner}
    </Link>
  )
}
export default GettingStartedItem
