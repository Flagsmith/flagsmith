import React, { Component } from 'react'
import InlineModal from './InlineModal'
import Icon from './Icon'
import classNames from 'classnames'

class TheComponent extends Component {
  state = {
    filter: '',
  }

  render() {
    const users =
      this.props.users &&
      this.props.users.filter((v) => {
        const search = this.state.filter.toLowerCase()
        if (!search) return true
        return `${v.first_name} ${v.last_name}`.toLowerCase().includes(search)
      })
    const value = this.props.value || []
    const modalClassName = `inline-modal--sm`

    return (
      <InlineModal
        title='Assignees'
        isOpen={this.props.isOpen}
        onClose={this.props.onToggle}
        className={modalClassName}
      >
        <Input
          disabled={this.props.disabled}
          value={this.state.filter}
          onChange={(e) =>
            this.setState({ filter: Utils.safeParseEventValue(e) })
          }
          className='full-width mb-2'
          placeholder='Search User'
          search
        />
        <div style={{ maxHeight: 200, overflowX: 'hidden', overflowY: 'auto' }}>
          {users &&
            users.map((v) => (
              <div
                onClick={() => {
                  const isRemove = value.includes(v.id)
                  if (isRemove && this.props.onRemove) {
                    this.props.onRemove(v.id)
                  } else if (!isRemove && this.props.onAdd) {
                    this.props.onAdd(v.id)
                  }
                  this.props.onChange &&
                    this.props.onChange(
                      isRemove
                        ? value.filter((f) => f !== v.id)
                        : value.concat([v.id]),
                    )
                }}
                className='assignees-list-item clickable'
                key={v.id}
              >
                <Row className="flex-nowrap w-100 overflow-hidden overflow-ellipsis" space>
                  <div
                    className={classNames(
                      value.includes(v.id) ? 'font-weight-bold' : '',
                      'overflow-ellipsis w-100',
                    )}
                  >
                    {v.first_name} {v.last_name}
                    <div className="text-muted text-small">
                      {v.email}
                    </div>
                  </div>
                  {value.includes(v.id) && (
                    <span className='mr-1'>
                      <Icon name='checkmark' fill='#6837FC' />
                    </span>
                  )}
                </Row>
              </div>
            ))}
        </div>
      </InlineModal>
    )
  }
}
export default TheComponent
