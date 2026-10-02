import { FC, ReactNode } from 'react'
import './DependenciesPanel.scss'

const DependenciesPanel: FC<{ children: ReactNode }> = ({ children }) => (
  <div className='dependencies-panel'>{children}</div>
)

export default DependenciesPanel
