import React, {HTMLAttributeAnchorTarget, PureComponent, ReactNode} from 'react';
export type ButtonType = React.ButtonHTMLAttributes<HTMLButtonElement> & {
    href?: string
    target?: HTMLAttributeAnchorTarget
}
const Button = class extends PureComponent<ButtonType> {
    static displayName = 'Button'

    button: HTMLButtonElement|null = null

    onMouseUp = () => {
        this.button?.blur();
    }

    render() {
        return (
            <button
              ref={(ref)=>this.button = ref} {...this.props} onMouseUp={this.onMouseUp}
              className={`btn ${this.props.className || ''}`}
            >
                {this.props.children}
            </button>
        );
    }
};


export default class extends Button {
    static displayName = 'Button';

    render() {
        return <Button {...this.props} className={`${this.props.className || ''}`}/>;
    }
}

export const ButtonOutline = class extends Button {
    static displayName = 'ButtonOutline';

    render() {
        return <Button {...this.props} className={`btn--outline ${this.props.className || ''}`}/>;
    }
};

export const ButtonLink = class extends Button {
    static displayName = 'ButtonLink';

    render() {
        const { ...rest } = this.props;
        return (
            <Button {...rest} className={`btn--link ${this.props.className || ''}`}>
                {this.props.href ? (
                    <a className="btn--link" target={this.props.target} href={this.props.href}>{this.props.children}</a>
                ) : (

                    <span className="btn--link">{this.props.children}</span>
                )}
            </Button>
        );
    }
};

export const ButtonProject = class extends Button {
    static displayName = 'ButtonProject';

    render() {
        return <Button {...this.props} className={`btn--project ${this.props.className || ''}`}/>;
    }
};
