from socket import gethostname
import json


options = {
    'dry_run': 'Forces dry-run (no change) mode',
    'overwrite': ('Overwrite conflicting files in destination '
                  '(Warning: Can cause data loss!)'),
    'verbose': ('Used once (-v): Show summary of package changes. '
                'Used twice (-vv): Behold! Every change is going to be listed!'),
    'group_output': 'Display output in order or group by status'
}


class Config():
    def __init__(self, conf='config.json'):
        try:
            with open(conf, 'r') as c:
                self.config = json.load(c)
        except FileNotFoundError:
            raise Warning(f'File "{conf}" not found.')
        except json.decoder.JSONDecodeError as e:
            raise Warning(f'Incorrectly formatted config file ({e})')

    def _get_section(self, hostname=gethostname()):
        """
        Checks if hostname equals to "name" key value in any section.
        If it's not - return the hostname of the machine.
        """
        hostname = hostname.lower()
        for sect, value in self.config.items():
            sect_host = value.get('name', '').lower()
            if sect_host == hostname:
                return sect

        return hostname

    def read(self):
        def dict_update(base, extra):
            """ Copies over `extra` to `base` AND overwrites keys """
            # Check if there are any nested dicts
            if any(map(lambda x: isinstance(x, dict), base.values())):
                for k, v in extra.items():
                    try:
                        dict_update(base[k], v)
                    except (KeyError, AttributeError):
                        base[k] = v
            else:
                base.update(extra)
            return base

        # Get config section
        try:
            section = self._get_section()
            general_bool = {
                k: v for k, v in self.config['general'].items()
                if k in options.keys()}
            # Initiate host bool options on top of general
            host = dict_update(general_bool, self.config[section])
            if 'name' not in host:
                host['name'] = section
        except KeyError:
            if section in map(lambda x: x.lower(), self.config.keys()):
                raise Warning('Section names must be in lowercase.')
            raise Warning(
                f'Section matching machine\'s hostname "{section}" wasn\'t found.')

        # Some tweaks to the containers section
        try:
            for ctnr, items in host['containers'].items():
                # Copy source from general section
                try:
                    # Try to copy over container options from general section
                    general_ctnr = self.config['general']['containers'][ctnr]
                    host['containers'][ctnr] = dict_update(general_ctnr, items)
                except AttributeError:  # Raises if not a dict
                    try:
                        if 'source' not in items:
                            # Explicitly set source
                            host['containers'][ctnr]['source'] = general_ctnr
                    except TypeError:
                        # Explicitly set src/dest since both are missing
                        host['containers'][ctnr] = {
                            'source': general_ctnr or None,
                            'destination': items
                        }
                        continue  # No need to further process
                except KeyError:
                    raise Warning(
                        f'Container "{ctnr}" doesn\'t appear in "general".')
                except TypeError:
                    raise Warning('Improperly formatted general "Containers".')
                except ValueError:
                    raise Warning(
                        f'Container "{ctnr}" improperly formatted.')

                # Convert packages to a proper list
                if items.get('packages'):
                    try:
                        host['containers'][ctnr]['packages'] = items[
                            'packages'].split()
                    except AttributeError:
                        pass
                    finally:
                        host['containers'][ctnr]['packages'] = set(
                            host['containers'][ctnr]['packages'])

                # Convert rules' files (second list item) to a proper list
                try:
                    is_pkg = host['containers'][ctnr].get('pkg')
                    rules = host['containers'][ctnr].get('rules', {})

                    if rules and is_pkg:
                        rules = {ctnr: rules}
                        host['containers'][ctnr]['rules'] = rules

                    for pkg, (rule, files) in rules.items():
                        try:
                            host['containers'][ctnr]['rules'][pkg][1] = (
                                files.split())
                        except AttributeError:
                            # Already a list
                            pass
                except TypeError:
                    raise Warning(
                        f'Improperly formatted rule "{pkg}" in "{container}" container.')
                except (AttributeError, KeyError, ValueError):
                    err = f'Improperly formatted rules for "{ctnr}"'
                    if is_pkg:
                        err += ' (maybe because "pkg" is True?)'
                    raise Warning(err)
        except AttributeError:
            raise Warning(
                f'Improperly formatted "containers" value in "{section}".')
        except KeyError:
            raise Warning(f'No "containers" key in "{section}".')

        return host
