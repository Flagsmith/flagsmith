// jsdom does not implement <dialog> modality; this mirrors the open/close behaviour the component uses.
export function installDialogPolyfill() {
    HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
        this.open = true;
    };
    HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
        this.open = false;
        this.dispatchEvent(new Event('close'));
    };
}
