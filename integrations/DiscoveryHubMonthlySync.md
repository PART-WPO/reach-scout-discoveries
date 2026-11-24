# Monthly proposals and private Discovery Hub synchronization

The December 1 harvest keeps its existing schedule. The scheduled coverage
catch-up waits for a verified harvest receipt and active source batches, uses
the existing quick intake, and dispatches the existing Scout feed publication
workflow. The publication workflow still independently checks official
publication status and requires exact draft checksums. The public feed keeps
the 24-column CSV contract. A public batch is an invitation for human review.

## Private installation

The public repo documents **Sync from Scout** as the current import action.
Its production handler, installed Apps Script project, private review store,
and time-trigger permissions are outside the connected repositories. The Hub
owner should check the deployed trigger list before installing anything.

In an authorized private Hub copy, extract the server-side operation used by
**Sync from Scout** so both the button and an installable time-driven trigger
call the same operation. Resolve the actual handler name and datastore with
the owner. Use the existing Hub review-identity function and import
permissions. The trigger's service identity needs read access to the public
manifest and its batches and narrowly scoped write access to private review
intake and private import receipts. Keep the trigger, configuration and
receipts inside the Hub. Public GitHub needs no Hub credential.

1. Under the same writer lock or transaction used by manual sync, read the
   validated manifest at a single Git revision. Fetch CSVs from that revision
   and verify each batch digest, row count and exact schema. Select monthly
   Direct API original proposals classified **New Candidate** or **Needs
   Investigation**. This check must accept documented blanks for author or
   abstract in **Needs Investigation** without accepting missing identity,
   publication date or funding source.
2. For each proposal use the existing stable Hub review identity across
   cohorts, feed revisions and classifications. Check existing candidates,
   legacy aliases, reviewed identities and private holds before writing.
   Insert one unreviewed card if new. Otherwise leave the existing card and
   review state unchanged. An unresolved legacy identity or active reviewer
   hold suppresses creation and remains visible only inside the Hub. Copy the
   public rationale, funding evidence and unresolved questions. Leave
   Smartsheet parent selection to a reviewer.
3. Record a durable private receipt with the manifest revision, source batch
   digest, result counts and per-item outcome. Write the import and receipt
   atomically where the existing store supports transactions. Otherwise persist
   per-identity progress under the shared writer lock, reconcile cards already
   present by stable identity after a crash, and acknowledge only after
   confirming the committed cards. Advance the private cursor only after a
   successful receipt. Retry from the previous cursor on failure. A repeat
   across the button and trigger must produce no additional cards.
4. In the copy, force a failed import before writing a card, then retry. Also
   force an interruption after writing a card but before acknowledging it.
   Require one card total, a successful receipt, and intact prior reviewer
   decisions in both scenarios. Test a known duplicate, prior reviewed card
   and held DOI. Enable a trigger only after the owner verifies these cases
   and confirms that approvals, Smartsheet and REACH writes are outside the
   trigger's authority.

The public Scout workflow can report manifest-published proposals. Count
confirmed Hub imports only from authorized private receipts. The October replay
and synthetic promotion tests stop at the public staging boundary.
