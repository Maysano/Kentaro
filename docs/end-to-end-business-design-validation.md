# End-to-end business-design validation

`tests/fixtures/business_design_validation/customer-risk-assessment.json` is Kentaro's
versioned synthetic Business Owner journey. It is a product-level contract, not a live bank
example: no credentials, customer content, or graph snapshots are stored in it.

The fixture includes ordinary-language prompts, two graph revisions, and expected outcomes for
context, discovery, reuse, alternatives, explicit decisions, incomplete-input handling, handover
gates, and changed evidence. The automated companion is
`tests/test_end_to_end_business_design.py`:

The fixture directory also contains `expected-design-portfolio.html`, an inspectable canvas
rendered from the checked-in completed portfolio, and `expected-handover.zip`, the corresponding
final handover example.

```shell
python3 -m unittest tests.test_end_to_end_business_design -v
```

To extend the case, append a turn with a stable ID and expected contract. Do not rewrite prior
prompts or expected outcomes: they represent the established Business Owner experience. Add only
synthetic graph records, and retain source references, versions, and timestamps—not source
payloads—in expected persisted evidence.

The current test invokes Kentaro's deterministic lifecycle services directly. A future agent-turn
runner should consume the same prompt fixture and assert its conversational response against each
turn's expected contract.
