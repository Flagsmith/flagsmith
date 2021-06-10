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
        return (
            <Button {...this.props} className={`btn--link ${this.props.className || ''}`}>
                <a className="btn--link" target={this.props.target} href={this.props.href}>{this.props.buttonText}{this.props.children}</a>
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
