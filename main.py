#!/usr/bin/env python3

from sys import exit
import argparse
import os

from linkthedots.config import Config, options
from linkthedots.stow import Stow
from linkthedots.style import Style
from linkthedots.functions import shrinkuser

# Setting globals
style = Style()


def run():
    # Parse terminal arguments
    args = parse_args()

    # Read config
    try:
        options = Config(conf=args.config).read()
    except Warning as e:
        exit(f'Config error: {e}')

    # Overwrite options from commandline args
    options.update(
        {k: v for k, v in vars(args).items() if v and k != 'config'})

    if options.get('dry_run', None):
        style.print('Running in dry (no change) mode...', 'notify')

    extra_opts = {k: v for k, v in options.items() if k != 'containers'}
    containers = options.get('containers')

    for ctnr, opt in containers.items():
        try:
            try:
                title = f'⠶ Stowing packages in "{ctnr}"'
                src, dest = map(shrinkuser,
                                (opt['source'], opt['destination']))
            except (KeyError, AttributeError):
                raise
            else:
                title = f'{title} ({src} -> {dest})'
            finally:
                style.print(title, 'header')

            # Check destination
            if not opt.get('destination_create', False):
                if not os.access(os.path.expanduser(opt['destination']),
                                 os.W_OK):
                    style.print((
                        f'Destination "{opt["destination"]}" inaccessible.'
                        ' Use key "destination_create" to force creation'
                        ' of destination.'
                    ), 'warning')
                    continue

            stow_container(ctnr, **opt, **extra_opts)

            if not options.get('verbose'):
                style.prepend('check')

        except (TypeError, KeyError, AttributeError):
            style.print(
                'Invalid source/destination setting. Skipping...', 'warning')


def parse_args():
    parser = argparse.ArgumentParser(description='Link your dot(file)s.')
    parser.add_argument('-c',
                        '--config',
                        dest='config',
                        default='config.json',
                        help='Path to the config file')

    # Add boolean parameters
    for option, desc in options.items():
        parser.add_argument(f'-{option[0]}',
                            f'--{option.replace("_", "-")}',
                            dest=option,
                            default=None,
                            action='store_true' if option != 'verbose' else 'count',
                            help=desc)

    return parser.parse_args()


def stow_container(container, **opts):
    source = os.path.expanduser(opts['source'])
    is_pkg = opts.get('pkg')

    # Work out packages to stow
    pkgs = [container] if is_pkg else opts.get('packages',
                                               os.listdir(source))

    verbose = opts.get('verbose')

    # Stow packages
    for pkg in sorted(pkgs):
        if verbose:
            title = f'Stowing {pkg}...'
            style.print(title, 'title', bold=False)
        else:
            title = None

        # Work out include/exclude files
        rule_fallback = ('include', [])
        try:
            rule, s_files = opts.get('rules', {}).get(pkg, rule_fallback)
        except ValueError:
            # Empty rules
            rule, s_files = rule_fallback

        # Execute
        stow_args = ('destination', 'name', 'dry_run', 'overwrite')
        stow_args = {arg: opts.get(arg, None) for arg in stow_args}
        stow_args.update({
            'source': source if is_pkg else os.path.join(source, pkg),
            rule: s_files
        })

        stow = Stow(**stow_args)
        to_stow = stow.collect()
        stow_result = stow.create(to_stow)

        show_pkg_results(stow_result, title, **opts)


def show_pkg_results(stow_result,
                     title,
                     source,
                     destination,
                     verbose=False,
                     group_output=False,
                     **kwargs):
    results = stow_result.get('results')

    # Set statistics
    stats = [f'{len(files)} file(s) {state}'
             for state, files in results.items() if files]
    output = {'text': ', '.join(stats), 'style': 'check'}

    if not output['text']:
        if not os.path.isdir(source):
            output = {
                'text': "Package wasn't found in source. Skipping...",
                'style': 'warning'
            }
        else:
            output['text'] = 'Nothing changed...'
        verbose = False  # There's really nothing to show

    # Show results
    if verbose > 1:
        notify_states = results.items()
    else:
        # Notify only on certain results
        to_notify = ('stowed', 'replaced', 'skipped')
        notify_states = [(state, results[state]) for state in to_notify
                         if results[state]]

        # Just show summary if there's nothing special to display
        if not notify_states:
            verbose and style.done(**output, col=len(title) + 2)
            return True

    # List of each file and its result (state)
    res = [(state, f) for state, files in notify_states for f in files]

    # Sort results according to the original file list (grouped by default)
    if not group_output:
        order = {f: i for i, f in enumerate(stow_result['files'])}
        res = sorted(res, key=lambda x: order.get(x[1]))

    for state, (src, dest) in res:
        style.link(shrinkuser(src),
                   shrinkuser(dest),
                   text=state.capitalize(),
                   **style.stow_states[state])

    style.print(**output, bold=True)


if __name__ == '__main__':
    run()
