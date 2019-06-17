import os


class Stow():
    def __init__(self,
                 source,
                 destination,
                 name,
                 dry_run=False,
                 overwrite=False,
                 verbose=False,
                 include=[],
                 exclude=[]):
        self.src = os.path.expanduser(source)
        self.dest = os.path.expanduser(destination)
        self.hostname = name
        self.dry_run = dry_run
        self.overwrite = overwrite
        self.verbose = verbose
        self.include = include
        self.exclude = exclude
        self.states = ('stowed', 'restowed', 'replaced', 'skipped')

    def collect(self):
        def need(item):
            """
            Decide whether a certain file/folder is needed
            according to the include/exclude rules.
            """
            if not (self.include or self.exclude):
                return True

            # At any point there should be either include or exclude
            for rule in (self.include or self.exclude):
                # Some rules are relative some are only the basename
                # Hence, we have to define the target accordingly
                target = item if '/' in rule else os.path.basename(item)

                if rule in target:
                    verdict = True if self.include else False
                    break  # No need to keep searching if we have a hit
            else:
                # No rules defined - fallback to default
                verdict = False if self.include else True

            return verdict

        def check_name(path):
            """
            Checks whether path contains a name hint (indicated by '#')
            and returns a value based on its match with the current name.
            """
            base = os.path.basename(path)
            name, *hostnames = base.split('#')
            if hostnames and (self.hostname not in hostnames):
                return False, False
            return base, name

        output, replace_hints = [], []
        for root, dirs, files in os.walk(self.src, followlinks=True):
            dest_dir = os.path.join(self.dest,
                                    os.path.relpath(root, start=self.src))

            base, name = check_name(dest_dir)
            if not name:
                # Do not descend into dirs not meant for this host
                dirs[:] = []
                continue
            elif base != name:
                replace_hints.append((base, name))

            # Applying this for every child of the dir as well
            for before, after in replace_hints:
                dest_dir = dest_dir.replace(before, after, 1)

            # Find out all the files to link
            for f in files:
                # Skip files not meant for this host
                base, no_host = check_name(f)
                if not no_host:
                    continue

                src = os.path.join(root, f)
                if need(src):
                    dest = os.path.normpath(os.path.join(dest_dir, no_host))
                    output.append((src, dest))

        return output

    def create(self, files):
        # Set output
        output = {'files': files, 'results': {}}
        output['results'].update({s: [] for s in self.states})

        # Symlink all files
        for src, dest in files:
            # Use absolute path if dest dir is a symlink,
            # otherwise use a relative path
            src_path = (src if os.path.islink(os.path.dirname(dest)) else
                        os.path.relpath(src, os.path.dirname(dest)))

            flag = 'stowed'
            while True:
                try:
                    try:
                        if not self.dry_run:
                            os.symlink(src_path, dest)
                        else:
                            if os.path.isfile(dest):
                                raise FileExistsError
                    except FileExistsError:
                        if os.path.islink(dest):
                            flag = 'restowed'
                        elif self.overwrite:
                            flag = 'replaced'
                        else:
                            flag = 'skipped'
                            break

                        if not self.dry_run:
                            os.remove(dest)
                        else:
                            break
                    except FileNotFoundError:
                        # Create parent tree
                        os.makedirs(os.path.dirname(dest))
                    else:
                        break
                except PermissionError:
                    flag = 'skipped'
                    break

            output['results'][flag].append((src, dest))

        return output
