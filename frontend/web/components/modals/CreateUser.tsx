import React, {Component, useEffect, useState} from 'react';
import ChipInput from '../ChipInput';
import ErrorMessage from '../ErrorMessage';
import Button from "../base/forms/Button";
import {FC} from 'react'
import {useCreateIdentitiesMutation} from "common/services/useIdentity"; // we need this to make JSX compile
const Utils = require("../../../common/utils/utils")
type CreateUserType = {
    environmentId: string
}

const CreateUser: FC<CreateUserType> = ({environmentId}) => {
    const [value, setValue] = useState<string[]>([]);
    const [createIdentities, {isSuccess, isError} ] = useCreateIdentitiesMutation()
    const submit = ()=> {
        createIdentities({identifiers:value, environmentId, isEdge: Utils.getIsEdge()})
    }
    useEffect(()=>{
        if(isSuccess) {
            closeModal()
        }
    },[isSuccess])
    return (
        <div>
            <FormGroup>
                <label>
                    User IDs
                </label>
            </FormGroup>
            <FormGroup className="text-right">
                <ChipInput
                    placeholder="User1, User2, User3"
                    onChange={value => setValue(value)}
                    value={value}
                />
            </FormGroup>
            {isError && (
                <ErrorMessage error="Some Identities already exist and were not created"/>
            )}
            <FormGroup className="text-right">
                <Button onClick={submit} disabled={!value?.length} >
                    Create users
                </Button>
            </FormGroup>
        </div>
    )
}

export default CreateUser

module.exports = CreateUser;
