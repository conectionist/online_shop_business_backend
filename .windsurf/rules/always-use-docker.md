---
trigger: always_on
---

The project uses docker.
For this reason, no dependencies will be installed on the user's machine unless absolutely necessary.
Any dependencies will be added in the appropriate places (e.g. requirements.txt).
Also, python tests will not be run manually. Instead they will be run via docker (there are also some scripts that facilitate this).
In short, whenever it's possible to use docker, use docker! Not something else.