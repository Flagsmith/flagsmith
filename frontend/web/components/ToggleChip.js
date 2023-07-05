import React from 'react'
import cx from 'classnames'

export default function (props) {
  return (
    <Row
      style={props.color ? { backgroundColor: props.color } : null}
      onClick={props.onClick}
      className={cx('chip mr-2 mt-0 clickable', props.className, {
        'chip--active': props.active,
        'light': !!props.color,
      })}
    >
      {props.children}
      <span
        className={cx('mx-1 chip-icon ion', {
          'ion-ellipse-outline': !props.active,
          'ion-ios-checkmark': props.active,
        })}
      />
    </Row>
  )
}
