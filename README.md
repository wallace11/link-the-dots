# Beware
- Plugin creates a new folder and THEN stows all of the files in it. If there's a change in the content of the source folder it need to be restowed.
- overwrites symlinks regardless of overwrite option
- Name key:

| Machine Hostname | Section Key     | Name Value          | File name hint           |
| --               | --              | --                  | --                       |
| computer         | computer        | -                   | computer                 |
| computer         | computer        | MyComputerIsTheBest | MyComputerIsTheBest      |
| computer         | TheBestComputer | computer            | computer                 |
| computer         | my-computer     | my-name             | Error: Section not found |

 - Best practice: Section Key = Machine Hostname, Name Value = Custom Name

