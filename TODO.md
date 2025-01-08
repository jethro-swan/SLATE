2025-01-06

###### The next few screens to be added ...

- **high priority**:
  Add in payment received notification for _payee_ **agent**'s (possibly below
  top menu). Include
  - option to confirm/acknowledge receipt (check box?)
  - option to reverse/refund payment received (reversal transaction)

- Correct _seed_ **currency**'s default **account** name from "local" to
  "hours".

- **high priority**:
  Add automatic **account** (creation in specified **currency**) for creation
  of new **aliases** and then

- **high priority**:
  Simplify screen (including "home") to remove references to **accounts**,
  shifting the _payment_ link (in this "basic" mode) from **account** to
  **identity**+**currency**.

- **high priority**:
  Add/complete screen for **identity**-to-**identity** payment.

- **high priority**:
  Complete screen for CSV import (for bulk creation of **namespaces**,
  **currencies**, **login identities**, **accounts** and **payments**, for
  sandbox payments sets).

- Add simple **agent**-to-**agent** (one-to-one) and  **agent**-to-**agents**
  (one-to-several) messaging (including, respectively, _steward_-to-**agent**
  and _steward_-to-**agents** messaging) via a _messages_ database.

- Correct **account** journal download to change the other **account**'s
_identifier_ from FPH to HRNS.

###### ... and then ...

- Add/complete **agent** self-management screens/endpoints/code.

- Add/complete **identities** screen.

- Add/complete invitation QR code generation screen/code.

- Add _steward_-to-**identity** messaging (via "home" page) - e.g. suspension.

- Add **identity**-to-_steward_ messaging - e.g. suspicious activity alert.

- Add/complete _entity_ management screens.

- Add/complete _stewardships_ listing/management screen.

- Add/complete CSV import screen for bulk entity creation (sandbox use).

###### ... which require also ...

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
