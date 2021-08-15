import React from 'react';
import cx from 'classnames';

export default function (props) {
    return (
        <Row style={props.color? {backgroundColor:props.color}: null} onClick={props.onClick} className={cx('chip mr-2 clickable', props.className, { 'light':!!props.color, 'chip--active': props.active })}>
            {props.children}
            <span
              className={cx('chip-icon ion', {
                  'ion-ellipse-outline': !props.active,
                  'ion-ios-checkmark': props.active,
              })}
            />
        </Row>
    );
}
