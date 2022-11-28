import React, {FC, HTMLAttributeAnchorTarget, PureComponent, ReactNode} from 'react';
export type ButtonType = React.ButtonHTMLAttributes<HTMLButtonElement>
export type ButtonLinkType = ButtonType & {
    href?: string
    target?: HTMLAttributeAnchorTarget
}

const Button: FC<ButtonType> = (props) => {
    return (
        <button
             {...props}
            className={`btn ${props.className || ''}`}
        >
            {props.children}
        </button>
    )
}


export default Button;



const ButtonOutline: FC<ButtonType> = (props) => {
    return (
        <Button {...props} className={`btn--outline ${props.className || ''}`}/>
    )
}

export const ButtonProject: FC<ButtonType> = (props) => {
    return (
        <Button {...props} className={`btn--project ${props.className || ''}`}/>
    )
}

export const ButtonLink: FC<ButtonLinkType> = ({href, className, target, children,...rest}) => {
    return (
        <Button {...rest} className={`btn--link ${className || ''}`}>
            {href ? (
                <a className="btn--link" target={target} href={href}>{children}</a>
            ) : (

                <span className="btn--link">{children}</span>
            )}
        </Button>
    )
}

