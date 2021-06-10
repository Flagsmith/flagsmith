const getQueryString = (params) => {
    const esc = encodeURIComponent;
    return Object.keys(params)
        .map(k => `${esc(k)}=${esc(params[k])}`)
        .join('&');
};

module.exports = {
    token: '',
    type: '',

    status(response) { // handle ajax requests
        if (response.status >= 200 && response.status < 300) {
            return Promise.resolve(response);
        }
        if (response.status == 401) {
            AppActions.setUser(null);
        }
        response.clone().text() // cloned so response body can be used downstream
            .then((err) => {
                if (E2E && document.getElementById('e2e-error')) {
                    const error = {
                        url: response.url,
                        status: response.status,
                        error: err,
                    };
                    document.getElementById('e2e-error').innerText = JSON.stringify(error);
                }
                API.log(response.url, response.status, err);
            });
        return Promise.reject(response);
    },

    get(url, data, headers) {
        return this._request('get', url, data || null, headers);
    },

    dummy(data) {
        return function () {
            return new Promise(((resolve) => {
                resolve(data);
            }));
        };
    },

    put(url, data, headers) {
        return this._request('put', url, data, headers);
    },

    post(url, data, headers) {
        return this._request('post', url, data, headers);
    },

    delete(url, data, headers) {
        return this._request('delete', url, data, headers);
    },

    _request(method, url, data, headers = {}) {
        const options = {
            timeout: 60000,
            method,
            headers: {
                'Accept': 'application/json',
                ...headers,
            },
        };


        let req;


        var qs = '';

        if (method != 'get') options.headers['Content-Type'] = 'application/json; charset=utf-8';

        if (this.token) { // add auth tokens to headers of all requests
            options.headers.AUTHORIZATION = `Token ${this.token}`;
        }

        if (data) {
            if (method == 'get') {
                var qs = getQueryString(data);
                url += url.indexOf('?') !== -1 ? `&${qs}` : `?${qs}`;
            } else {
                options.body = JSON.stringify(data);
            }
        } else if (method == 'post' || method == 'put') {
            options.body = '{}';
        }

        if (E2E && document.getElementById('e2e-request')) {
            const payload = {
                url,
                options,
            };
            document.getElementById('e2e-request').innerText = JSON.stringify(payload);
        }

        req = fetch(url, options);
        return req
            .then(this.status)
            .then((response) => { // always return json
                let contentType = response.headers.get('content-type');
                if (!contentType) {
                    contentType = response.headers.get('Content-Type');
                }
                if (contentType && contentType.indexOf('application/json') !== -1) {
                    return response.json();
                }
                return {};
            })
            .then((response) => {
                API.log(url, 200, response);
                return response;
            });
    },

    setToken(_token) { // set the token for future requests
        this.token = _token;
    },
};
