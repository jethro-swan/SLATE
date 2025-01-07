2025-01-06

###### The next few screens to be added ...

- Complete screen for CSV import (for bulk creation of **namespaces**,
  **currencies**, **login identities**, **accounts** and **payments**, for
  sandbox payments sets).

- Add **agent** to **agent** messaging (including _steward_ to **agent**
  messaging) via _messages_ database (using serialized list of dictionaries)
  suitable for direct display in "home.html" template.

- Add/complete screen for **identity**-to-**identity** payment.

- Add/complete **agent** self-management screens/endpoints/code.

- Add/complete **identities** screen.

- Add/complete invitation QR code generation screen/code.

- Add _steward_-to-**identity** messaging (via "home" page) - e.g. suspension.

- Add **identity**-to-_steward_ messaging - e.g. suspicious activity alert.

- Add/complete _entity_ management screens.

- Add/complete _stewardships_ listing/management screen.

- Add/complete CSV import screen for bulk entity creation (sandbox use).

###### .. which require also ...

- Make _private_ **namespace** extensible.

- Permit inclusion of _open_ **namespace** below _private_ **namespace** tree.

###### ... then ...

- Update tables and other elements for HTML5 consistency.

- Find a simple, mobile-first, responsive template.

- Separate endpoint code into multiple files (as blueprints).

###### ... and later ...

- Merge _primids_ and _secids_ table into single _agents_ table.

- Add _social_roles_ table to gather detailed information for mapping local
  economic activity.

- Add in the parabola plot (adapted from _LETSplay_).

- Complete CLI for SSH use.

- Add in ABS functions.

- Add REST API.

- Add hub replication.

- Add minimalist Python API and plug-in directory.

- Add simulation library support (for increasingly rich patterns).

- Add **namespace** tree visualization tool.

- Add window pop-up support for more detailed display in larger screens.

- Add provision to use _PostgreSQL_ in place of _SQLite_ for large data sets.

###### ... after which ...

- Apply what has been learnt here to a re-design/-implementation of _NESTS_.

- Maximize reusability of _SLATE_ components in _NESTS_.
