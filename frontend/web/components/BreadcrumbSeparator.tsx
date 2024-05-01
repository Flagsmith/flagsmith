import { FC } from 'react'
import { IonIcon } from '@ionic/react';
import { chevronForward } from 'ionicons/icons';

type BreadcrumbSeparatorType = {}

const BreadcrumbSeparator: FC<BreadcrumbSeparatorType> = ({}) => {
  return <IonIcon icon={chevronForward} className='text-muted'/>
}

export default BreadcrumbSeparator
