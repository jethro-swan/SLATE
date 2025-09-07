2025-09-06

##### higher priority

- Simplify the user menu by separating

        app/templates/base.html

  into mode-specific menu templates such as

        app/templates/slate_base.html
        app/templates/slate_extended_base.html
        app/templates/nests_base.html

- Since the _parent_ of an **ahid** may be any **namespace** (where authorized),
  there is no longer a need for **secids** to provide an aliased presence.
  Therefore
  - all functions relating to **secids** can be removed,
  - **ahid** can replace **secid** in the dependency diagram and throughout the
    NESTS/SLATE descriptions,
  - modes (including _omtrad_) can be abandoned, and
  - the  app/templates/base.html  menu can be greatly simplified.

  This will allow ...

  - Creation of a new page/endpoint to list the _added identifier_ HRNS of any
    **account** created during a **currency**|**ahid** pairing (ignoring the
    HRNS created automatically) as links from which **account**-to-**account**
    payments can be made..

  - Optional display of the FPH of _all_ **account**s as links from which an
    **account**-to-**account** payment can be made.

- Fragment the entities database by assigning a distinct SQLite file for each
  _private_ **namespace** (using the root FPH as its filename).

  This should greatly increase the speed of CSV dataset imports while
  simplifying pruning/grafting of **namespace** sub-trees.

  To facilitate this, a new MDB map will be added:

  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  entity FPH &rarr; private **namespace** root FPH

  - When a new **namespace** is registered to an _identifier_, it inherits its
    PNSR (private **namespace** root) from its parent **namespace**.
  - When a new **primid** is registered to an _identifier_, a **namespace** is
    registered to the same _identifier_ and its own FPH is added as its
    FPH>PNSR map entry.
  i.e. The FPH of the root of each private **namespace** tree is the same as
  that of the **primid** to which it belongs. This minimizes the changes
  necessary.

  In due course, the  identify_entity( )  function can then be modified
  to provide this as an output:

  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  entity_fph, entity_hrns, etypes, private_namespace_fph,
  m = identify_entity(entity_id)

  For the time being, the  get_private_namespace_root( )  function will suffice
  (and may in fact be both more efficient and more convenient).

  The  private_namespace_fph  value (an empty string if in the public
  **namespace**) can then be passed to any function access the SQLite databases
  - entities.db  or  entities_c0076b4af07e8128789185a116d63ce6.db
  - payments.db  or  payments_c0076b4af07e8128789185a116d63ce6.db


- Create secondary screens to declutter the "newbie-friendly" interfaces, e.g.
  - Extending beyond the pairing-based **account** indexing to allow direct
    identification of an **account** as well more direct and sophisticated
    payment approaches.  

- Add to payment received notification to include
  - option to confirm/acknowledge receipt (check box?)
  - option to reverse/refund payment received (reversal transaction)

- Restore and extend simple **agent**-to-**agent** (one-to-one) and
  **agent**-to-**agents** (one-to-several) messaging.

- Begin extension to include NESTS capabilities such as

  - Vector **currency** support

  - Time-series analysis and algedonic signalling

##### lower priority

- Add/complete **agent** self-management screens/endpoints/code.

- Add/complete **identities** screen.

- Add _steward_-to-**identity** messaging (via "home" page) - e.g. suspension.

- Add **identity**-to-_steward_ messaging - e.g. suspicious activity alert.

- Add/complete _entity_ management screens.

- Add/complete _stewardships_ listing/management screen.

- Permit inclusion of _open_ **namespace** below _private_ **namespace** tree.

##### eventually

- Separate endpoint code into multiple files (as blueprints).

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

##### ... after which ...

- Apply what has been learnt here to a re-design/-implementation of _NESTS_.

- Maximize reusability of _SLATE_ components in _NESTS_.
