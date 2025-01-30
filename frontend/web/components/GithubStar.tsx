import React, { FC, useEffect, useState } from 'react'
import Utils, { planNames } from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { IonIcon } from '@ionic/react'
import { logoGithub } from 'ionicons/icons'

type GithubStarType = {}

const GithubStar: FC<GithubStarType> = ({}) => {
  const organisation = AccountStore.getOrganisation()
  const plan = organisation?.subscription?.plan || ''
  const planName = Utils.getPlanName(plan)
  const [stars, setStars] = useState<number | null>(null)

  const formatStars = (count: number): string => {
    if (count >= 1000) {
      const formattedCount = Math.ceil(count / 100) * 100 // Round up to nearest 100
      return `${(formattedCount / 1000).toFixed(1)}k` // Format as 'x.xk'
    }
    return count.toString()
  }

  useEffect(() => {
    if (planName !== planNames.enterprise) {
      fetch('https://api.github.com/repos/flagsmith/flagsmith')
        .then((res) => res.json())
        .then((res) => {
          setStars(res.stargazers_count)
        })
        .catch(() => {})
    }
  }, [planName])

  if (planName === planNames.enterprise) {
    return <></>
  }

  return (
    <a
      style={{ width: 90 }}
      target='_blank'
      href='https://github.com/flagsmith/flagsmith'
      className='btn btn-sm btn-with-icon text-body'
      rel='noreferrer'
    >
      <div
        className={
          stars !== null
            ? 'd-flex flex-row justify-content-center align-items-center'
            : ''
        }
      >
        <IonIcon style={{ fontSize: 16 }} icon={logoGithub} />
        {stars !== null && <div className='ms-1'>{formatStars(stars)}</div>}
      </div>
    </a>
  )
}

export default GithubStar
