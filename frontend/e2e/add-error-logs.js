let onError = window.onError
window.onerror = (message, source, lineno, colno, error) => {
    console.error(JSON.stringify({ message, source, lineno, colno, error }));
}
