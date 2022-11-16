import React from 'react';
import { Component } from 'react';
import cx from 'classnames';
import Popover from './base/Popover';


class ButtonDropdown extends Component {
    state = {}

    render() {
        return (
            <div className="relative">
                <Popover
                  className="popover-bottom"
                  contentClassName="popover-bt"
                  renderTitle={toggle => (
                      <Button className="btn-secondary" onClick={toggle}>
                          {this.props.children}
                      </Button>
                  )}
                >
                    {toggle => (
                        <div className="popover-inner__content">
                            {
                                !!this.props.title && (
                                    <span
                                      className="popover-bt__title"
                                    >
                                        {this.props.title}
                                    </span>
                                )
                            }
                            {this.props.items.map(({ title, onClick }) => (
                                <Row
                                  onClick={() => {
                                      toggle();
                                      onClick();
                                  }} className={cx('popover-bt__list-item list-item clickable')}
                                >
                                    {title}
                                </Row>
                            ))}

                        </div>
                    )}
                </Popover>
            </div>

        );
    }
}

export default ButtonDropdown;
