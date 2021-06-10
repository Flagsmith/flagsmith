// Redirect routes to index.html for the single page app
module.exports = function (req, res, next) {
    const headers = req.headers;
    let rewriteTarget = '/index.html';

    if (req.method !== 'GET') {
        // req.url = rewriteTarget.split('/')[rewriteTarget.split('/').length - 1];
        return next();
    } if (!headers || typeof headers.accept !== 'string') {
        req.url = rewriteTarget.split('/')[rewriteTarget.split('/').length - 1];
        return next();
    } if (headers.accept.indexOf('application/json') === 0) {
        req.url = rewriteTarget.split('/')[rewriteTarget.split('/').length - 1];
        return next();
    } if (headers.accept.indexOf('html') === -1) {
        req.url = `/${req.url.split('/')[req.url.split('/').length - 1]}`;
        return next();
    }


    const parsedUrl = req.url;


    const parts = parsedUrl.split('/');


    const lastPart = parts[parts.length - 1].split('?')[0]; // get last part of url without queryparam

    if (parsedUrl.indexOf('/api/') !== -1) {
        return next();
    }
    if (lastPart.indexOf('.') !== -1) {
        return next();
    }

    rewriteTarget = '/';
    req.url = rewriteTarget;
    next();
};
