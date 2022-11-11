export default {
    safeParseEventValue(e) { // safe attempt to parse form value
        if (!e) {
            return e;
        }
        if (typeof e === 'string') {
            return e;
        }
        const target = e || e.target;

        if (target.getAttribute) {
            return target.type === 'checkbox' || target.type === 'radio' ? target.getAttribute('checked')
                : target.getAttribute('data-value') || target.getAttribute('value');
        }

        if (e && e.target && (e.target.type === 'checkbox' || e.target.type === 'radio')) {
            return e.target.checked;
        }

        if (target.type && target.type === 'span' && e.target.textContent) {
            return e.target.textContent;
        }
        return e && e.target ? e.target.value : e;
    },

};
