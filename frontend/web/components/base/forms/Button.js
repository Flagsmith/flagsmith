import { PureComponent } from 'react';

const Button = class extends PureComponent {
    static displayName = 'Button'

    onMouseUp = () => {
        this.refs.button.blur();
    }

    render() {
        return (
            <button
              ref="button" {...this.props} onMouseUp={this.onMouseUp}
              className={`btn ${this.props.className || ''}`}
            >
                {this.props.children}
            </button>
        );
    }
};

Button.propTypes = {
    className: OptionalString,
    children: OptionalNode,
};

export default class extends PureComponent {
    static displayName = 'Button';

    render() {
        return <Button {...this.props} className={`${this.props.className || ''}`}/>;
    }
}

export const ButtonOutline = class extends PureComponent {
    static displayName = 'ButtonOutline';

    render() {
        return <Button {...this.props} className={`btn--outline ${this.props.className || ''}`}/>;
    }
};

export const ButtonLink = class extends PureComponent {
    static displayName = 'ButtonLink';

    render() {
        const {buttonText, ...rest} = this.props;
        return (
            <Button {...rest} className={`btn--link ${this.props.className || ''}`}>
                {this.props.href ? (
                    <a className="btn--link" target={this.props.target} href={this.props.href}>{this.props.buttonText}{this.props.children}</a>
                ) : (

                    <span className="btn--link">{this.props.buttonText}{this.props.children}</span>
                )}
            </Button>
        );
    }
};

export const ButtonProject = class extends PureComponent {
    static displayName = 'ButtonProject';

    render() {
        return <Button {...this.props} className={`btn--project ${this.props.className || ''}`}/>;
    }
};
