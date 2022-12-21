import React, {FC, PureComponent, useState} from 'react'
import color from 'color';
import cx from 'classnames'

import {Tag as TTag} from 'common/types/responses'
import ToggleChip from "../ToggleChip";

type TagType = {
    className?:string
    deselectedColor?: string
    hideNames?:boolean
    onClick?: (tag:TTag)=>void
    selected?:boolean
    tag: Partial<TTag>
}

const Tag: FC<TagType> = ({onClick, tag, selected, deselectedColor, className, hideNames}) => {
    const [hover, setHover] = useState(false);

    const toggleHover = () => {
        if(onClick) {
            setHover(!hover)
        }
    }

    const getColor = () => {
        if (selected) {
            return tag.color;
        }
        return deselectedColor || tag.color;
    }

    if (!hideNames) {
        return (
            <ToggleChip color={getColor()} active={selected} onClick={onClick ? () => onClick(tag as TTag) : null}>
                {tag.label}
            </ToggleChip>
        );
    }

    return (
        <div
            onClick={ () => onClick?.(tag as TTag)}
            onMouseEnter={toggleHover}
            onMouseLeave={toggleHover}
            style={{ backgroundColor: hover ? `${color(getColor()).darken(0.1)}` : getColor() }}
            className={cx('tag', { selected, hideNames: hideNames }, className)}
        >
            <div>
                <div className="text-center">
                    {selected && (
                        <span className="icon ion-md-checkmark"/>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Tag
