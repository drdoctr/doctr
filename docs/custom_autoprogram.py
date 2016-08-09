"""
Custom autoprogram that doesn't wrap the command description

Assumes sphinxcontrib.autoprogram version 0.1.2.
"""
import sphinxcontrib.autoprogram

class AutoprogramDirective(sphinxcontrib.autoprogram.AutoprogramDirective):
    def make_rst(self):
        import_name, = self.arguments
        parser = sphinxcontrib.autoprogram.import_object(import_name or '__undefined__')
        parser.prog = self.options.get('prog', parser.prog)
        for commands, options, desc, epilog in sphinxcontrib.autoprogram.scan_programs(parser):
            command = ' '.join(commands)
            title = '{0} {1}'.format(parser.prog, command).rstrip()
            yield ''
            yield '.. program:: ' + title
            yield ''
            yield title
            yield ('!' if commands else '?') * len(title)
            yield ''
            ##################################################################
            # This is the only change, from
            #
            # yield desc or ''
            #
            # This prevents it from wrapping all the lines of the command
            # description into a single paragraph.
            ##################################################################
            yield from (desc or '').splitlines()
            yield ''
            yield parser.format_usage()
            yield ''
            for option_strings, help_ in options:
                yield '.. option:: {0}'.format(', '.join(option_strings))
                yield ''
                yield '   ' + help_.replace('\n', '   \n')
                yield ''
            yield ''
            for line in epilog.splitlines():
                yield line or ''

def setup(app):
    app.add_directive('autoprogram', AutoprogramDirective)
    sphinxcontrib.autoprogram.patch_option_role_to_allow_argument_form()
