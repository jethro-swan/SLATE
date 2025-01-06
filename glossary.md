## Glossary

NB, the following applies to both SLATE and NESTS.

Over time, the use of terms has gradually drifted from the [open money
specification](https://openmoney.github.io/specification) via those introduced
in [NESTS](https://nests.lrc.org.uk), but the concepts remain the same.

The terms defined here may appear slightly inconsistent with those used in
earlier _open money_ implementations, but that is really of little importance.
What matters is that the underlying concepts do not contradict those outlined
in
[The LETSystem Design Manual](https://archive.lets.net/gmlets/design/home.html)
(although new terms have been introduced in both
[NESTS](https://nests.lrc.org.uk) and _SLATE_ in order to accommodate their
additional features and capabilities).

This has introduced occasional confusion, for which reason the following
glossary has been constructed to supersede the
[earlier glossary](https://openmoney.github.io/specification/glossary.html)
written to accompany the
[open money specification](https://openmoney.github.io/specification) (which is
long overdue for review and revision).

For our purposes, we can identify two levels of detail required from a user's
perspective.

---
### A simple perspective

This is a minimal list of terms sufficient to name the distinct elements
required to realize an _open money_ payments network.
- A **currency** (in this context) is a synonym for money ("stuff that gets you
stuff").
- An _agent_ (in this context) is a _user_ of one of more **currencies**.
- A _name_ is something that identifies something (such as an _agent_, a
  **currency** or a **namespace**) uniquely within a **namespace**.
- A **namespace** is simply a collection of _names_ (each unique within _that_
  **namespace** but able also to appear uniquely within any other **namespace**
  in which they are _authorized_). Since the _name_ of every **namespace** is
  also contained (uniquely) within another **namespace**, the **namespaces**
  form a _tree_ each unique path within which is identified by a string of
  _names_ joined by a character (a "." by established convention[^1]), e.g.
  - if a **namespace** at the _root_ of such a tree is identified by a single
    _name_ (which is not unusual), no immediate distinction need to made
    between the _name_ and the _namespace_ identifier (which may help to ease a
    new user into _open money_ world), but
  - if the _name_ of a **namespace** is located in another **namespace** (which
    is the more general case) it will take the form
    - _a.b_ (where _b_ is the _identifier_ of a **namespace**)
    - _a.b.c_ (where _b.c_ is the _identifier_ of a different **namespace**)
    - _c.b.c_ or _d.e.b.b_ or any other unique string of _names_ can be used to
      to identify a **namespace**, a **currency** or an **identity**.
- An _identifier_ comprises a _name_ and a **namespace**. Each _identifier_ is
  therefore globally unique, and can identify any **currency**, _agent_ or
  **namespace**.
- An **identity** identifies an _agent_. Any _agent_ may have any number of
  **identities** each of which comprises a different concatenation of _name_
  and **namespace** _identifier_.

The terms **currency**, **identity** and **namespace** are shown in bold (a
convention introduced for _NESTS_ originally) because these are the _atomic
units_ from which a payment network can be built. Together they are classed as
_entities_ (another term introduced for _NESTS_ and which can be considered
synonymous with _atomic units_).

The _name_ of every _entity_ is contained within a **namespace** (known as its
_parent_ **namespace**). The _entities_ the _names_ of which are contained in a
**namespace** are referred to as its _children_.[^2]

In the case of **namespaces**, the _parent_-_child_ concept can be extended in
either direction to refer to _ancestors_ and _descendants_ respectively.  

In order to make a _payment_ from one _agent_ to _another_, the following must
be known:
- the **identity** by which the _payer_ is to be identified
- the **identity** by which the _payee_ is to be identified
- the **currency** in which the _payment_ is to be made

Each combination of **identity** and **currency** is unique and has a _value_
(its _balance_). When a _payment_ is made, one such _balance_ (that of the
_payer_) is decreased by a specified _amount_ while the other (that of the
_payee_) is increased by exactly the same _amount_. Because an expression such
as "unique combination of **identity** and **currency**" is rather unwieldy, it
is convenient to introduce a new term (_account_) to simplify things. So, for
example, the term _payment_ can now be defined as
- the simultaneous adjustment of two _accounts_ in the same **currency** by the
  same _amount_, one positive and the other negative.

You will note that the term _account_ is not rendered as **account** here. That
is because, in this simpler context (that in which users will be introduced
gently to _open money_ concepts), the **account** is not _required_ as a
distinct category of _entity_.

An **identity** (as defined above) is all that is required, in combination with
a **currency**, to identify either of the two parties (_agents_) involved in a
payment.

However, since any _agent_ may have a uniquely-identified presence (a _name_)
in any **namespace**, a further distinction must be made here:

- A **login identity** is the unique identifier of an _agent_ (within a
  collection of connected _open money_ networks). Upon first registering, the
  _agent_ has only a **login identity** (also known sometimes as a **primary
  identity**).
- Once registered, the _agent_ may create any number of **aliases**, the _name_
  of each of which may appear in _any_ **namespace** (in which that _name_ is
  not already in use, and subject to authorization by the _stewards_ of that
  **namespace**) and each in any **currency** (subject to authorization by the
  _stewards_ of that **currency**). This means that an _agent_ does not have to
  maintain a collection of **login identities** in order to move around within
  the various _payment_ networks (although that option is always open as well).
  This also means that the _agent_ can easily see the balance of each _account_
  alongside its **currency** and the **identity** that _owns_ it.

A new term has just been introduced:

- A _steward_ is one of a set of **(**login**)** identities** sharing
  responsibility for the governance or maintenance of a **namespace** or
  **currency**. How the _stewards_ organize themselves in this role in largely
  up to them (within certain constraints) as is the detail of the policies they
  may choose to adopt as criteria for _authorization_ to use that _entity_.

NB, few rules are imposed generally, and the approach to _governance_ is
usually very light touch. However, in the case where an _open money_
**currency** is used in place of (and alongside) a _metrically equivalent_
government-issued money, the users obviously have a legal responsibility not to
violate laws (and, for this reason, each is responsible for disclosure its own
_payment_ records[^3] where, when and to whomever required). The _stewards_ have
a role in identifying possible misuse of the tools provided, and they have both
the _ability_ and the _obligation_ to exclude misbehaving _agents_.


---
### An extended perspective

As originally designed in _NESTS_ (and later carried over to _SLATE_), a
number of extensions increases the potential power and reach of these tools
considerably. _NESTS_/_SLATE_ extends things an a number of ways:

- An **account** (as distinct from an _account_) is the unique _identifier_ of
  a unique combination of an **identity** and a **currency**. The _name_ of
  that **account** may be in any **namespace** (which may be different from the
  _parent_ **namespace** of either the **identity** or the **currency**). This
  approach offers two advantages (especially for _payment_ intensive
  applications such as simulations):
  - A _payment_ may be made directly to an **account** (without having to
    specify the unique **identity**+**currency** combination it identifies). If
    situations were to arise in which a greater measure of privacy were
    required (and these are not inconceivable, even in a very small and highly-local network - for example where an _agent_ might wish to make a
    quasi-anonymous donation), or in which someone who has carried out an
    anonymous act of generosity does not wish to be identified by a beneficiary
    insistent upon acknowledging that act through a payment.
  - This approach in turn reduces the number of columns required (for example
    in a CSV file used to specify the _payers_ and _payees_ in a bulk upload),
    so, for example, the same _payment_ can be specified or recorded in either
    of the two equivalent ways:
    - **identity** (payer) | **identity** (payee) | **currency** | _amount_
    - **account** (payer) | **account** (payee) | _amount_

- In _NESTS_, the concept of the **currency** has been extended to encompass
  any _named_ variable. This means that we are no longer restricted to scalar
  values. In addition, the **accounts** within[^4] a **currency** may be
  anything the structure of which can be implemented, including
  - vectors (including information preserving currencies and high-variety
    impact vectors)
  - matrices
  - tuples
  - arbitrary mappings
  - (pointers to) time series data
  - trigger descriptors (e.g. for escrow use)

- In _NESTS_, the concept of the _agent_ has been extended beyond humans,
  organizations or virtual representations of such (e.g. in agent-based
  simulations and interactive sandboxes) to include _devices_ ranging from
  networked sensors and controls (used in such IoT[^5] or "edge computing" roles
  as environmental monitoring, irrigation and climate control within a food
  production system, or the management of a multi-functional "community hub"
  [^6]).

Here we are extending a concept of _open measure_[^7], of which _open money_ is
a very important special case.


---
##### Notes

[^1]: This convention has arisen because the implementations to date have been
      restricted to the standard Latin character set. In order to accommodate
      other character sets, the _NESTS_ design allows for any UTF-8 character
      to be used. It remains to be seen whether that provides an adequate
      solution.

[^2]: This is not strictly true because **namespaces** at the _root_ of a tree
      cannot have a named _parent_ **namespace**. Instead their names sit
      within a _nameless_ **namespace** (referred to as the _substrate_ in some
      places) serving them as a _virtual parent_ in which new _entities_ cannot
      be created.  

[^3]: Unless such a law applies locally, the _stewards_ generally bear no
      responsibility for monitoring or reporting on the activity of an
      **agents** within the scope of their _stewardship_. They do however have
      the right to exclude **agents** (each of which retains _ownership_ of the
      **accounts** for which they bear responsibility). (In general, it is
      likely that the _stewards_ would take a rather gentle approach initially,
      starting with a query, followed by advice, then by a series of warnings,
      before reaching the stage of exclusion, and the details of the policy
      adopted are largely to be agreed among themselves).

[^4]: For consistency with use (in such a context) by accountants or tax
      authorities (for example), the term "accounts" could have been used here
      in place of "_payment_ records", but that would be inconsistent with the
      use above (which is analoguous to its use in terms such as _savings
      account_, _current account_, _loan account_ and so on). Instead, the
      term _journal_ is used here to refer to the record of all _payments_ to
      or from a particular _account_.

[^5]: IoT = "Internet of Things". Networked devices varyingly widely in their
      purpose, capacity and sophistication.

[^6]: It is easy to imagine (as an example) developing a (very) local facility
      to manage the storage and distribution of community-generated energy.
      Such a facility might also assist in the management of local
      water-collection, -filtration and -distribution systems, or as a host for
      any number of other approaches to increasing local capacity and
      resilience. While such a _hub_ would generally be networked in various
      ways with other such _hubs_, they would also serve a very important role
      where the inter-_hub_ communication is lost temporarily. For example, in
      the case a disaster (such as a flood) bringing down _either_ the power
      lines of the phone/fibre lines, the _hub_ could help both to keep the
      lights on (adequately if minimally) and to maintain a shorter-term
      continuity is the _truly local_ economy by the provision of _open money_
      payment tools that any member of the community can use.

[^7]: The term _open measure_ was coined by Les Moore, building upon the
      earlier concept of _open money_ (itself an expansion of the earlier
      _LETSystem_ model developed by Michael Linton and others).
