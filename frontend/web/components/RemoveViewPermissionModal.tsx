import Button from "./base/forms/Button"

type RemoveViewPermissionModalProps = {
    level: string
    onConfirm: () => void
    onCancel: () => void
}

const RemoveViewPermissionModal = ({
    level,
    onCancel,
    onConfirm,
}: RemoveViewPermissionModalProps) => {
    return (
        <div>
            <div>
                Removing <b>view {level} permission</b> will remove all other user
                permissions for this {level}.
            </div>
            <div className='text-right mt-2'>
                <Button
                    className='mr-2'
                    onClick={() => {
                        onCancel()
                    }}
                >
                    Cancel
                </Button>
                <Button
                    theme='danger'
                    onClick={() => {
                        onConfirm()
                    }}
                >
                    Confirm
                </Button>
            </div>
        </div>
    )
}

export type { RemoveViewPermissionModalProps }
export default RemoveViewPermissionModal