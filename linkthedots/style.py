class Style():
    def __init__(self):
        self.RESET = '0'
        self.BOLD = '1'
        self.ITALIC = '3'
        self.UNDERLINE = '4'
        self.BLACK = '30'
        self.RED = '31'
        self.GREEN = '32'
        self.YELLOW = '33'
        self.BLUE = '34'
        self.MAGENTA = '35'
        self.CYAN = '36'
        self.WHITE = '37'
        self.ERASE_LINE = 'K'
        self.UP = '1A'
        self.RIGHT = lambda count: f'{count}C'
        self.templates = {
            'header': {
                'sign': '',
                'colors': 'yellow',
                'bold': True,
                'underline': True
            },
            'title': {
                'sign': '➡',
                'colors': 'yellow'
            },
            'check': {
                'sign': '✔',
                'colors': ('green', 'cyan')
            },
            'warning': {
                'sign': '✘',
                'colors': ('red', 'magenta')
            },
            'notify': {
                'sign': '‼',
                'colors': ('red', 'cyan')
            }
        }
        self.stow_states = {
            'stowed': {
                'color': 'green'
            },
            'restowed': {
                'color': 'cyan',
                'icon': '♻️'
            },
            'replaced': {
                'color': 'magenta',
                'icon': '📥'
            },
            'skipped': {
                'color': 'red'
            }
        }

    def _get_code(self, code, suffix='', *args):
        """
        Returns a terminal code corresponding to its name
        (defined by this module)
        """
        # This simplifies calls to this function
        # by automatically converting names to attributes
        code = getattr(self, code.upper())

        # Some terminal codes have optional arguments (like going up x times)
        if args:
            code = code(*args)

        return f'\33[{code}{suffix}'

    def _format(self, text, *styles):
        """
        Returns a formatted string using corresponding terminal codes.
        Options: color name, bold, underline, italic
        """
        if not text:
            return ''

        output = [self._get_code(style, 'm') for style in styles]
        output += [text, self._get_code('reset', 'm')]

        return ''.join(output)

    def _command(self, command, *args):
        """ Returns a formatted terminal code for the corrosponding command """
        return self._get_code(command, '', *args)

    def _msg(self, text, sign=None, colors=('black', 'white'), **formats):
        """
        Forms a string consisting of individually-colored text and sign strings.
        Additional styles are applied uniformly
        """
        if isinstance(colors, str):
            colors = [colors] * 2

        text_to_color = (zip([sign, text], colors) if sign
                         else [[text, colors[1]]])

        output = [self._format(text, color, *formats.keys())
                  for text, color in text_to_color]

        return ' '.join(output)

    def print(self, text, style=None, **formats):
        output = (self._msg(text, **self.templates[style], **formats) if style
                  else text)
        print(output)

    def link(self, src, dest, icon='🔗', text='Linking', color='green'):
        """ Prints out a predefined template for links """
        output = [
            self._format(f'{icon} {text}', 'white', 'bold'),
            self._format(src, 'blue', 'bold'),
            self._format('➡', 'reset', 'bold'),
            self._format(dest, color, 'bold')
        ]
        self.print(' '.join(output))

    def prepend(self, template):
        """
        Prepends a sign from `template` to a previous line.
        """
        output = [
            self._command('erase_line'),
            self._command('up'),
            self._msg('', **self.templates[template])
        ]
        self.print(''.join(output))

    def done(self, text, style, col):
        """
        Prints out a predefined template for "done" messages.
        They come at the end of the previous line,
        so the exact position (col) is needed.
        """
        output = [
            self._command('erase_line'),
            self._command('up'),
            self._command('right', col + 1),
            self._format(text, *self.templates[style]['colors'], 'bold')
        ]
        self.print(''.join(output))
