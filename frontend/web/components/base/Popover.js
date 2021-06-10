import cn from 'classnames';
import FocusMonitor from './higher-order/FocusMonitor';

const Popover = class extends React.Component {
    static displayName = 'Popover'

    constructor(props, context) {
        super(props, context);
        this.state = { isActive: false };
    }

    _focusChanged = isActive => this.setState({ isActive });

    toggle = () => {
        this.focus.toggle();
    }

    isActive = () => this.state.isActive

    render() {
        const classNames = cn({
            popover: true,
            in: this.state.isActive,
        }, this.props.contentClassName, this.props.className);

        return (
            <FocusMonitor
              ref={c => this.focus = c}
              onFocusChanged={this._focusChanged}
              isHover={this.props.isHover}
            >
                <div className={this.props.className}>
                    {this.props.renderTitle(this.toggle, this.state.isActive)}
                    <div className="popover-inner">
                        <div className={`${classNames}`}>
                            {this.props.children(this.toggle)}
                        </div>
                    </div>
                </div>
            </FocusMonitor>
        );
    }
};

Popover.propTypes = {
    isHover: OptionalBool,
    className: OptionalString,
    renderTitle: RequiredFunc,
    children: Any,
};

module.exports = Popover;
