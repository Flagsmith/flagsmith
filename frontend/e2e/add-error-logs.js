let onError = window.onError
window.onerror = (message, source, lineno, colno, error) => {
    console.error(message + source + lineno + colno + error);
}
