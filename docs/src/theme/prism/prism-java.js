;(function (Prism) {
  let keywords =
    /\b(?:abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|exports|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|module|native|new|non-sealed|null|open|opens|package|permits|private|protected|provides|public|record(?!\s*[(){}[\]<>=%~.:,;?+\-*/&|^])|requires|return|sealed|short|static|strictfp|super|switch|synchronized|this|throw|throws|to|transient|transitive|try|uses|var|void|volatile|while|with|yield)\b/

  // full package (optional) + parent classes (optional)
  let classNamePrefix = /(?:[a-z]\w*\s*\.\s*)*(?:[A-Z]\w*\s*\.\s*)*/.source

  // based on the java naming conventions
  let className = {
    inside: {
      'namespace': {
        inside: {
          'punctuation': /\./,
        },
        pattern: /^[a-z]\w*(?:\s*\.\s*[a-z]\w*)*(?:\s*\.)?/,
      },
      'punctuation': /\./,
    },
    lookbehind: true,
    pattern: RegExp(
      /(^|[^\w.])/.source +
        classNamePrefix +
        /[A-Z](?:[\d_A-Z]*[a-z]\w*)?\b/.source,
    ),
  }

  Prism.languages.java = Prism.languages.extend('clike', {
    'class-name': [
      className,
      {
        inside: className.inside,

        lookbehind: true,
        // variables, parameters, and constructor references
        // this to support class names (or generic parameters) which do not contain a lower case letter (also works for methods)
        pattern: RegExp(
          /(^|[^\w.])/.source +
            classNamePrefix +
            /[A-Z]\w*(?=\s+\w+\s*[;,=()]|\s*(?:\[[\s,]*\]\s*)?::\s*new\b)/
              .source,
        ),
      },
      {
        inside: className.inside,

        lookbehind: true,
        // class names based on keyword
        // this to support class names (or generic parameters) which do not contain a lower case letter (also works for methods)
        pattern: RegExp(
          /(\b(?:class|enum|extends|implements|instanceof|interface|new|record|throws)\s+)/
            .source +
            classNamePrefix +
            /[A-Z]\w*\b/.source,
        ),
      },
    ],
    'constant': /\b[A-Z][A-Z_\d]+\b/,
    'function': [
      Prism.languages.clike.function,
      {
        lookbehind: true,
        pattern: /(::\s*)[a-z_]\w*/,
      },
    ],
    'keyword': keywords,
    'number':
      /\b0b[01][01_]*L?\b|\b0x(?:\.[\da-f_p+-]+|[\da-f_]+(?:\.[\da-f_p+-]+)?)\b|(?:\b\d[\d_]*(?:\.[\d_]*)?|\B\.\d[\d_]*)(?:e[+-]?\d[\d_]*)?[dfl]?/i,
    'operator': {
      lookbehind: true,
      pattern:
        /(^|[^.])(?:<<=?|>>>?=?|->|--|\+\+|&&|\|\||::|[?:~]|[-+*/%&|^!=<>]=?)/m,
    },
    'string': {
      greedy: true,
      lookbehind: true,
      pattern: /(^|[^\\])"(?:\\.|[^"\\\r\n])*"/,
    },
  })

  Prism.languages.insertBefore('java', 'string', {
    'char': {
      greedy: true,
      pattern: /'(?:\\.|[^'\\\r\n]){1,6}'/,
    },
    'triple-quoted-string': {
      alias: 'string',

      greedy: true,
      // http://openjdk.java.net/jeps/355#Description
      pattern: /"""[ \t]*[\r\n](?:(?:"|"")?(?:\\.|[^"\\]))*"""/,
    },
  })

  Prism.languages.insertBefore('java', 'class-name', {
    'annotation': {
      alias: 'punctuation',
      lookbehind: true,
      pattern: /(^|[^.])@\w+(?:\s*\.\s*\w+)*/,
    },
    'generics': {
      inside: {
        'class-name': className,
        'keyword': keywords,
        'operator': /[?&|]/,
        'punctuation': /[<>(),.:]/,
      },
      pattern:
        /<(?:[\w\s,.?]|&(?!&)|<(?:[\w\s,.?]|&(?!&)|<(?:[\w\s,.?]|&(?!&)|<(?:[\w\s,.?]|&(?!&))*>)*>)*>)*>/,
    },
    'import': [
      {
        inside: {
          'class-name': /\w+/,
          'namespace': className.inside.namespace,
          'operator': /\*/,
          'punctuation': /\./,
        },
        lookbehind: true,
        pattern: RegExp(
          /(\bimport\s+)/.source +
            classNamePrefix +
            /(?:[A-Z]\w*|\*)(?=\s*;)/.source,
        ),
      },
      {
        alias: 'static',
        inside: {
          'class-name': /\w+/,
          'namespace': className.inside.namespace,
          'operator': /\*/,
          'punctuation': /\./,
          'static': /\b\w+$/,
        },
        lookbehind: true,
        pattern: RegExp(
          /(\bimport\s+static\s+)/.source +
            classNamePrefix +
            /(?:\w+|\*)(?=\s*;)/.source,
        ),
      },
    ],
    'namespace': {
      inside: {
        'punctuation': /\./,
      },
      lookbehind: true,
      pattern: RegExp(
        /(\b(?:exports|import(?:\s+static)?|module|open|opens|package|provides|requires|to|transitive|uses|with)\s+)(?!<keyword>)[a-z]\w*(?:\.[a-z]\w*)*\.?/.source.replace(
          /<keyword>/g,
          function () {
            return keywords.source
          },
        ),
      ),
    },
  })
})
