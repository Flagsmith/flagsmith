import React, { FC } from 'react'
import { IonIcon } from '@ionic/react'
import {
  book,
  checkmarkCircle,
  document,
  chatbox,
  bookSharp,
} from 'ionicons/icons'
import Button from './base/forms/Button'
import loadCrisp from 'common/loadCrisp'
import Utils from 'common/utils/utils'
import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'
import AccountStore from 'common/stores/account-store'

type ResourcesType = {}

const Resources: FC<ResourcesType> = ({}) => {
  useGetBuildVersionQuery({})
  const isSaas = Utils.isSaas()
  const show = !isSaas && !isFreeEmailDomain(AccountStore.getUser()?.email)
  if (!show) {
    return null
  }
  async function onCrispClick() {
    loadCrisp('8857f89e-0eb5-4263-ab49-a293872b6c19')
    Utils.openChat()
  }
  return (
    <div>
      <div className='rounded border-1 bg-body p-2 text-primary'>
        <h6 className='d-flex mb-0 fs-captionXSmall letter-spacing text-muted  align-items-center gap-2'>
          <IonIcon className='' icon={bookSharp} />
          <span className='fw-semibold'>RESOURCES</span>
        </h6>
        <hr className='mt-1' />
        <div className='mt-1'>
          <div className='d-flex flex-column gap-2 my-2'>
            <Button
              theme='text'
              onClick={onCrispClick}
              className='text-primary d-flex align-items-center gap-2'
              href=''
            >
              <IonIcon icon={chatbox} />
              Ask a question
            </Button>
            <Button
              theme='text'
              onClick={() => loadCrisp}
              className='text-primary fs-small d-flex align-items-center'
              href='https://docs.flagsmith.com'
            >
              <IonIcon icon={document} />
              Docs
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Resources
