import unittest
import os

from linkthedots.config import Config


class TestConfig(unittest.TestCase):
    def setUp(self):
        from socket import gethostname
        self.fake_config = {'general': {}}
        self.hostname = gethostname().lower()

    def makeconf(self, fake_config, use_dumps=True):
        from json import dumps
        from unittest.mock import patch, mock_open

        if use_dumps:
            fake_config = dumps(fake_config)

        with patch('builtins.open', new=mock_open(read_data=fake_config)) as f:
            fake_path = 'file/path/mock'
            config = Config(conf=fake_path)
            # Check that file was opened
            f.assert_called_once_with(fake_path, 'r')

        return config

    def test_no_file(self):
        with self.assertRaises(Warning):
            Config(conf='fake_config_file.json')

    def test_empty(self):
        with self.assertRaises(Warning):
            self.makeconf(self.fake_config).read()

    def test_incorrectly_formatted(self):
        fake_config = '{ \
        "general": { \
            "containers": { \
                "fake": { \
                    "source": "/path/to/fake" \
                } \
            } \
        }'                                # Missing one closing bracket

        with self.assertRaises(Warning):
            self.makeconf(fake_config, use_dumps=False).read()

    def test_uppercase_section_name(self):
        self.fake_config[self.hostname.upper()] = {}
        with self.assertRaises(Warning):
            self.makeconf(self.fake_config).read()

    def test_no_containers_key(self):
        self.fake_config[self.hostname] = {}
        with self.assertRaises(Warning):
            self.makeconf(self.fake_config).read()

    def test_improperly_formatted_containers(self):
        # yapf: disable
        bad = [{'containers': ''},
               {'containers': []},
               {'containers': {'fake': {}}}
               ]
        # yapf: enable

        for b in bad:
            self.fake_config[self.hostname] = b
            with self.assertRaises(Warning):
                self.makeconf(self.fake_config).read()

        self.fake_config[self.hostname] = {}
        for b in bad:
            self.fake_config['general'] = b
            with self.assertRaises(Warning):
                self.makeconf(self.fake_config).read()

        self.fake_config[self.hostname] = bad[2]
        for b in bad[:2]:
            self.fake_config['general'] = b
            with self.assertRaises(Warning):
                self.makeconf(self.fake_config).read()

    def test_improperly_formatted_rules(self):
        # yapf: disable
        bad = [{'rules': ''},
               {'rules': []}
               ]
        # yapf: enable
        self.fake_config['general'] = {'containers': {'fake': ''}}
        self.fake_config[self.hostname] = {
            'containers': {
                'fake': {
                    'packages': 'fakepkg'
                }
            }
        }

        for b in bad:
            self.fake_config[self.hostname]['containers']['fake'].update(b)
            with self.assertRaises(Warning):
                self.makeconf(self.fake_config).read()

    def test_hostname(self):
        self.fake_config['general'] = {'containers': {'fake': ''}}

        # Scenario 1: (section = hostname), no name key => (name = section)
        self.fake_config[self.hostname] = {'containers': {}}
        self.assertEqual(
            self.makeconf(self.fake_config).read()['name'], self.hostname)

        # Scenario 2: (section = hostname), (name = 'fake') => (name = 'fake')
        self.fake_config[self.hostname] = {'name': 'fake', 'containers': {}}
        self.assertEqual(
            self.makeconf(self.fake_config).read()['name'], 'fake')

        # Scenario 3: (section = 'fake'), (name = hostname) => (name = hostname)
        del self.fake_config[self.hostname]  # Remove previous key
        self.fake_config['fake'] = {'name': self.hostname, 'containers': {}}
        self.assertEqual(
            self.makeconf(self.fake_config).read()['name'], self.hostname)

        # Scenario 4: (section = 'fake'), (name = 'fake') => Error
        self.fake_config['fake'] = {'name': 'fake', 'containers': {}}
        with self.assertRaises(Warning):
            self.makeconf(self.fake_config).read()

    def test_output(self):
        fake_config = {
            'general': {
                'containers': {
                    'fake': '/path/to/fake',
                    'faker': {
                        'source': '/path/to/src',
                        'destination': '/path/to/dest'
                    }
                }
            },
            self.hostname: {
                'overwrite': True,
                'dry_run': False,
                'containers': {
                    'faker': {
                        'packages': 'pkg1 pkg2',
                        'rules': {
                            'pkg1': ['include', 'file']
                        }
                    },
                    'fake': {
                        'source': '/this/is/the/source',
                        'destination_create': True
                    }
                }
            }
        }

        expected = {
            'name': self.hostname,  # Added key
            'overwrite': True,
            'dry_run': False,
            'group_output': None,  # Is added
            'containers': {
                'faker': {
                    'source': '/path/to/src',
                    'destination': '/path/to/dest',
                    'packages': ['pkg1', 'pkg2'],  # A list
                    'rules': {
                        'pkg1': ['include', ['file']]  # A list in a list
                    }
                },
                'fake': {
                    'source':
                    '/this/is/the/source',  # Overwrites general value
                    'destination_create': True
                }
            }
        }

        output = self.makeconf(fake_config).read()

        self.assertDictEqual(output, expected)
