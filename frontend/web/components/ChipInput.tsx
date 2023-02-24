import React, {FC, FormEventHandler, useState} from 'react';
import TheInput from 'material-ui-chip-input';
const Utils = require('../../common/utils/utils')
import {filter} from 'lodash'
type ChipInputType = {
    placeholder?:string
    value?:string[]
    onChange:(v:string[])=>void
}

const ChipInput: FC<ChipInputType> = ({value, onChange,placeholder}) => {
    const [inputValue, setInputValue] = useState("");

    console.log(inputValue)
    const onChangeText:FormEventHandler = (e) => {
        const v = Utils.safeParseEventValue(e);
        const currentValue = value || [];
        if (v.search(/[ ,]/) !== -1) {
            //delimit when detecting one of the following characters
            const split = filter(v.split(/[ ,;]/), v => v !== ' ' && v !== ',' && v !== ';' && v !== '');
            setInputValue("")
            onChange(currentValue.concat(split));
        } else {
            setInputValue(v);
        }
    }

    const onDelete = (_:any, index:number) => {
        const v = (value||[]);
        onChange(Utils.removeElementFromArray(v,index));
    }

    const onSubmit = (chip:string) => {
        if (chip) {
            onChange((value||[]).concat([chip]));
        }
        setInputValue("")
        return true
    }

    return (
        <TheInput
            fullWidth
            placeholder={placeholder}
            blurBehavior="add"
            onChangeCapture={onChangeText}
            value={value}
            inputValue={inputValue}
            onDelete={onDelete}
            onBeforeAdd={onSubmit}
            onChange={onChange}
        />
    )
}

export default ChipInput
