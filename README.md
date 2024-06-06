## SLATE (Simple Ledger Application for Temporary Expediency)

This is an extremely simple _Flask_ application to support un-nested
[open money](https://openmoney.github.io/specification) payment networks, each
able to support multiple currencies.

This is a temporary system to allow networks/islands to form while
[NESTS](https://nests.lrc.org.uk) is still being developed (its specification
being still somewhat fluid at this stage). For this reason, the names used to
identify _entities_ (users and currencies) in the un-nested _SLATE_ are
compatible with those of the fully-nested (and much more capable) _NESTS_
software.

----
#### User categories

There are three categories of user:

  - A **general user** - a set to which _all_ **users** belong.
  - A **currency steward** - a _steward_ of a **currency**, assigned this role
    either by another _steward_ of a **currency** or by a **global system
    administrator**.
  - A **global system administrator**, assigned this role at setup or by
    an existing **global system administrator**.

----
#### Internal representation

For convenience, each _entity_ (**user**, **currency** or **community**) is
represented internally by a unique number (assigned sequentially), mapped each
way using a pair of associative arrays (_DBM_). These numbers are _not_
compatible with the _FPH_ (_Full Path Hash_) used in _NESTS_ (although they
could be made so).

These global mappings are:
  - **user**: _name_ &rarr; _number_
  - **user**: _number_ &rarr; _name_
  - **currency**: _name_ &rarr; _number_
  - **currency**: _number_ &rarr; _name_
  - **community**: _name_ &rarr; _number_
  - **community**: _number_ &rarr; _name_

Each **community** has its own collection of **currencies** and **users**, so
this lacks the flexibility of the recursively-nested **namespaces** in _NESTS_.
However, a **user**'s or **currency**'s _name_ may be duplicated in multiple
**communities**, so a this provides a sufficient entry point into a network
fully compatible with [open money](https://openmoney.github.io/specification)
(although notably lacking provision for the construction of the rich governance
system that it is intended to support).

The compatibility of the _entity_ names is sufficient to enable convenient and
complete migration from _SLATE_ to _NESTS_ in due course.

-----
#### Ledger files

###### Currency journal

Each **currency** has an associated journal (CSV) in which all _payments_ are
recorded, listing
  - the _payer_
  - the _payee_
  - the _amount_
  - an (optional) annotation (if specified by the _payer_)

The **currency**'s journal can be exported at any time by one of its _stewards_
or by a **global system administrator**.

###### Users' ledgers

The ledgers are all stored internally as CSV, in a format convenient for direct
export.

Each **user** (_agent_) has access to at least one **currency** (generally
more), and a separate ledger for each of these. The **user**'s ledgers list the
transaction (_payments_ and _receipts_) for its accounts. These ledgers each
comprise fields listing
  - the name of the other **user** (whether a _payer_ or a _payee_)
  - the _amount_ paid or received (+ or -)
  - the _balance_ following this payment
  - an _annotation_ (if specified by the _payer_)
and the _ledger_ file is identified by **currency** and **user**.

For each payment made
  - the _payer's_ balance in this **currency** is reduced by _amount_
  - the _payee's_ balance  in this **currency** is increased by _amount_
  - the payment is recorded in the this **currency**'s _journal_

Each **user** (_agent_) can export its own ledger in any **currency** to which
it has access.

----
### The user interface

#### User screens

  - **Registration**  
    Once registered, the **user** has access to (an **account** in) every **currency** within that **community**.
    - **community** (selected from a drop-down list)
    - **user name** (entered in a text box)
    - real name (entered in a text box) (optional)
    - _email address_ (entered in a text box)
    - password (entered in a text box)
    - PIN (entered in a text box) 

  - **Login recovery**
    - _email address_ or **user name** (entered in a text box)

A recovery link is sent by email.

  - **Payment**
    - _payee_ identifier
    - _amount_
    - parallel amount paid in national currency (optional)
    - **currency** (selected from drop-down list)
    - _annotation_ (optional)

Each _payment_ is recorded in the **currency**'s journal and in the ledgers of
both _payer_ and _payee_.

  - **home screen** displaying
    - _balance_ in each **currency**
    - links to
      - transaction history in each **currency**
      - export link for the _ledger_ in each **currency**
      - a link to the _parabola plots_ for each **currency**
      - a **user update** screen

This is the screen displayed upon logging in.

  - **User update** screen allowing changes to
    - **user name** (entered in a text box)
    - real name (entered in a text box) (optional)
    - _email address_ (entered in a text box)
    - password (entered in a text box)
    - PIN (entered in a text box)

This screen can be reached either when already logged in or via a _password
reset_ received by email.

#### Community stewards

When logged in, any **user** registered as a _steward_ of a **community** will
see the following additional links in its **home screen**:
  - _add steward_
  - _add new currency_
  - _confirm pending registration_
  - _suspend **user**_
  - _re-enable **user**_
  - _export journal_

So the following additional screens are required:

  - **Suspend user**
    - **user** name (entered in a text box)
  - **Re-enable user**
    - **user** name (selected from drop-down list)
  - **Export journal**
    - **currency** name (selected from drop-down list)

#### Global administrators

When logged in, any **user** registered as a _global administrator_ will see
the following additional links in its **home screen**:
  - _add new community_
  - _add global administrator_
  - _confirm pending registration_
  - _suspend **user**_
  - _re-enable **user**_
  - _export journal_ (for any **currency**)

So the following additional screens are required:

  - **Add new community**
    - **community** name (entered in a text box)
  - **Add global administrator**
    - user name (entered in a text box)
  - **Suspend user**
    - user name (entered in a text box)
  - **Re-enable user**
    - user name (selected from drop-down list)
  - **Export journal**
    - **currency** name (selected from drop-down list)


----
