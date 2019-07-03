from socket import gethostname
import json


options = {
    'dry_run': 'Forces dry-run (no change) mode',
    'overwrite': ('Overwrite conflicting files in destination '
                  '(Warning: Can cause data loss!)'),
    'verbose': 'Behold! Every change is going to be listed!',
    'group_output': 'Display output in order or group by status'
}


class Config():
    def __init__(self, conf='config.json'):
        try:
            with open(conf, 'r') as c:
                self.config = json.load(c)
        except FileNotFoundError:
            raise Warning('File "{}" not found.'.format(conf))
        except json.decoder.JSONDecodeError as e:
            raise Warning('Incorrectly formatted config file ({})'.format(e))

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
                'Section matching machine\'s hostname "{}" wasn\'t found.'.
                format(section))

        # Some tweaks to the containers section
        try:
            for ctnr, items in host['containers'].items():
                # Copy source from general section
                try:
                    # Try to copy over container options from general section
                    general_ctnr = self.config['general']['containers'][ctnr]
                    host['containers'][ctnr] = dict_update(general_ctnr, items)
                except AttributeError as e:  # Raises if not a dict
                    if 'source' not in items:
                        # Fallback to source option
                        host['containers'][ctnr]['source'] = general_ctnr
                except KeyError:
                    raise Warning(
                        'Container "{}" doesn\'t appear in "general".'.format(
                            ctnr))
                except TypeError:
                    raise Warning('Improperly formatted general "Containers".')

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

                    for pkg, (rule, files) in rules.items():
                        try:
                            if not is_pkg:
                                host['containers'][ctnr]['rules'][pkg][1] = (
                                    files.split())
                            else:
                                host['containers'][ctnr]['rules'][1] = (
                                    files.split())
                        except AttributeError:
                            # Already a list
                            pass
                except TypeError:
                    raise Warning(
                        'Improperly formatted rule "{}" in "{}" container.'.
                        format(pkg, ctnr))
                except (AttributeError, KeyError, ValueError):
                    err = 'Improperly formatted rules for "{}"'.format(ctnr)
                    if is_pkg:
                        err += ' (maybe because "pkg" is True?)'
                    raise Warning(err)
        except AttributeError:
            raise Warning(
                'Improperly formatted "containers" value in "{}".'.format(
                    section))
        except KeyError:
            raise Warning('No "containers" key in "{}".'.format(section))

        return host
