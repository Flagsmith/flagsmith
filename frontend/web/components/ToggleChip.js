import React from 'react'
import cx from 'classnames'
import color from 'color'
import Icon from './Icon'

export default function (props) {
  return (
    <Row
      style={
        props.color
          ? {
              backgroundColor: props.children
                ? color(props.color).fade(0.92)
                : color(props.color).fade(0.76),
              border: `1px solid ${color(props.color).fade(0.76)}`,
              color: color(props.color).darken(0.1),
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
              : `1px solid ${color(props.color ? props.color : '#6837FC').fade(
                  0.76,
                )}`,
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
