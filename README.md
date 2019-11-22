<img align="left" width="90" height="90" src="https://repository-images.githubusercontent.com/191015829/b8897f80-aa82-11e9-8272-9586c23b4f7f">

# Link The Dots

A simple utility for Linux that allows easy management of [dotfiles](https://en.wikipedia.org/wiki/Hidden_file_and_hidden_directory) (aka dots) deployment, usually on more than one system, while maintaining the same set of directories and files ("packages") for all of them.\
Link The Dots "packages" use similar structure to the so-called [GNU Stow](https://www.gnu.org/software/stow/) software packages, which makes it extremely easy for users to migrate from using this tool.\
The tool strives to be as portable as possible, requiring only Python standard library as a dependency, and is intended to live as part of the dotfiles either as a cloned repository or as a submodule.

![link-the-dots-demo](https://my-take-on.tk/img/repo-assets/link-the-dots/link-the-dots-demo.apng)

# Table of contents

- [Features (Or: What Link The Dots will do for you)](#features-or-what-link-the-dots-will-do-for-you)
- [Non-Features (Or: What Link The Dots won't do for you)](#non-features-or-what-link-the-dots-wont-do-for-you)
- [Dependencies](#dependencies)
- [Quick start (TL;DR version)](#quick-start-tldr-version)
    - [Requirements](#requirements)
    - [Create a config file](#create-a-config-file)
- [How it works](#how-it-works)
    - [Terminology](#terminology)
    - [Overview](#overview)
    - [The Config File](#the-config-file)
    - [Hints](#hints)
    - [Command Line Options](#command-line-options)
- [Typical Setup](#typical-setup)
- [Tips and Tricks](#tips-and-tricks)
- [Advanced Example](#advanced-example)
- [FAQ](#faq)

## Features (Or: What Link The Dots will do for you)

- Manage any directory containing GNU Stow software packages (=a [container](#terminology)) and deploy its content by using symlinks.
- Manage multiple machines in a single config file.
- Per-machine and per-[package](#terminology) include/exclude rules.
- Designate two similar directories or files to different machines (good for keeping different versions of the same file/directory for each machine).


## Non-Features (Or: What Link The Dots won't do for you)

- No version control/sync feature.
- No support for fancy template processing (Ninja2, etc).


## Dependencies

- Python 3.6+
- A functioning brain ;)


## Quick start (TL;DR version)

### Requirements

1. A directory with (dot)files organized in GNU Stow software packages.
2. The `git` tool.

### Create a config file

1. Clone this repository.
2. Create [`config.json`](#the-config-file) inside the cloned directory with the desired options.
3. Run `./main.py` or `python3 link-the-dots` (if you're one level above) to deploy\*.
4. All packages should now be symlinked to their respective locations.

See `main.py --help` for more options.

\* It's recommended to first run with the `--dry-run` flag to make sure everything works as intended.


## How it works

### Terminology

- **Package** - A directory identical to GNU Stow software package, containing exactly the same directory tree of the destination.
        For instance: `package/.config/package/file`
- **Container** - A directory that *contains* multiple packages.
- **Section** - The key in the config file that contains the options of an individual machine.
- **Stow** - The process of linking the destination directory to the source.
- **Restow** - Replacing an already existing link (regardless of where it points to).
- **Hint** - A suffix to any file/directory name that *hints* its intended host. (ex: `config.json#mycomputer` will hint that this file is intended only for the host `mycomputer`)

### Overview

Link The Dots will run in the following order:

1. Attempt to read the JSON config file at `config.json` in the current directory, or a different file that was given via the `--config` [argument](#command-line-options).
2. Look for a section corresponding to that of the machine's hostname\* (see [`name`](#name) option for more information).
3. For each container in the matching section:
    1. Make sure the container is declared at the "general" section and overwrites its keys with the current container's (the current machine's section gets priority).
    2. Link all the packages from "source" to "destination", based on the [particular settings](#the-config-file) for that container.\
        **Note:** Directories are *created* and not linked. Therefore, if there's a change in the contents of the source (a new file was created, file name was changed, etc...) then the package must be restowed.

\* Hostname is obtainable via `cat /etc/hostname` or simply `hostname` command on most Linux distributions.


### The Config File

The config file is written in JSON and must contain *at least* two [sections](#terminology): `general` and `hostname`, where `hostname` refers to the machine it's intended for.

Let's start with a basic example:

```json
{
    "general": {
        "containers": {
            "dotfiles": {
                "source": "/path/to/src"
            }
        }
    },
    "mycomputer": {
        "containers":{
            "dotfiles": {
                "source": "/path/to/dest"
            }
        }
    }
}
```

In the above example we consider a machine with the hostname "mycomputer", and therefore the config file has one *section* called "mycomputer" with one *container* called "dotfiles".\
All packages in `/path/to/src` will be symlinked to `/path/to/dest`. Very simple and straightforward.

This is actually the equivalent of using `stow --target=/path/to/target -R package` for any package in `/path/to/src`.


#### Configuring options

A list of all the possible options:

| Option               | Type              | Affiliation           | Mandatory |
|:---------------------|:------------------|:----------------------|:---------:|
| `name`               | string            | Host section **only** |           |
| `verbose`            | boolean           | General/Host sections |           |
| `overwrite`          | boolean           | General/Host sections |           |
| `dry-run`            | boolean           | General/Host sections |           |
| `group_output`       | boolean           | General/Host sections |           |
| `containers`         | dictionary        | General/Host sections | ✔         |
| Container            | dictionary/string | `containers`          | ✔         |
| `source`             | string            | Container             | ✔         |
| `destination`        | string            | Container             | ✔         |
| `packages`           | string/list       | Container             |           |
| `destination_create` | boolean           | Container             |           |
| `pkg`                | boolean           | Container             |           |
| `rules`              | dictionary/list   | Container             |           |

##### `name`

Gives more control over the name of the machine and section. Especially useful when the hostname is very long and we want to have shorter hints.

Assume that the machine hostname is `mycomputer`:

| Section Key     | Name Value          | File Name Hint           |
|:----------------|:--------------------|:-------------------------|
| mycomputer      | -                   | mycomputer               |
| mycomputer      | mycomputeristhebest | mycomputeristhebest      |
| thebestcomputer | mycomputer          | mycomputer               |
| my-computer     | my-name             | error: section not found |

In order to identify the machine, either the section or the `name` value must be equal to the machine's hostname.\
The hint is affected only from the `name` value, however if it's not set then it falls back to the section key.

**Note:** Both section name and `name` are CaSe InSeNsItIvE.

Best practice would be:
- section key = machine hostname
- `name` value = custom name


##### `verbose`, `overwrite`, `dry-run` and `group_output`

Those are the same as the [command-line arguments](#command-line-options), just permanent.

Acceptable values: `true`/`false` (case sensitive)


##### `containers`

A dictionary with the various containers.


##### Container

The key name is a custom name for the desired container.
When the value is a string, it's interpreted as `destination`.
If other settings are required, the container can also be a dictionary, and they can be set inside it.


##### `source` and `destination`

The source and the destination paths for the container. Without those, nothing starts.


##### `packages`

By default, all packages are deployed. However, using this key makes it possible to set a list of packages from this container to deploy.

It can be either a list of strings:

```json
"packages": ["pkg1", "pkg1"]
```

Or a space-separated string:

```json
"packages": "pkg1 pkg2"
```

**Note:** If for some reason there's a package with a space in its name, only the first method can be used.


##### `destination_create`

On certain containers, when deploying on a new machine, the destination directory may not exist at all. By default, this kind of scenario will result in an error, however it can be overcome by using this option.
Please note that setting this option will recursively create the full destination path, just like using `mkdir -p`.


##### `pkg`

In some cases, there's a package that doesn't quite fit in any container, or it needs a different destination, like scripts that must be deployed to `$PATH`.

`pkg` option will make the container behave like a single package.

**Note:** If this `pkg` is set to `true`, [`packages`](#packages) will have no effect.


##### `rules`

This is a package-based include/exclude filtering that maximizes the control over the specific files that will be deployed.

The easiest way to explain how it works is by using an example.

Consider the following container tree:

```bash
container
├── package-a
│   └── .config
│       └── package-a
│           ├── config
│           ├── important-a
│           └── important-b
└── package-b
    └── .directory
        ├── config
        └── no-need
            ├── extra
            └── main
```

With the following `rules`:
```json
"rules": {
    "package a": ["include", ["important-a", "important-b"]],
    "package b": ["exclude", "no-need"]
}
```

- For `package-a`: the files `important-a` and `important-b` will be stowed, but not `config`.
- For `package-b`: everything besides `no-need` will be stowed. Since `no-need` is a directory, all files within it will be skipped as well.

###### Some notes
- For each package, either "include" or "exclude" rule can be applied, not both.
- `rules` files (second list item) are **case sensitive**.
- `rules` files (second list item) can be either a list or a space-separated string. Therefore, `["include", ["a", "b"]]` is equivalent to `["include", "a b"]`.
- Rules can match substrings as well. The above example of `package-a` could be simplified to `["include", "important"]` which will match both `important-a` and `important-b`.
- If `pkg` option is used, `rules` value should be a list: `"rules": ["include/exclude", "packages"]`. Otherwise, a config error will be raised.


### Hints

Hints are like an extension to `rules` where `rules` cannot be applied.

Consider a situation where there's a config file for two different machines - both files must be named `config`, however it's impossible to include/exclude them via `rules`. Enter hints!

With hints, it's possible to designate a specific file to a specific machine by appending a small hint to its name.

Say we have two machines: `comp1` and `comp2`. The file `config` in the above example can be named `config#comp1` and `config#comp2` to hint its intended machine. The files will then be stowed to `destination` **without** the hint so each machine will actually see a symlink called `config`. Problem solved!

#### Some notes

- The hint *must* come at the end of file name, even on files with en extension. For example: `config.json#comp1`.
- It's possible to target multiple machines for the same file, just use multiple hints like so: `config.json#comp1#comp3`.
- Hints value can be customized. See [`name`](#name) option in config file.


### Command Line Options

```
usage: main.py [-h] [-c CONFIG] [-d] [-o] [-v] [-g]

Link your dot(file)s.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the config file
  -d, --dry-run         Forces dry-run (no change) mode
  -o, --overwrite       Overwrite conflicting files in destination (Warning:
                        Can cause data loss!)
  -v, --verbose         Behold! Every change is going to be listed!
  -g, --group-output    Display output in order or group by status
```

#### A warning

- If no options specified, program will go ahead and execute, permanently changing the destination directory. It's advised to first use and inspect the output of `--dry-run` option.
- Symlinks that exist on the destination will be rewritten regardless of the `--overwrite` option. However, actual files will be be skipped unless `--overwrite` argument is used.


## Typical Setup

Soon!


## Tips and Tricks

Soon!


## Advanced example

```json
{
    "general": {
        "group_output": true,
        "verbose": true,
        "containers": {
            "dotfiles": {
                "source": "~/mydotfiles",
                "rules": {
                    "applications": ["exclude", "/scripts bspwm"]
                }
            }
        }
    },
    "mysuperawesomeretrocomputer": {
        "name": "ibm5100",
        "containers": {
            "dotfiles": {
                "destination": "~/test/dest",
                "destination_create": true,
                "packages": "bspwm compton dunst nvim",
                "rules": {
                    "applications": ["include", "bspwm"]
                }
            }
        }
    }
}
```

Starting from top to bottom:
- Set to always group output, so all stowed files will appear together, all restowed files will appear together, and so on...
- Set to always show verbose output.
- Create one container called "dotfiles".
    - Set source directory to `~/mydotfiles/`.
    - Set a rule to "applications" package (effectively `~/mydotfiles/applications/`) that will exclude the directory "scripts" and any file with "bspwm" in its name (effectively `~/mydotfiles/applications/scripts/` and any other directory or file that contains "bspwm" in `~/mydotfiles/applications/`)
- Create a setting for a machine with hostname "mysuperawesomeretrocomputer".
- Name it "ibm5100" so [hints](#hints) will be that and not that aweful hostname.
- Create one container called "dotfiles".
    - Set destination directory to `~/test/dest/`.
    - Make sure to create the destination if it doesn't exist (will also create `~/test` if needed).
    - Choose only certain packages from the container. For instance, `~/mydotfiles/git` will be completely ignored.
    - Overwrite the general rule for "applications" package to only **include** directories and files that contain "bspwm" in their names.


## FAQ

### Why bother creating yet another dotfiles manager?

When I was on a hunt for a dotfiles manager after my setup was too complicated for GNU Stow to handle, I tried all the managers I could find, but none of them was simple enough nor provided the elegance and control I was looking for. Dependencies was also something I considered an issue, since I believe that less dependencies are equal to less headache as a user as well.

While Link The Dots is not completely adherent to the [Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy), it simply does one thing, and strives to do it well, and leaving all the [other stuff](#non-features-or-what-link-the-dots-wont-do-for-you) to other tools to handle.

In other words, it tries to solve a simple problem by not creating a bunch of other ones in the process.

### GNU Stow is enough. Change my mind.

Think GNU Stow with the ability to always stow the same packages without the need to remember which package belong to which machine.\
Think GNU Stow that allows you to stow [only part of a package](#rules).\
Think GNU Stow that supports [assigning the same file name](#hints) to be stowed on different machines.\
Convinced yet?

### I'm afraid that this tool will mess up my dotfiles.

At this point, the project is indeed considered beta.\
It was tested on all of my machines, on different Linux distributions and I made sure to iron out all the bugs that I could find.\
I also made sure to write a test suite that'd simulate all kinds of scenarios, to make sure nothing gets destroyed.

However, being one person with one set of mind has its limits so if you find this project interesting but afraid to try it, I encourage you to try it with the `--dry-run` option first, or even in a "controlled" environment where `source` contains dummy packages and `destination` is an empty directory.

### JSON is LAME! I only use YAML!

I definitely agree that YAML is more readable and easier to maintain, however one of the main goals in building Link The Dots was having no extra dependencies other than Python itself. On Linux, Python 3's Standard Library ships with JSON support but not YAML, and therefore I opted to using JSON.

That being said, if there was enough demand, I wouldn't mind add YAML support as well as an optional dependency.

### I use pip and PyPi! Why can't I install this tool on my system?

The main goal for me in developing this tool was making it an integral part of my dotfiles, and not a separated tool. The idea is having this repository being added as a submodule in the main dotfiles repository, so they always stay together.

Different opinions and use cases may also exist, so I'm open to changing my opinion and making this tool installable if there's enough demand.

### All this sounds nice and all but how do I sync my dotfiles between all of my machines?

That is a job for another tool and is entirely up to you!\
You can host your dotfiles in a git repository and add this module as a submodule, or you can use a tool like [Syncthing](https://syncthing.net), or an online "cloud" service like Dropbox, Mega.co.nz or Google Drive. You can even use a thumb drive to backup your dotfiles if you really wanted to!


