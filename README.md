## SLATE (Simple Ledger Application: a Temporary Expedient)

This is an extremely simple _Flask_ application to support nested
[open money](https://openmoney.github.io/specification) payment networks, each
able to support multiple currencies.

This is a temporary system to allow networks/islands to form while
[NESTS](https://nests.lrc.org.uk) is still being developed (its specification
being still somewhat fluid at this stage). For this reason, the names used to
identify _entities_ (agents and currencies) in _SLATE_ are compatible [^1] with
those of the fully-nested (and much more capable) _NESTS_ software.

----
### Entity categories

There are five categories of _entity_:
  - **namespaces** (a.k.a. _network_ or _island_) in which _names_ of all
    _entities_ (including other **namespaces**) are contained.
  - **primary identities** (**primds** - which anchor an _agent_ both
    within a **namespace** and to the real world).
  - **secondary identities** (**secids** - aliases of **primids** - which
    can anchor that same _agent_  within any number of **namespace**s).
  - **currencies** (limited to scalar values of type _money_, in contrast
    to those supported by _NESTS_) - a set of **accounts**.
  - **accounts** (_variables_) each of which is a member of one **currency**
    (set).

### Agent categories

There are four categories of _agent_:
  - A general _agent_ - the set to which _all_ **primids** and **secids**
    belong.
  - A **namespace**'s _steward_, a **primid** assigned this role either by
    another **primid** already holding it or by a _global system administrator_.
  - A **currency**'s _steward_, a **primid** assigned this role either by
    another **primid** already holding it or by a _global system administrator_.
  - A _global system administrator_, assigned this role at setup or by an
    existing _global system administrator_.

----
### Internal representation

For convenience, each _entity_ (**namespace**, **primid**, **secid**, **currency**
or **account**) is identified internally by a unique number (_FPH_) serving as the
primary key in an _SQLite_ table. (NB, these numbers are _not_ fully compatible
with the _FPH_ (_Full Path Hash_) used in _NESTS_.

These global mappings are:
  - **namespace**: _namespace_hrns_ &rarr; _namespace_fph_
  - **namespace**: _namespace_fph_ &rarr; _namespace_hrns_
  - **currency**: _currency_hrns_ &rarr; _currency_fph_
  - **currency**: _currency_fph_ &rarr; _currency_hrns_
  - **primid**: _primid_hrns_ &rarr; _primid_fph_
  - **agent**: _primid_fph_ &rarr; _primid_hrns_
  - **agent**: _secid_hrns_ &rarr; _secid_fph_
  - **agent**: _secid_fph_ &rarr; _secid_hrns_
  - **account**: _account_hrns_ &rarr; _account_fph_
  - **account**: _account_fph_ &rarr; _account_hrns_

As in _NESTS_, each entity (**namespace**, **currency**, **primid**, **secid**
or **account**) is identified by a human-readable name string (HRNS) placing it
within a **namespace**.

Each **namespace** contains the names of **namespaces**, **currencies**, 
**primds** and **secids** and, as in _NESTS_, the names of **accounts** may 
be contained within any **namespace** (subject to authorization by its
_stewards_. This provides a sufficient entry point into a network fully 
compatible with [open money](https://openmoney.github.io/specification) 
(although notably lacking provision for the construction of the rich 
governance system that _NESTS_ is intended to support).

The compatibility of the _entity_ names is sufficient to enable convenient and
complete migration from _SLATE_ to _NESTS_ in due course.

-----
### Ledger files

#### Currency journal

Each **currency** has an associated journal in which all _payments_ are
recorded, listing
  - the _payer_ **account**
  - the _payee_ **account**
  - the _amount_
  - an (optional) annotation (if specified by the _payer_)

The **currency**'s journal can be exported at any time (either as a CSV files
or as a pretty-printed table) by one of its _stewards_ or by a **global system
administrator**.

#### Agents' ledgers

Each **account** has an associated journal in which all _payments_ and
_receipts_ are recorded.

Each **agent** (_agent_) has access to at least one **account** (generally
more), and a separate ledger for each of these. The **account**s' ledgers list
all transaction (_payments_ and _receipts_). These ledgers each comprise fields
listing
  - the name of the other **account** (whether a _payer_ or a _payee_)
  - the _amount_ paid or received (+ or -)
  - the _balance_ following this payment
  - an _annotation_ (if specified by the _payer_)

For each payment made
  - the _payer's_ balance in this **currency** is reduced by _amount_
  - the _payee's_ balance  in this **currency** is increased by _amount_
  - the payment is recorded in the this **currency**'s _journal_

Each **agent** (_agent_) can export its own **accounts**' ledgers, each
**account** being in a distinct **currency**.

----
## The agent interface

The _SLATE_ screens form a subset those used in _NESTS_, with minimal, if any,
modification.

### Agent screens

  - **Registration**  
    Once registered, the **agent** has access to (an **account** in) every
    **currency** within that **namespace** to which the _stewards_ of both
    have authorized access (a matter of policy).
    - **namespace** (selected from a drop-down list)
    - **agent** name (entered in a text box)
    - real name (entered in a text box) (optional)
    - _email address_(es) (entered in a text box)
    - password (entered in a text box)
    - PIN (entered in a text box)
  - **Login recovery**
    A recovery link is sent by email.[^2]
    - _email address_ or **agent name** (entered in a text box)
  - **Payment**
    Each _payment_ is recorded in the **currency**'s journal
    and in the ledgers of both _payer_ and _payee_.
    - _payee_ identifier
    - _amount_
    - parallel amount paid in national currency (optional)
    - **currency** (selected from drop-down list)
    - _annotation_ (optional)
  - **home screen**
    This is the screen displayed upon logging in, displaying
    - _balance_ in each **currency**
    - links to
      - transaction history in each **currency**
      - export link for the _ledger_ in each **currency**
      - a link to the _parabola plots_ for each **currency**
      - a **primid**/**secid** update screen
  - **primid update** screen allowing changes to
    - **agent name** (entered in a text box)
    - real name (entered in a text box) (optional)
    - _email address_ (entered in a text box)
    - password (entered in a text box)
    - PIN (entered in a text box)

This screen can be reached either when already logged in or via a _password
reset_ received by email.

### Namespace stewards

When logged in, any **agent** registered as a _steward_ of a **namespace** will
see the following additional links in its _home screen_:
  - _add steward_
  - _add new **currency**_
  - _confirm pending registration_
  - _suspend **primid**_
  - _re-enable **primid**_
  - _suspend **secid**_
  - _re-enable **secid**_

Therefore the following additional screens are required:
  - **Add steward** for this **namespace**
    - _steward_ **name**
  - **Add currency** for this **namespace**
    - **currency**'s **name** (entered in a text box)
    - **currency** prefix (entered in a text box) (optional)
    - **currency** suffix (entered in a text box) (optional)
    - initial _steward_ **name** (entered in a text box)
  - **Suspend primid**
    - **primid** name (entered in a text box)
  - **Re-enable secid**
    - **agent** name (selected from drop-down list)
  - **Re-enable secid**
    - **agent** name (selected from drop-down list)

### Currency stewards

When logged in, any **agent** registered as a _steward_ of a **currency** will
see the following additional links in its _home screen_:
  - _add steward_
  - _add new **currency**_
  - _confirm pending registration_
  - _suspend **primd** or **secid**_
  - _re-enable **primd** or **secid**_
  - _export journal_ (the record of payments)
  - _post a reversing transaction_

Therefore the following additional screens are required:
  - **Add steward** for this **currency**
    - _steward_ **name**
  - **Suspend primid**
    - **primid** name (entered in a text box)
  - **Re-enable primid**
    - **primid** name (selected from drop-down list)
  - **Suspend secid**
    - **secid** name (entered in a text box)
  - **Re-enable secid**
    - **secid** name (selected from drop-down list)
  - **Export journal**
    - **currency** name (selected from drop-down list)
  - **Post reversing transaction**[^3]
    - **currency**'s **name** (selected from drop-down list)
    - _transaction_ (selected from drop-down list displaying most recent
      transactions in this **currency**).

### Global administrators

When logged in, any **primid** registered as a _global administrator_ will see
the following additional links in its **home screen**:
  - _add new **namespace**_
  - _add global administrator_
  - _confirm pending registration_
  - _suspend **primid**/**secid**_
  - _re-enable **primid**/**secid**_
  - _export journal_ (for any **currency**)

Therefore the following additional screens are required:
  - **Add new namespace**
    - **namespace** name (entered in a text box)
  - **Add global administrator**
    - **primid** name (entered in a text box)
  - **Suspend primid**[^4]
    - **primid** name (entered in a text box)
  - **Re-enable primid**
    - **primid** name (selected from drop-down list of disabled **primids**s)
  - **Suspend secid**[^5]
    - **secid** name (entered in a text box)
  - **Re-enable secid**
    - **secid** name (selected from drop-down list of disabled **secdis**s)
  - **Export journal**
    - **currency** name (selected from drop-down list)
    - File download location (file dialogue)


----

[^1]: _SLATE_ names are limited to UTF-8 Latin characters using only "." as the
namespace delimiter whereas _NESTS_ names and the namespace delimiter may be
any UTF-8 character.

[^2]: The password is not stored. Instead, a crypotographic hash of the password
is stored against which the access-recovery password entered can be authenticated.

[^3]: NB, this does not remove the original transaction from the journal.
Instead, it posts a reversing transaction.

[^4]: When a **primid** is suspended, all of its **secids** are also suspended.

[^5]: When a **secid** is suspended, its **secids** are will not necessarily also
be suspended (although that may happen where the _stewards_ of the **namespaces**
have configured such a policy).



----

Most recently updated: 2024/11/05
