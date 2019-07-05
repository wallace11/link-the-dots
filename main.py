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
        exit('Config error: {}'.format(e))

    # Overwrite options from commandline args
    options.update(
        {k: v
         for k, v in vars(args).items() if v and k != 'config'})

    options.get('dry_run', None) and style.print(
        'Running in dry (no change) mode...', 'notify', bold=False)

    extra_opts = {k: v for k, v in options.items() if k != 'containers'}
    containers = options.get('containers')

    for ctnr, opt in containers.items():
        try:
            try:
                title = 'Stowing files in "{}"'.format(ctnr)
                src, dest = map(shrinkuser,
                                (opt['source'], opt['destination']))
            except (KeyError, AttributeError):
                raise
            else:
                title = '{} ({} -> {})'.format(title, src, dest)
            finally:
                style.print(title, 'header')

            # Check destination
            if not opt.get('destination_create', False):
                if not os.access(os.path.expanduser(opt['destination']),
                                 os.W_OK):
                    style.print((
                        'Destination "{}" inaccessible. Use key '
                        '"destination_create" to force creation of destination.'
                    ).format(opt['destination']), 'warning')
                    continue

            stow_container(ctnr, **opt, **extra_opts)
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

    # Add boolean parameterc
    for option, desc in options.items():
        parser.add_argument('-{}'.format(option[0]),
                            '--{}'.format(option.replace('_', '-')),
                            dest=option,
                            default=None,
                            action='store_true',
                            help=desc)

    return parser.parse_args()


def stow_container(container, **opts):
    source = os.path.expanduser(opts['source'])

    # Work out packages to stow
    pkgs = [source] if opts.get('pkg') else opts.get('packages',
                                                     os.listdir(source))

    # Stow packages
    for pkg in pkgs:
        title = 'Stowing {}...'.format(
            pkg if not opts.get('pkg') else container)
        style.print(title, 'title', bold=False)

        # Skip packages that do not exist
        if not os.path.isdir(os.path.join(source, pkg)):
            style.done('Package was not found in dotfiles path. Skipping...',
                       'warning', len(title), 'warning')
            continue

        # Work out include/exclude files
        rule_fallback = ('include', [])
        try:
            if not opts.get('pkg'):
                rule, s_files = opts.get('rules', {}).get(pkg, rule_fallback)
            else:
                rule, s_files = opts.get('rules', rule_fallback)
        except ValueError:
            # Empty rules
            rule, s_files = rule_fallback

        # Execute
        stow_args = ('destination', 'name', 'dry_run', 'overwrite', 'verbose')
        stow_args = {arg: opts.get(arg, None) for arg in stow_args}
        stow_args.update({'source': os.path.join(source, pkg), rule: s_files})

        stow = Stow(**stow_args)
        to_stow = stow.collect()
        stow_result = stow.create(to_stow)

        show_results(stow_result, title, **opts)


def show_results(stow_result,
                 title,
                 source,
                 destination,
                 verbose=False,
                 group_output=False,
                 **kwargs):
    results = stow_result.get('results')

    # Set statistics
    stats = []
    for key, files in results.items():
        files and stats.append('{total} file(s) {res}'.format(total=len(files),
                                                              res=key))
    stats = ', '.join(stats) if stats else 'Nothing changed'

    # Show results
    if verbose:
        notify_states = results.items()
    else:
        # Notify only on certain results
        to_notify = ('replaced', 'skipped')
        notify_states = [(state, results[state]) for state in to_notify
                         if results[state]]

        # Just show summary if there's nothing special to display
        if not notify_states:
            style.done(stats, 'check', len(title) + 2)
            return True

    res = ((state, f) for state, files in notify_states for f in files)

    if not group_output:
        # Results are grouped by default and need to be sorted according to
        # the original files list otherwise.
        order = {f: i for i, f in enumerate(stow_result['files'])}
        res = sorted(res, key=lambda x: order.get(x[1]))

    for state, (src, dest) in res:
        style.link(shrinkuser(src),
                   shrinkuser(dest),
                   text=state.capitalize(),
                   **style.stow_states[state])

    style.print(stats, 'check', bold=True)


if __name__ == '__main__':
    run()
