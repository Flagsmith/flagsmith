import React, { ComponentType } from 'react'
import { MemoryRouter } from 'react-router-dom'

export const withRouter = (Story: ComponentType) => (
  <MemoryRouter>
    <Story />
  </MemoryRouter>
)
