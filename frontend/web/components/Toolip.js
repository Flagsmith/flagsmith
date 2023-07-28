import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const ReactTooltip = require('react-tooltip')

const TooltipStyler = ({ children }) => (
  <div className='flex-row'>
    <div className='icon--tooltip ion-ios-information-circle mr-1'></div>
    <span>{`${children}`}</span>
  </div>
)

const Tooltip = class extends React.Component {
  static displayName = 'Tooltip'

  id = Utils.GUID()

  render() {
    return (
      <span className='question-tooltip'>
        {this.props.title ? (
          <span data-for={this.id} data-tip>
            {this.props.title}
          </span>
        ) : (
          <span className='ion ion-ios-help' data-for={this.id} data-tip />
        )}
        <ReactTooltip
          html
          id={this.id}
          place={this.props.place || 'top'}
          type='dark'
          effect='solid'
        >
          {renderToStaticMarkup(
            <TooltipStyler>{this.props.children}</TooltipStyler>,
          )}
        </ReactTooltip>
      </span>
    )
  }
}

Tooltip.propTypes = {
  children: RequiredElement,
  place: OptionalString,
}

export default Tooltip
