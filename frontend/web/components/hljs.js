/*! highlight.js v9.12.0 | BSD3 License | git.io/hljslicense */
!(function (e) {
    const n = typeof window === 'object' && window || typeof self === 'object' && self;
    typeof exports !== 'undefined' ? e(exports) : n && (n.hljs = e({}), typeof define === 'function' && define.amd && define([], () => n.hljs));
}((e) => {
    function n(e) {
        return e.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function t(e) {
        return e.nodeName.toLowerCase();
    }

    function r(e, n) {
        const t = e && e.exec(n);
        return t && t.index === 0;
    }

    function a(e) {
        return k.test(e);
    }

    function i(e) {
        let n; let t; let r; let i; let
            o = `${e.className} `;
        if (o += e.parentNode ? e.parentNode.className : '', t = B.exec(o)) return w(t[1]) ? t[1] : 'no-highlight';
        for (o = o.split(/\s+/), n = 0, r = o.length; r > n; n++) if (i = o[n], a(i) || w(i)) return i;
    }

    function o(e) {
        let n; const t = {}; const
            r = Array.prototype.slice.call(arguments, 1);
        for (n in e) t[n] = e[n];
        return r.forEach((e) => {
            for (n in e) t[n] = e[n];
        }), t;
    }

    function u(e) {
        const n = [];
        return (function r(e, a) {
            for (let i = e.firstChild; i; i = i.nextSibling) {
                i.nodeType === 3 ? a += i.nodeValue.length : i.nodeType === 1 && (n.push({
                    event: 'start',
                    offset: a,
                    node: i,
                }), a = r(i, a), t(i).match(/br|hr|img|input/) || n.push({ event: 'stop', offset: a, node: i }));
            }
            return a;
        }(e, 0)), n;
    }

    function c(e, r, a) {
        function i() {
            return e.length && r.length ? e[0].offset !== r[0].offset ? e[0].offset < r[0].offset ? e : r : r[0].event === 'start' ? e : r : e.length ? e : r;
        }

        function o(e) {
            function r(e) {
                return ` ${e.nodeName}="${n(e.value).replace('"', '&quot;')}"`;
            }

            s += `<${t(e)}${E.map.call(e.attributes, r).join('')}>`;
        }

        function u(e) {
            s += `</${t(e)}>`;
        }

        function c(e) {
            (e.event === 'start' ? o : u)(e.node);
        }

        for (var l = 0, s = '', f = []; e.length || r.length;) {
            let g = i();
            if (s += n(a.substring(l, g[0].offset)), l = g[0].offset, g === e) {
                f.reverse().forEach(u);
                do c(g.splice(0, 1)[0]), g = i(); while (g === e && g.length && g[0].offset === l);
                f.reverse().forEach(o);
            } else g[0].event === 'start' ? f.push(g[0].node) : f.pop(), c(g.splice(0, 1)[0]);
        }
        return s + n(a.substr(l));
    }

    function l(e) {
        return e.v && !e.cached_variants && (e.cached_variants = e.v.map(n => o(e, { v: null }, n))), e.cached_variants || e.eW && [o(e)] || [e];
    }

    function s(e) {
        function n(e) {
            return e && e.source || e;
        }

        function t(t, r) {
            return new RegExp(n(t), `m${e.cI ? 'i' : ''}${r ? 'g' : ''}`);
        }

        function r(a, i) {
            if (!a.compiled) {
                if (a.compiled = !0, a.k = a.k || a.bK, a.k) {
                    const o = {}; const
                        u = function (n, t) {
                            e.cI && (t = t.toLowerCase()), t.split(' ').forEach((e) => {
                                const t = e.split('|');
                                o[t[0]] = [n, t[1] ? Number(t[1]) : 1];
                            });
                        };
                    typeof a.k === 'string' ? u('keyword', a.k) : x(a.k).forEach((e) => {
                        u(e, a.k[e]);
                    }), a.k = o;
                }
                a.lR = t(a.l || /\w+/, !0), i && (a.bK && (a.b = `\\b(${a.bK.split(' ').join('|')})\\b`), a.b || (a.b = /\B|\b/), a.bR = t(a.b), a.e || a.eW || (a.e = /\B|\b/), a.e && (a.eR = t(a.e)), a.tE = n(a.e) || '', a.eW && i.tE && (a.tE += (a.e ? '|' : '') + i.tE)), a.i && (a.iR = t(a.i)), a.r == null && (a.r = 1), a.c || (a.c = []), a.c = Array.prototype.concat.apply([], a.c.map(e => l(e === 'self' ? a : e))), a.c.forEach((e) => {
                    r(e, a);
                }), a.starts && r(a.starts, i);
                const c = a.c.map(e => (e.bK ? `\\.?(${e.b})\\.?` : e.b)).concat([a.tE, a.i]).map(n).filter(Boolean);
                a.t = c.length ? t(c.join('|'), !0) : {
                    exec() {
                        return null;
                    },
                };
            }
        }

        r(e);
    }

    function f(e, t, a, i) {
        function o(e, n) {
            let t; let
                a;
            for (t = 0, a = n.c.length; a > t; t++) if (r(n.c[t].bR, e)) return n.c[t];
        }

        function u(e, n) {
            if (r(e.eR, n)) {
                for (; e.endsParent && e.parent;) e = e.parent;
                return e;
            }
            return e.eW ? u(e.parent, n) : void 0;
        }

        function c(e, n) {
            return !a && r(n.iR, e);
        }

        function l(e, n) {
            const t = N.cI ? n[0].toLowerCase() : n[0];
            return e.k.hasOwnProperty(t) && e.k[t];
        }

        function p(e, n, t, r) {
            const a = r ? '' : I.classPrefix; let i = `<span class="${a}`; const
                o = t ? '' : C;
            return i += `${e}">`, i + n + o;
        }

        function h() {
            let e; let t; let r; let
                a;
            if (!E.k) return n(k);
            for (a = '', t = 0, E.lR.lastIndex = 0, r = E.lR.exec(k); r;) a += n(k.substring(t, r.index)), e = l(E, r), e ? (B += e[1], a += p(e[0], n(r[0]))) : a += n(r[0]), t = E.lR.lastIndex, r = E.lR.exec(k);
            return a + n(k.substr(t));
        }

        function d() {
            const e = typeof E.sL === 'string';
            if (e && !y[E.sL]) return n(k);
            const t = e ? f(E.sL, k, !0, x[E.sL]) : g(k, E.sL.length ? E.sL : void 0);
            return E.r > 0 && (B += t.r), e && (x[E.sL] = t.top), p(t.language, t.value, !1, !0);
        }

        function b() {
            L += E.sL != null ? d() : h(), k = '';
        }

        function v(e) {
            L += e.cN ? p(e.cN, '', !0) : '', E = Object.create(e, { parent: { value: E } });
        }

        function m(e, n) {
            if (k += e, n == null) return b(), 0;
            const t = o(n, E);
            if (t) return t.skip ? k += n : (t.eB && (k += n), b(), t.rB || t.eB || (k = n)), v(t, n), t.rB ? 0 : n.length;
            const r = u(E, n);
            if (r) {
                const a = E;
                a.skip ? k += n : (a.rE || a.eE || (k += n), b(), a.eE && (k = n));
                do E.cN && (L += C), E.skip || (B += E.r), E = E.parent; while (E !== r.parent);
                return r.starts && v(r.starts, ''), a.rE ? 0 : n.length;
            }
            if (c(n, E)) throw new Error(`Illegal lexeme "${n}" for mode "${E.cN || '<unnamed>'}"`);
            return k += n, n.length || 1;
        }

        var N = w(e);
        if (!N) throw new Error(`Unknown language: "${e}"`);
        s(N);
        let R; var E = i || N; var x = {}; var
            L = '';
        for (R = E; R !== N; R = R.parent) R.cN && (L = p(R.cN, '', !0) + L);
        var k = '';


        var B = 0;
        try {
            for (var M, j, O = 0; ;) {
                if (E.t.lastIndex = O, M = E.t.exec(t), !M) break;
                j = m(t.substring(O, M.index), M[0]), O = M.index + j;
            }
            for (m(t.substr(O)), R = E; R.parent; R = R.parent) R.cN && (L += C);
            return { r: B, value: L, language: e, top: E };
        } catch (T) {
            if (T.message && T.message.indexOf('Illegal') !== -1) return { r: 0, value: n(t) };
            throw T;
        }
    }

    function g(e, t) {
        t = t || I.languages || x(y);
        let r = { r: 0, value: n(e) }; let
            a = r;
        return t.filter(w).forEach((n) => {
            const t = f(n, e, !1);
            t.language = n, t.r > a.r && (a = t), t.r > r.r && (a = r, r = t);
        }), a.language && (r.second_best = a), r;
    }

    function p(e) {
        return I.tabReplace || I.useBR ? e.replace(M, (e, n) => (I.useBR && e === '\n' ? '<br>' : I.tabReplace ? n.replace(/\t/g, I.tabReplace) : '')) : e;
    }

    function h(e, n, t) {
        const r = n ? L[n] : t; const
            a = [e.trim()];
        return e.match(/\bhljs\b/) || a.push('hljs'), e.indexOf(r) === -1 && a.push(r), a.join(' ').trim();
    }

    function d(e) {
        let n; let t; let r; let o; let l; const
            s = i(e);
        a(s) || (I.useBR ? (n = document.createElementNS('http://www.w3.org/1999/xhtml', 'div'), n.innerHTML = e.innerHTML.replace(/\n/g, '').replace(/<br[ \/]*>/g, '\n')) : n = e, l = n.textContent, r = s ? f(s, l, !0) : g(l), t = u(n), t.length && (o = document.createElementNS('http://www.w3.org/1999/xhtml', 'div'), o.innerHTML = r.value, r.value = c(t, u(o), l)), r.value = p(r.value), e.innerHTML = r.value, e.className = h(e.className, s, r.language), e.result = {
            language: r.language,
            re: r.r,
        }, r.second_best && (e.second_best = { language: r.second_best.language, re: r.second_best.r }));
    }

    function b(e) {
        I = o(I, e);
    }

    function v() {
        if (!v.called) {
            v.called = !0;
            const e = document.querySelectorAll('pre code');
            E.forEach.call(e, d);
        }
    }

    function m() {
        addEventListener('DOMContentLoaded', v, !1), addEventListener('load', v, !1);
    }

    function N(n, t) {
        const r = y[n] = t(e);
        r.aliases && r.aliases.forEach((e) => {
            L[e] = n;
        });
    }

    function R() {
        return x(y);
    }

    function w(e) {
        return e = (e || '').toLowerCase(), y[e] || y[L[e]];
    }

    var E = []; var x = Object.keys; var y = {}; var L = {}; var k = /^(no-?highlight|plain|text)$/i; var B = /\blang(?:uage)?-([\w-]+)\b/i;


    var M = /((^(<[^>]+>|\t|)+|(?:\n)))/gm; var C = '</span>';


    var I = { classPrefix: 'hljs-', tabReplace: null, useBR: !1, languages: void 0 };
    return e.highlight = f, e.highlightAuto = g, e.fixMarkup = p, e.highlightBlock = d, e.configure = b, e.initHighlighting = v, e.initHighlightingOnLoad = m, e.registerLanguage = N, e.listLanguages = R, e.getLanguage = w, e.inherit = o, e.IR = '[a-zA-Z]\\w*', e.UIR = '[a-zA-Z_]\\w*', e.NR = '\\b\\d+(\\.\\d+)?', e.CNR = '(-?)(\\b0[xX][a-fA-F0-9]+|(\\b\\d+(\\.\\d*)?|\\.\\d+)([eE][-+]?\\d+)?)', e.BNR = '\\b(0b[01]+)', e.RSR = '!|!=|!==|%|%=|&|&&|&=|\\*|\\*=|\\+|\\+=|,|-|-=|/=|/|:|;|<<|<<=|<=|<|===|==|=|>>>=|>>=|>=|>>>|>>|>|\\?|\\[|\\{|\\(|\\^|\\^=|\\||\\|=|\\|\\||~', e.BE = {
        b: '\\\\[\\s\\S]',
        r: 0,
    }, e.ASM = { cN: 'string', b: "'", e: "'", i: '\\n', c: [e.BE] }, e.QSM = {
        cN: 'string',
        b: '"',
        e: '"',
        i: '\\n',
        c: [e.BE],
    }, e.PWM = { b: /\b(a|an|the|are|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|they|like|more)\b/ }, e.C = function (n, t, r) {
        const a = e.inherit({ cN: 'comment', b: n, e: t, c: [] }, r || {});
        return a.c.push(e.PWM), a.c.push({ cN: 'doctag', b: '(?:TODO|FIXME|NOTE|BUG|XXX):', r: 0 }), a;
    }, e.CLCM = e.C('//', '$'), e.CBCM = e.C('/\\*', '\\*/'), e.HCM = e.C('#', '$'), e.NM = {
        cN: 'number',
        b: e.NR,
        r: 0,
    }, e.CNM = { cN: 'number', b: e.CNR, r: 0 }, e.BNM = { cN: 'number', b: e.BNR, r: 0 }, e.CSSNM = {
        cN: 'number',
        b: `${e.NR}(%|em|ex|ch|rem|vw|vh|vmin|vmax|cm|mm|in|pt|pc|px|deg|grad|rad|turn|s|ms|Hz|kHz|dpi|dpcm|dppx)?`,
        r: 0,
    }, e.RM = {
        cN: 'regexp',
        b: /\//,
        e: /\/[gimuy]*/,
        i: /\n/,
        c: [e.BE, { b: /\[/, e: /\]/, r: 0, c: [e.BE] }],
    }, e.TM = { cN: 'title', b: e.IR, r: 0 }, e.UTM = {
        cN: 'title',
        b: e.UIR,
        r: 0,
    }, e.METHOD_GUARD = { b: `\\.\\s*${e.UIR}`, r: 0 }, e;
}));
hljs.registerLanguage('objectivec', (e) => {
    const t = { cN: 'built_in', b: '\\b(AV|CA|CF|CG|CI|CL|CM|CN|CT|MK|MP|MTK|MTL|NS|SCN|SK|UI|WK|XC)\\w+' }; const _ = {
        keyword: 'int float while char export sizeof typedef const struct for union unsigned long volatile static bool mutable if do return goto void enum else break extern asm case short default double register explicit signed typename this switch continue wchar_t inline readonly assign readwrite self @synchronized id typeof nonatomic super unichar IBOutlet IBAction strong weak copy in out inout bycopy byref oneway __strong __weak __block __autoreleasing @private @protected @public @try @property @end @throw @catch @finally @autoreleasepool @synthesize @dynamic @selector @optional @required @encode @package @import @defs @compatibility_alias __bridge __bridge_transfer __bridge_retained __bridge_retain __covariant __contravariant __kindof _Nonnull _Nullable _Null_unspecified __FUNCTION__ __PRETTY_FUNCTION__ __attribute__ getter setter retain unsafe_unretained nonnull nullable null_unspecified null_resettable class instancetype NS_DESIGNATED_INITIALIZER NS_UNAVAILABLE NS_REQUIRES_SUPER NS_RETURNS_INNER_POINTER NS_INLINE NS_AVAILABLE NS_DEPRECATED NS_ENUM NS_OPTIONS NS_SWIFT_UNAVAILABLE NS_ASSUME_NONNULL_BEGIN NS_ASSUME_NONNULL_END NS_REFINED_FOR_SWIFT NS_SWIFT_NAME NS_SWIFT_NOTHROW NS_DURING NS_HANDLER NS_ENDHANDLER NS_VALUERETURN NS_VOIDRETURN',
        literal: 'false true FALSE TRUE nil YES NO NULL',
        built_in: 'BOOL dispatch_once_t dispatch_queue_t dispatch_sync dispatch_async dispatch_once',
    }; const i = /[a-zA-Z@][a-zA-Z0-9_]*/; const
        n = '@interface @class @protocol @implementation';
    return {
        aliases: ['mm', 'objc', 'obj-c'],
        k: _,
        l: i,
        i: '</',
        c: [t, e.CLCM, e.CBCM, e.CNM, e.QSM, {
            cN: 'string',
            v: [{ b: '@"', e: '"', i: '\\n', c: [e.BE] }, { b: "'", e: "[^\\\\]'", i: "[^\\\\][^']" }],
        }, {
            cN: 'meta',
            b: '#',
            e: '$',
            c: [{ cN: 'meta-string', v: [{ b: '"', e: '"' }, { b: '<', e: '>' }] }],
        }, {
            cN: 'class',
            b: `(${n.split(' ').join('|')})\\b`,
            e: '({|$)',
            eE: !0,
            k: n,
            l: i,
            c: [e.UTM],
        }, { b: `\\.${e.UIR}`, r: 0 }],
    };
});
hljs.registerLanguage('cs', (e) => {
    const i = {
        keyword: 'abstract as base bool break byte case catch char checked const continue decimal default delegate do double enum event explicit extern finally fixed float for foreach goto if implicit in int interface internal is lock long nameof object operator out override params private protected public readonly ref sbyte sealed short sizeof stackalloc static string struct switch this try typeof uint ulong unchecked unsafe ushort using virtual void volatile while add alias ascending async await by descending dynamic equals from get global group into join let on orderby partial remove select set value var where yield',
        literal: 'null false true',
    }; const t = { cN: 'string', b: '@"', e: '"', c: [{ b: '""' }] }; const r = e.inherit(t, { i: /\n/ });


    const a = { cN: 'subst', b: '{', e: '}', k: i }; const c = e.inherit(a, { i: /\n/ });


    const n = { cN: 'string', b: /\$"/, e: '"', i: /\n/, c: [{ b: '{{' }, { b: '}}' }, e.BE, c] };


    const s = { cN: 'string', b: /\$@"/, e: '"', c: [{ b: '{{' }, { b: '}}' }, { b: '""' }, a] };


    const o = e.inherit(s, { i: /\n/, c: [{ b: '{{' }, { b: '}}' }, { b: '""' }, c] });
    a.c = [s, n, t, e.ASM, e.QSM, e.CNM, e.CBCM], c.c = [o, n, r, e.ASM, e.QSM, e.CNM, e.inherit(e.CBCM, { i: /\n/ })];
    const l = { v: [s, n, t, e.ASM, e.QSM] }; const
        b = `${e.IR}(<${e.IR}(\\s*,\\s*${e.IR})*>)?(\\[\\])?`;
    return {
        aliases: ['csharp'],
        k: i,
        i: /::/,
        c: [e.C('///', '$', {
            rB: !0,
            c: [{ cN: 'doctag', v: [{ b: '///', r: 0 }, { b: '<!--|-->' }, { b: '</?', e: '>' }] }],
        }), e.CLCM, e.CBCM, {
            cN: 'meta',
            b: '#',
            e: '$',
            k: { 'meta-keyword': 'if else elif endif define undef warning error line region endregion pragma checksum' },
        }, l, e.CNM, { bK: 'class interface', e: /[{;=]/, i: /[^\s:]/, c: [e.TM, e.CLCM, e.CBCM] }, {
            bK: 'namespace',
            e: /[{;=]/,
            i: /[^\s:]/,
            c: [e.inherit(e.TM, { b: '[a-zA-Z](\\.?\\w)*' }), e.CLCM, e.CBCM],
        }, {
            cN: 'meta',
            b: '^\\s*\\[',
            eB: !0,
            e: '\\]',
            eE: !0,
            c: [{ cN: 'meta-string', b: /"/, e: /"/ }],
        }, { bK: 'new return throw await else', r: 0 }, {
            cN: 'function',
            b: `(${b}\\s+)+${e.IR}\\s*\\(`,
            rB: !0,
            e: /[{;=]/,
            eE: !0,
            k: i,
            c: [{ b: `${e.IR}\\s*\\(`, rB: !0, c: [e.TM], r: 0 }, {
                cN: 'params',
                b: /\(/,
                e: /\)/,
                eB: !0,
                eE: !0,
                k: i,
                r: 0,
                c: [l, e.CNM, e.CBCM],
            }, e.CLCM, e.CBCM],
        }],
    };
});
hljs.registerLanguage('python', (e) => {
    const r = {
        keyword: 'and elif is global as in if from raise for except finally print import pass return exec else break not with class assert yield try while continue del or def lambda async await nonlocal|10 None True False',
        built_in: 'Ellipsis NotImplemented',
    }; const b = { cN: 'meta', b: /^(>>>|\.\.\.) / }; const c = { cN: 'subst', b: /\{/, e: /\}/, k: r, i: /#/ }; const a = {
        cN: 'string',
        c: [e.BE],
        v: [{ b: /(u|b)?r?'''/, e: /'''/, c: [b], r: 10 }, {
            b: /(u|b)?r?"""/,
            e: /"""/,
            c: [b],
            r: 10,
        }, { b: /(fr|rf|f)'''/, e: /'''/, c: [b, c] }, { b: /(fr|rf|f)"""/, e: /"""/, c: [b, c] }, {
            b: /(u|r|ur)'/,
            e: /'/,
            r: 10,
        }, { b: /(u|r|ur)"/, e: /"/, r: 10 }, { b: /(b|br)'/, e: /'/ }, { b: /(b|br)"/, e: /"/ }, {
            b: /(fr|rf|f)'/,
            e: /'/,
            c: [c],
        }, { b: /(fr|rf|f)"/, e: /"/, c: [c] }, e.ASM, e.QSM],
    }; const s = { cN: 'number', r: 0, v: [{ b: `${e.BNR}[lLjJ]?` }, { b: '\\b(0o[0-7]+)[lLjJ]?' }, { b: `${e.CNR}[lLjJ]?` }] };


    const i = { cN: 'params', b: /\(/, e: /\)/, c: ['self', b, s, a] };
    return c.c = [a, s, b], {
        aliases: ['py', 'gyp'],
        k: r,
        i: /(<\/|->|\?)|=>/,
        c: [b, s, a, e.HCM, {
            v: [{ cN: 'function', bK: 'def' }, { cN: 'class', bK: 'class' }],
            e: /:/,
            i: /[${=;\n,]/,
            c: [e.UTM, i, { b: /->/, eW: !0, k: 'None' }],
        }, { cN: 'meta', b: /^[\t ]*@/, e: /$/ }, { b: /\b(print|exec)\(/ }],
    };
});
hljs.registerLanguage('php', (e) => {
    const c = { b: '\\$+[a-zA-Z_-Ã¿][a-zA-Z0-9_-Ã¿]*' }; const i = { cN: 'meta', b: /<\?(php)?|\?>/ }; const t = {
        cN: 'string',
        c: [e.BE, i],
        v: [{ b: 'b"', e: '"' }, { b: "b'", e: "'" }, e.inherit(e.ASM, { i: null }), e.inherit(e.QSM, { i: null })],
    }; const
        a = { v: [e.BNM, e.CNM] };
    return {
        aliases: ['php3', 'php4', 'php5', 'php6'],
        cI: !0,
        k: 'and include_once list abstract global private echo interface as static endswitch array null if endwhile or const for endforeach self var while isset public protected exit foreach throw elseif include __FILE__ empty require_once do xor return parent clone use __CLASS__ __LINE__ else break print eval new catch __METHOD__ case exception default die require __FUNCTION__ enddeclare final try switch continue endfor endif declare unset true false trait goto instanceof insteadof __DIR__ __NAMESPACE__ yield finally',
        c: [e.HCM, e.C('//', '$', { c: [i] }), e.C('/\\*', '\\*/', {
            c: [{
                cN: 'doctag',
                b: '@[A-Za-z]+',
            }],
        }), e.C('__halt_compiler.+?;', !1, { eW: !0, k: '__halt_compiler', l: e.UIR }), {
            cN: 'string',
            b: /<<<['"]?\w+['"]?$/,
            e: /^\w+;?$/,
            c: [e.BE, { cN: 'subst', v: [{ b: /\$\w+/ }, { b: /\{\$/, e: /\}/ }] }],
        }, i, {
            cN: 'keyword',
            b: /\$this\b/,
        }, c, { b: /(::|->)+[a-zA-Z_\x7f-\xff][a-zA-Z0-9_\x7f-\xff]*/ }, {
            cN: 'function',
            bK: 'function',
            e: /[;{]/,
            eE: !0,
            i: '\\$|\\[|%',
            c: [e.UTM, { cN: 'params', b: '\\(', e: '\\)', c: ['self', c, e.CBCM, t, a] }],
        }, {
            cN: 'class',
            bK: 'class interface',
            e: '{',
            eE: !0,
            i: /[:\(\$"]/,
            c: [{ bK: 'extends implements' }, e.UTM],
        }, { bK: 'namespace', e: ';', i: /[\.']/, c: [e.UTM] }, { bK: 'use', e: ';', c: [e.UTM] }, { b: '=>' }, t, a],
    };
});
hljs.registerLanguage('javascript', (e) => {
    const r = '[A-Za-z$_][0-9A-Za-z$_]*';


    const t = {
        keyword: 'in of if for while finally var new function do return void else break catch instanceof with throw case default try this switch continue typeof delete let yield const export super debugger as async await static import from as',
        literal: 'true false null undefined NaN Infinity',
        built_in: 'eval isFinite isNaN parseFloat parseInt decodeURI decodeURIComponent encodeURI encodeURIComponent escape unescape Object Function Boolean Error EvalError InternalError RangeError ReferenceError StopIteration SyntaxError TypeError URIError Number Math Date String RegExp Array Float32Array Float64Array Int16Array Int32Array Int8Array Uint16Array Uint32Array Uint8Array Uint8ClampedArray ArrayBuffer DataView JSON Intl arguments require module console window document Symbol Set Map WeakSet WeakMap Proxy Reflect Promise',
    };


    const a = { cN: 'number', v: [{ b: '\\b(0[bB][01]+)' }, { b: '\\b(0[oO][0-7]+)' }, { b: e.CNR }], r: 0 };


    const n = { cN: 'subst', b: '\\$\\{', e: '\\}', k: t, c: [] };


    const c = { cN: 'string', b: '`', e: '`', c: [e.BE, n] };
    n.c = [e.ASM, e.QSM, c, a, e.RM];
    const s = n.c.concat([e.CBCM, e.CLCM]);
    return {
        aliases: ['js', 'jsx'],
        k: t,
        c: [{ cN: 'meta', r: 10, b: /^\s*['"]use (strict|asm)['"]/ }, {
            cN: 'meta',
            b: /^#!/,
            e: /$/,
        }, e.ASM, e.QSM, c, e.CLCM, e.CBCM, a, {
            b: /[{,]\s*/,
            r: 0,
            c: [{ b: `${r}\\s*:`, rB: !0, r: 0, c: [{ cN: 'attr', b: r, r: 0 }] }],
        }, {
            b: `(${e.RSR}|\\b(case|return|throw)\\b)\\s*`,
            k: 'return throw case',
            c: [e.CLCM, e.CBCM, e.RM, {
                cN: 'function',
                b: `(\\(.*?\\)|${r})\\s*=>`,
                rB: !0,
                e: '\\s*=>',
                c: [{ cN: 'params', v: [{ b: r }, { b: /\(\s*\)/ }, { b: /\(/, e: /\)/, eB: !0, eE: !0, k: t, c: s }] }],
            }, {
                b: /</,
                e: /(\/\w+|\w+\/)>/,
                sL: 'xml',
                c: [{ b: /<\w+\s*\/>/, skip: !0 }, {
                    b: /<\w+/,
                    e: /(\/\w+|\w+\/)>/,
                    skip: !0,
                    c: [{ b: /<\w+\s*\/>/, skip: !0 }, 'self'],
                }],
            }],
            r: 0,
        }, {
            cN: 'function',
            bK: 'function',
            e: /\{/,
            eE: !0,
            c: [e.inherit(e.TM, { b: r }), { cN: 'params', b: /\(/, e: /\)/, eB: !0, eE: !0, c: s }],
            i: /\[|%/,
        }, { b: /\$[(.]/ }, e.METHOD_GUARD, {
            cN: 'class',
            bK: 'class',
            e: /[{;=]/,
            eE: !0,
            i: /[:"\[\]]/,
            c: [{ bK: 'extends' }, e.UTM],
        }, { bK: 'constructor', e: /\{/, eE: !0 }],
        i: /#(?!!)/,
    };
});
hljs.registerLanguage('java', (e) => {
    const a = '[Ã€-Ê¸a-zA-Z_$][Ã€-Ê¸a-zA-Z_$0-9]*';


    const t = `${a}(<${a}(\\s*,\\s*${a})*>)?`;


    const r = 'false synchronized int abstract float private char boolean static null if const for true while long strictfp finally protected import native final void enum else break transient catch instanceof byte super volatile case assert short package default double public try this switch continue throws protected public private module requires exports do';


    const s = '\\b(0[bB]([01]+[01_]+[01]+|[01]+)|0[xX]([a-fA-F0-9]+[a-fA-F0-9_]+[a-fA-F0-9]+|[a-fA-F0-9]+)|(([\\d]+[\\d_]+[\\d]+|[\\d]+)(\\.([\\d]+[\\d_]+[\\d]+|[\\d]+))?|\\.([\\d]+[\\d_]+[\\d]+|[\\d]+))([eE][-+]?\\d+)?)[lLfF]?';


    const c = { cN: 'number', b: s, r: 0 };
    return {
        aliases: ['jsp'],
        k: r,
        i: /<\/|#/,
        c: [e.C('/\\*\\*', '\\*/', {
            r: 0,
            c: [{ b: /\w+@/, r: 0 }, { cN: 'doctag', b: '@[A-Za-z]+' }],
        }), e.CLCM, e.CBCM, e.ASM, e.QSM, {
            cN: 'class',
            bK: 'class interface',
            e: /[{;=]/,
            eE: !0,
            k: 'class interface',
            i: /[:"\[\]]/,
            c: [{ bK: 'extends implements' }, e.UTM],
        }, { bK: 'new throw return else', r: 0 }, {
            cN: 'function',
            b: `(${t}\\s+)+${e.UIR}\\s*\\(`,
            rB: !0,
            e: /[{;=]/,
            eE: !0,
            k: r,
            c: [{ b: `${e.UIR}\\s*\\(`, rB: !0, r: 0, c: [e.UTM] }, {
                cN: 'params',
                b: /\(/,
                e: /\)/,
                k: r,
                r: 0,
                c: [e.ASM, e.QSM, e.CNM, e.CBCM],
            }, e.CLCM, e.CBCM],
        }, c, { cN: 'meta', b: '@[A-Za-z]+' }],
    };
});
