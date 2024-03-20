import React, { FC, useEffect, useState } from 'react'
import Utils, { planNames } from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import Button from './base/forms/Button'
import { IonIcon } from '@ionic/react'
import { starOutline } from 'ionicons/icons'
import Icon from './Icon'

type GithubStarType = {}

const GithubStar: FC<GithubStarType> = ({}) => {
  const organisation = AccountStore.getOrganisation()
  const plan = organisation?.subscription?.plan || ''
  const planName = Utils.getPlanName(plan)
  const [stars, setStars] = useState()
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (planName !== planNames.enterprise) {
      fetch(`https://api.github.com/repos/flagsmith/flagsmith`)
        .then(function (res) {
          return res.json()
        })
        .then(function (res) {
          setStars(res.stargazers_count)
        })
    }
  }, [planName])

  if (planName === planNames.enterprise) {
    return <></>
  }

  return (
    <>
      <a
        style={{ width: 90 }}
        target='_blank'
        href='https://github.com/flagsmith/flagsmith'
        className='btn btn-sm btn-with-icon text-body me-2'
        rel='noreferrer'
      >
        <div className='d-flex flex-row justify-content-center align-items-center'>
          <Icon name='github' width={20} fill='#9DA4AE' />
          <div className='ms-1'>{stars}</div>
        </div>
      </a>
    </>
  )
}

export default GithubStar
