module.exports = {

    enumeration: {
        get(value) { // MY_CONSTANT > My constant
            if (!value) {
                return '';
            }
            return Format.camelCase(value.replace(/_/g, ' '));
        },
        set(value) { // My Constant > MY_CONSTANT
            return value.replace(/ /g, '_').toUpperCase();
        },
    },

    money(value, defaultValue) {
        if (value == 0) {
            return defaultValue == null ? 'FREE' : defaultValue;
        }

        return value && `£${(value).toFixed(2).replace(/./g, (c, i, a) => (i && c !== '.' && ((a.length - i) % 3 === 0) ? `,${c}` : c))}`;
    },

    age(value) { // DATE > 10
        if (value) {
            const a = moment();


            const b = moment(value);
            return a.diff(b, 'years');
        }
        return value;
    },

    dateAndTime(value) {
        return Format.moment(value, 'MMMM Do YYYY, h:mm a');
    },

    monthAndYear(value) {
        return Format.moment(value, 'MMM YYYY');
    },

    time(value) { // DATE > 10:00pm
        return Format.moment(value, 'hh:mm a');
    },

    countdown(value) { // DATE > NOW || 10d1h10m
        let duration;
        if (value) {
            if (Utils.isInPast(value)) {
                return 'Now';
            }
            duration = moment.duration({ to: moment(value), from: moment() });
            return `${Format.nearestTen(parseInt(duration.asDays()))}d ${Format.nearestTen(duration.hours())}h ${
                Format.nearestTen(duration.minutes())}m`;
        }
        return value;
    },

    countdownMinutes(value) { // DATE > 10:05
        let duration;
        if (value) {
            duration = moment.duration({ to: moment(value), from: moment() });
            return `${Format.nearestTen(parseInt(duration.minutes()))}:${Format.nearestTen(duration.seconds())}`;
        }
        return value;
    },

    ago(value) { // DATE > 5 minutes ago (see moment docs)
        if (value) {
            const m = moment(value);
            return m.fromNow();
        }
        return value;
    },

    moment(value, format) { // DATE, hh:mm > 23:00
        if (value) {
            const m = moment(value);
            return m.format(format);
        }
        return value;
    },

    nearestTen(value) { // 11 > 10
        return value >= 10 ? value : `0${value}`;
    },

    camelCase(val) { // hello world > Hello world
        return val.charAt(0).toUpperCase() + val.slice(1).toLowerCase();
    },

    fullName(person) { // {firstName:'Kyle', lastName:'Johnson'} > Kyle Johnson
        if (!person) {
            return '';
        }
        const fn = person.firstName || '';


        const sn = person.lastName || '';

        return fn ? `${Format.camelCase(fn)} ${Format.camelCase(sn)}` : Format.camelCase(sn);
    },

    initialAndLastName(person) { // {firstName:'Kyle', lastName:'Johnson'} > K. Johnson
        const value = Format.fullName(person);


        let words;

        if (!value) {
            return value;
        }

        words = value.split(' ');

        if (words.length > 1) {
            return `${words[0].charAt(0).toUpperCase()}.` + ` ${words[words.length - 1]}`;
        }

        return value;
    },

    cssImage(value) { // lol.jpg  > url('lol.jpg')
        return value ? `url("${value}")` : 'none';
    },

    ordinal(value) {
        const s = ['th', 'st', 'nd', 'rd'];


        const v = value % 100;
        return value ? value + (s[(v - 20) % 10] || s[v] || s[0]) : '';
    },

    truncateText(text, numberOfChars) { // lol,1 > l...
        if (text) {
            if (text.length > numberOfChars) {
                return `${text.substring(0, numberOfChars)}...`;
            }
        }
        return text;
    },

    removeAccents(str) { // Sergio Agüero > Sergio Aguero
        if (!str) {
            return str;
        }

        for (let i = 0; i < Utils.accents.length; i++) {
            str = str.replace(Utils.accents[i].letters, Utils.accents[i].base);
        }

        return str;
    },
};
