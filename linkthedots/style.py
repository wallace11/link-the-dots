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
        self.RIGHT = lambda x: '{}C'.format(x)
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
                # 'icon': '♻️'
            },
            'replaced': {
                'color': 'magenta',
                # 'icon': '📥'
            },
            'skipped': {
                'color': 'red'
            }
        }

    def _get_code(self, code, suffix='', *args):
        code = getattr(self, code.upper())
        if args:
            code = code(*args)
        return '\33[{code}{suffix}'.format(code=code, suffix=suffix)

    def _set_color(self,
                   text,
                   color,
                   bold=False,
                   underline=False,
                   italic=False):
        if not text:
            return ''
        output = [
            self._get_code(color, 'm'), text,
            self._get_code('reset', 'm')
        ]
        bold and output.insert(1, self._get_code('bold', 'm'))
        italic and output.insert(1, self._get_code('italic', 'm'))
        underline and output.insert(1, self._get_code('underline', 'm'))
        return ''.join(output)

    def _set_command(self, command, *args):
        return self._get_code(command, '', *args)

    def _msg(self, text, sign, colors=('black', 'white'), **kwargs):
        if isinstance(colors, str):
            colors = [colors] * 2
        output = [
            self._set_color(sign, colors[0], **kwargs),
            self._set_color(text, colors[1], **kwargs)
        ]
        output = filter(None, output)
        return ' '.join(output)

    def print(self, text, style, **kwargs):
        print(self._msg(text, **self.templates[style], **kwargs))

    def link(self, src, dest, icon='🔗', text='Linking', color='green'):
        output = [
            self._set_color('{} {}'.format(icon, text), 'white', bold=False),
            self._set_color(src, 'blue', bold=True),
            self._set_color('➡', 'reset', bold=False),
            self._set_color(dest, color, bold=True)
        ]
        print(' '.join(output))

    def done(self, text, style, col):
        output = [
            self._set_command('erase_line'),
            self._set_command('up'),
            self._msg('', **self.templates[style]),
            self._set_command('right', col),
            self._msg(text,
                      '',
                      colors=self.templates[style]['colors'],
                      bold=True)
        ]
        print(''.join(output))
