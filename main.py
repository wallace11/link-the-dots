#!/usr/bin/env python3

from sys import exit
import argparse
import os

from linkthedots.config import Config
from linkthedots.stow import Stow
from linkthedots.style import Style
from linkthedots.functions import shrinkuser

# Setting globals
style = Style()


def run():
    # Parse terminal arguments
    parser = argparse.ArgumentParser(description='Link your dot(file)s.')
    parser.add_argument('-c',
                        '--config',
                        dest='config',
                        default='config.json',
                        help='Path to the config file')
    parser.add_argument('-d',
                        '--dry-run',
                        dest='dry_run',
                        default=None,
                        action='store_true',
                        help='Forces dry-run (no change) mode')
    args = parser.parse_args()

    try:
        options = Config(conf=args.config).read()
    except Warning as e:
        exit('Config error: {}'.format(e))

    if args.dry_run:
        options['dry_run'] = True

    options.get('dry_run', None) and style.print(
        'Running in dry (no change) mode...', 'notify', bold=False)

    extra_opts = {k: v for k, v in options.items() if k != 'containers'}

    containers = options.get('containers')

    if not containers:
        style.print('Nothing to do...', 'warning')

    for ctnr, opt in containers.items():
        try:
            try:
                title = 'Stowing files in "{}"'.format(ctnr)
                src, dest = map(shrinkuser,
                                (opt['source'], opt['destination']))
            except KeyError:
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
        except (TypeError, KeyError):
            style.print(
                'No valid destination for container "{}". Skipping...'.format(
                    ctnr), 'warning')


def stow_container(container, **opts):
    source = os.path.expanduser(opts['source'])

    # Work out packages to stow
    if opts.get('pkg', False):
        pkgs = [source]
    else:
        pkgs = opts.get('packages', os.listdir(source))

    # Stow packages
    for pkg in pkgs:
        title = 'Stowing {}...'.format(pkg)
        style.print(title, 'title', bold=False)

        # Skip packages that do not exist
        if not os.path.isdir(os.path.join(source, pkg)):
            style.done('Package was not found in dotfiles path. Skipping...',
                       'warning', len(title), 'warning')
            continue

        # Work out include/exclude files
        try:
            rule, s_files = opts['rules'][pkg]
        except KeyError:
            rule, s_files = 'include', []

        # Execute
        stow_args = ('destination', 'hostname', 'dry_run', 'overwrite',
                     'verbose')
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
                 dry_run=False,
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
    if dry_run:
        notify_states = results.items()
    else:
        notify_states = [
            results[k] and (k, results[k]) for k in ('replaced', 'skipped')
        ]

        if not any(notify_states):
            style.done(stats, 'check', len(title), 'notify')
            return True

        notify_states = list(filter(None, notify_states))

    res = ((state, f) for state, files in notify_states for f in files)
    if not group_output:
        order = {f: i for i, f in enumerate(stow_result['files'])}
        res = sorted(res, key=lambda x: order.get(x[1]))

    for state, (src, dest) in res:
        style.link(shrinkuser(src),
                   shrinkuser(dest),
                   text=state.capitalize(),
                   **style.stow_states[state])

    style.print(stats, 'check', bold=True)
