import { useState, useEffect, useRef, useCallback } from "react"
import { RouterChildContext } from "react-router-dom"
import { Modal, ModalHeader, ModalBody } from "reactstrap"

/**
 * useFormNotSavedModal
 * @param {history: RouterChildContext['router']['history']} history - The history object
 * @param {string} warningMessage - The message to show when user attempts to leave
 * @returns {[React.FC, Function, boolean]}
 */

type UseFormNotSavedModalReturn = [React.FC, React.Dispatch<React.SetStateAction<boolean>>, boolean]

interface UseFormNotSavedModalOptions {
  warningMessage?: string
  onDiscard?: () => void
}

const useFormNotSavedModal = (
  history: RouterChildContext['router']['history'],
  options: UseFormNotSavedModalOptions = {}
): UseFormNotSavedModalReturn => {
    const { onDiscard, warningMessage = "You have unsaved changes, are you sure you want to leave?" } = options

    const [isDirty, setIsDirty] = useState(false)
    const [isNavigating, setIsNavigating] = useState(false);
    const [nextLocation, setNextLocation] = useState<Location | null>(null);

    const unblockRef = useRef<(() => void) | null>(null);
    useEffect(() => {
        if (!isDirty) return;

        const unblock = history.block((transition: Location) => {
            setNextLocation(transition);
            setIsNavigating(true);
            return false;
        });

        unblockRef.current = unblock;
        return () => {
            if (unblockRef.current) {
                unblockRef.current();
            }
            unblockRef.current = null;
        };
    }, [isDirty, history]);

    const confirmNavigation = useCallback(() => {
        // allow the route change to happen
        if (unblockRef.current) {
            unblockRef.current(); // unblocks
            unblockRef.current = null;
        }
        // navigate
        if (nextLocation) {
            history.push(`${nextLocation.pathname}${nextLocation.search}`);
        }
        if (onDiscard) {
            onDiscard()
        }
        setIsDirty(false)
        setIsNavigating(false);
        setNextLocation(null);
    }, [nextLocation, history, onDiscard]);

    const cancelNavigation = useCallback(() => {
        history.push(`${history.location.pathname}${history.location.search}`);
        setIsNavigating(false);
        setNextLocation(null);
    }, [history]);

    // Listen for browser/tab close (the 'beforeunload' event)
    useEffect(() => {
        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            if (!isDirty) return
            event.preventDefault()
            event.returnValue = warningMessage
        }

        window.addEventListener("beforeunload", handleBeforeUnload)
        return () => {
            window.removeEventListener("beforeunload", handleBeforeUnload)
        }
    }, [isDirty, warningMessage])

    const DirtyFormModal = () => (
        <Modal isOpen={isDirty && isNavigating} toggle={cancelNavigation}>
            <ModalHeader>
                <h5>Unsaved Changes</h5>
            </ModalHeader>
            <ModalBody>
                <p>{warningMessage}</p>
            </ModalBody>
            <div className="modal-footer">
                <Button onClick={confirmNavigation} theme="secondary" className="mr-2">Yes, discard changes</Button>
                <Button onClick={cancelNavigation} class="btn-primary">Cancel</Button>
            </div>
        </Modal>
    )

    return [DirtyFormModal, setIsDirty, isDirty]
}

export default useFormNotSavedModal
