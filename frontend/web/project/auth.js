// import './lib/fb';

export const Facebook = {
    init: (appId) => {
        window.fbAsyncInit = function () {
            FB.init({
                appId,
                xfbml: true,
                version: 'v2.7',
            });
        };
    },
    login(permissions) {
        return new Promise((resolve) => {
            if (typeof FB !== 'undefined') {
                FB.login(() => {
                    if (FB.getAccessToken()) {
                        resolve(FB.getAccessToken());
                    }
                }, { scope: permissions || 'public_profile,email' });
                return true;
            }
            return false;
        });
    },
    logout: () => new Promise((resolve) => {
        if (typeof FB !== 'undefined') {
            FB.logout((response) => {
                resolve();
                return true;
            });
        } else {
            return false;
        }
    }),
};
