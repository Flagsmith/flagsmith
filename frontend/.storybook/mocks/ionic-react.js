// Storybook mock for @ionic/react.
// Renders IonIcon as a small inline placeholder so components that depend on
// IonIcon (ClearFilters, NavSubLink, BreadcrumbSeparator, etc.) can still
// render in stories without forcing a refactor of production components.
import React from 'react'

export const IonIcon = ({ icon, color, ...rest }) =>
  React.createElement('span', {
    ...rest,
    'aria-hidden': true,
    'data-stub-icon': typeof icon === 'string' ? icon : 'icon',
    style: {
      backgroundColor: color || 'currentColor',
      borderRadius: '50%',
      display: 'inline-block',
      height: '1em',
      verticalAlign: 'middle',
      width: '1em',
      ...(rest.style || {}),
    },
  })

export default { IonIcon }
