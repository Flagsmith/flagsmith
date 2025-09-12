import React from 'react'
import cx from 'classnames'
import Icon from './Icon'
import Utils from 'common/utils/utils'

export default function (props) {
  const colour = Utils.colour(props.color)
  return (
    <Row
      style={
        props.color
          ? {
              backgroundColor: props.children
                ? colour.fade(0.92)
                : colour.fade(0.76),
              border: `1px solid ${colour.fade(0.76)}`,
              color: colour.darken(0.1),
            }
          : null
      }
      onClick={props.onClick}
      className={cx('chip no-wrap mr-2 mt-0 clickable', props.className)}
    >
      <span
        style={{
          backgroundColor: props.active ? 'white' : 'transparent',
          border:
            props.active || !props.children
              ? 'none'
              : `1px solid ${colour.fade(0.76)}`,
          marginRight: props.children ? '0.5rem' : '0',
        }}
        className='icon-check'
      >
        {props.active && <Icon name='checkmark-square' fill={props.color} />}
      </span>
      {props.children}
    </Row>
  )
}
