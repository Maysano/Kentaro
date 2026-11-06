# ODPC v1.1 AI Product Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** Make ODPC v1.1 the only AI-product specification emitted by Kentaro, backed by first-class validation in Open Data Products.

**Architecture:** Open Data Products first gains ODPC v1.1 profile recognition, validation, and catalog support. Kentaro then pins that released SDK, captures missing AI-product business claims through its persistent engagement workflow, and emits only validated ODPC profile/catalog/graph artifacts while exposing incomplete coverage without blocking local business design.

**Tech Stack:** Python 3.11+, open-data-products, JSON Schema Draft 2020-12, JSON-compatible YAML, unittest, zipfile.

---

## Repository boundary and file structure

Tasks 1–4 run in the upstream Open Data Products SDK repository. Tasks 5–8 run in \`/Users/jarkkomoilanen/Developer/GitHub/Kentaro\`. Do not begin Task 5 until Task 4's SDK wheel is published and clean-installed.

**SDK files**

- Create \`open_data_products/odpc/ai_product.py\`: profile loading, validation, and cross-artifact checks.
- Create \`open_data_products/odpc/data/schema/v1.1/{ai-product,odpc}.yaml\`: exact official schemas.
- Modify \`open_data_products/odpc/{__init__.py,catalog.py}\`, \`open_data_products/{agent.py,cli.py,resources.py}\`, and package-data settings.
- Create \`tests/fixtures/odpc_v1_1/\` and \`tests/test_odpc_v1_1_ai_product.py\`; extend existing CLI/wheel tests.

**Kentaro files**

- Modify \`pyproject.toml\`, \`kentaro/design/{specifications,engagement,handover,reports,render}.py\`, and \`kentaro/cli.py\`.
- Modify \`tests/{test_design_engagement,test_design_handover,test_design}.py\` and generated business-design fixtures.
- Modify \`README.md\`, \`docs/{README,delivery-plan,roadmap,business-design-journeys}.md\`, and \`.agents/skills/kentaro-ai-product-design/SKILL.md\`.

### Task 1: Add upstream profile validation

**Files:**

- Create: \`open_data_products/odpc/data/schema/v1.1/ai-product.yaml\`
- Create: \`open_data_products/odpc/ai_product.py\`
- Create: \`tests/fixtures/odpc_v1_1/rag-knowledge-assistant.{yaml,json}\`
- Create: \`tests/test_odpc_v1_1_ai_product.py\`

- [ ] **Step 1: Write the failing profile tests.**

~~~python
from open_data_products.odpc import load_ai_product, validate_ai_product

def test_validate_ai_product_accepts_the_official_v1_1_example():
    result = validate_ai_product(load_ai_product(FIXTURES / "rag-knowledge-assistant.yaml"))
    assert result.valid
    assert result.errors == []

def test_validate_ai_product_reports_missing_governance_path():
    document = load_ai_product(FIXTURES / "rag-knowledge-assistant.yaml")
    del document["aiProduct"]["governance"]
    assert any("aiProduct.governance" in error for error in validate_ai_product(document).errors)
~~~

- [ ] **Step 2: Run the focused test to verify RED.**

Run: \`python3 -m pytest tests/test_odpc_v1_1_ai_product.py -q\`

Expected: import failure for the new public functions.

- [ ] **Step 3: Add the canonical schema and minimal validator.**

Copy the official profile schema without semantic changes. Use the SDK's safe mapping loader and return the shared result shape:

~~~python
AI_PRODUCT_SCHEMA_URL = "https://opendataproducts.org/odpc-v1.1/schema/ai-product.yaml"

def validate_ai_product(document: dict[str, object]) -> ValidationResult:
    validator = Draft202012Validator(load_ai_product_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    messages = [f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors]
    return ValidationResult(not messages, "odpc", "AIProduct", messages, version="1.1")
~~~

- [ ] **Step 4: Run the focused test to verify GREEN.**

Run: \`python3 -m pytest tests/test_odpc_v1_1_ai_product.py -q\`

Expected: both tests pass.

- [ ] **Step 5: Commit the isolated upstream change.**

~~~bash
git add open_data_products/odpc/ai_product.py open_data_products/odpc/data/schema/v1.1/ai-product.yaml tests/fixtures/odpc_v1_1 tests/test_odpc_v1_1_ai_product.py
git commit -m "feat: validate ODPC v1.1 AI products"
~~~

### Task 2: Detect and validate AI-product documents through the SDK API and CLI

**Files:**

- Modify: \`open_data_products/odpc/__init__.py\`, \`open_data_products/agent.py\`, \`open_data_products/cli.py\`, \`open_data_products/resources.py\`, and package-data settings.
- Modify: \`tests/test_odpc_v1_1_ai_product.py\` and the existing CLI-validation tests.

- [ ] **Step 1: Write failing detector and CLI tests.**

~~~python
def test_detect_document_distinguishes_an_ai_product_from_a_catalog():
    assert detect_document(load_ai_product(FIXTURES / "rag-knowledge-assistant.yaml")) == ("odpc", "AIProduct")

def test_cli_validate_reports_an_ai_product_json_payload(capsys):
    assert main(["validate", str(FIXTURES / "rag-knowledge-assistant.yaml"), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "AIProduct"
~~~

- [ ] **Step 2: Run the focused tests to verify RED.**

Run: \`python3 -m pytest tests/test_odpc_v1_1_ai_product.py -q\`

Expected: the document is treated as a catalog or rejected.

- [ ] **Step 3: Dispatch before generic catalog detection and export the new API.**

Add the detector branch before catalog handling:

~~~python
if schema == AI_PRODUCT_SCHEMA_URL or kind == "AIProduct":
    return "odpc", "AIProduct"
if "odpc" in schema or kind == "Catalog" or "catalog" in document:
    return "odpc", kind or "Catalog"
~~~

Update \`load_document\`, \`validate_document\`, CLI help/activity output, SDK resources, and wheel package data. AI-product validation must not call \`load_catalog\`.

- [ ] **Step 4: Run focused API and CLI tests to verify GREEN.**

Run: \`python3 -m pytest tests/test_odpc_v1_1_ai_product.py tests/test_cli.py -q\`

Expected: JSON reports \`spec: "odpc"\`, \`kind: "AIProduct"\`, and \`version: "1.1"\`.

- [ ] **Step 5: Commit.**

~~~bash
git add open_data_products/odpc/__init__.py open_data_products/agent.py open_data_products/cli.py open_data_products/resources.py pyproject.toml tests
git commit -m "feat: detect ODPC AI product documents"
~~~

### Task 3: Validate ODPC v1.1 catalog forms and the profile/catalog/graph bundle

**Files:**

- Create: \`open_data_products/odpc/data/schema/v1.1/odpc.yaml\`
- Modify: \`open_data_products/odpc/{catalog.py,ai_product.py}\`
- Create: \`tests/fixtures/odpc_v1_1/catalog-ai-products.yaml\`
- Modify: \`tests/test_odpc_v1_1_ai_product.py\`

- [ ] **Step 1: Write failing catalog and cross-artifact tests.**

~~~python
def test_v1_1_catalog_accepts_inline_ai_product_and_profile_reference():
    assert validate_catalog(load_catalog(FIXTURES / "catalog-ai-products.yaml")).valid

def test_bundle_rejects_product_reference_identity_mismatch():
    bundle = load_ai_product_bundle(PROFILE, CATALOG, GRAPH)
    bundle.catalog["catalog"]["nodes"][1]["node"]["productID"] = "wrong-id"
    assert not validate_ai_product_bundle(bundle).valid
~~~

- [ ] **Step 2: Run the tests to verify RED.**

Run: \`python3 -m pytest tests/test_odpc_v1_1_ai_product.py -q\`

Expected: v1.1 catalog selection or bundle validation is unavailable.

- [ ] **Step 3: Add version-aware schema selection and exact cross-artifact checks.**

Select v1.1 only for its canonical schema URL and \`version: "1.1"\`; do not widen v1.0. Validate profile, catalog, and ODPG first, then collect all mismatch findings. Check equality of the three \`productID\` and \`productVersion\` values, \`ODPC/1.1/AIProduct\` product-model fields, relative profile reference, and \`graph_node["type"] == "AIProduct"\`.

- [ ] **Step 4: Run focused tests to verify GREEN.**

Run: \`python3 -m pytest tests/test_odpc_v1_1_ai_product.py -q\`

Expected: valid fixtures pass; identity, version, reference, and node-type mismatches fail.

- [ ] **Step 5: Commit.**

~~~bash
git add open_data_products/odpc tests/fixtures/odpc_v1_1 tests/test_odpc_v1_1_ai_product.py
git commit -m "feat: validate ODPC v1.1 AI product catalogs"
~~~

### Task 4: Verify and release the SDK

**Files:**

- Modify: release metadata and notes under the upstream repository's established release convention.
- Test: full suite and clean wheel installation.

- [ ] **Step 1: Run the full SDK suite.**

Run: \`python3 -m pytest -q\`

Expected: exit code 0.

- [ ] **Step 2: Build the SDK distributions.**

Run: \`PYTHONDONTWRITEBYTECODE=1 python3 -m build\`

Expected: wheel and source distribution under \`dist/\`.

- [ ] **Step 3: Smoke test the installed wheel outside the checkout.**

Run: \`python3 -m venv /private/tmp/odpc-v11-sdk-smoke && /private/tmp/odpc-v11-sdk-smoke/bin/pip install dist/*.whl && /private/tmp/odpc-v11-sdk-smoke/bin/open-data-products validate tests/fixtures/odpc_v1_1/rag-knowledge-assistant.yaml --json\`

Expected: valid JSON for ODPC \`AIProduct\` version \`1.1\`.

- [ ] **Step 4: Publish using the upstream repository's existing release procedure, then install the published version in a fresh environment.**

Expected: the package index serves the exact wheel verified in Step 3.

- [ ] **Step 5: Commit verified release metadata.**

~~~bash
git add pyproject.toml CHANGELOG.md
git commit -m "release: publish ODPC v1.1 AI product support"
~~~

### Task 5: Add non-blocking ODPC claim intake and targeted questions in Kentaro

**Files:**

- Modify: \`kentaro/design/{specifications.py,engagement.py}\`, \`kentaro/cli.py\`
- Modify: \`tests/{test_design_engagement.py,test_design.py}\`

- [ ] **Step 1: Write failing engagement tests.**

~~~python
def test_engagement_requests_missing_odpc_ai_product_details():
    state = build_engagement_state(portfolio_with_proposed_ai_product(), portfolio_path=Path("/tmp/portfolio.json"))
    topic = next(item for item in state["topics_to_resolve"] if item["topic"] == "ODPC AI-product definition")
    assert topic["items"][0]["code"] == "missing_ai_product_odpc_identity"
    assert "product ID" in state["next_unresolved_requirement"]

def test_odpc_ai_product_gaps_do_not_change_structural_completion():
    assert structural_completion(portfolio_with_proposed_ai_product())["structurally_complete"]
~~~

- [ ] **Step 2: Run the tests to verify RED.**

Run: \`python3 -m unittest tests.test_design_engagement tests.test_design -v\`

Expected: the ODPC topic and question are absent.

- [ ] **Step 3: Implement one coverage function and structured CLI input.**

Implement \`ai_product_odpc_coverage(item)\` in \`specifications.py\`. It returns a coverage state, stable missing paths, source-claim IDs, and one grouped question. Required confirmed/case-fact claims are identity/version/type, structured owner, autonomy, human oversight requirements, consequential-action approval requirements, risk classification, known limitations, and one complete evaluation metric.

Add \`kentaro design set-ai-product-odpc --input --object-id --input-json --status --source-id --source-revision --derivation-input-hash\`. It must reject malformed JSON and non-AI-product objects before saving; otherwise it makes each leaf provenance-bearing, saves, and invokes the existing engagement refresh.

- [ ] **Step 4: Run the focused tests to verify GREEN.**

Run: \`python3 -m unittest tests.test_design_engagement tests.test_design -v\`

Expected: the grouped question is actionable and does not alter unrelated handover gates.

- [ ] **Step 5: Commit.**

~~~bash
git add kentaro/design/specifications.py kentaro/design/engagement.py kentaro/cli.py tests/test_design_engagement.py tests/test_design.py
git commit -m "feat: collect ODPC AI product design claims"
~~~

### Task 6: Replace private Kentaro AI-product export with SDK-validated artifacts

**Files:**

- Modify: \`pyproject.toml\`, \`kentaro/design/{reports.py,specifications.py,handover.py}\`
- Modify: \`tests/test_design_handover.py\`

- [ ] **Step 1: Write failing partial and complete handover tests.**

~~~python
def test_incomplete_ai_product_has_status_but_no_normative_artifacts():
    prepare_handover_review(portfolio_with_proposed_ai_product(), target)
    status = json.loads((target / "governance" / "ai-product-specification-status.json").read_text())
    assert status["products"][0]["coverage"] == "awaiting_odpc_input"
    assert not (target / "specifications" / "ai-products" / "ai-review.odpc.yaml").exists()

def test_complete_ai_product_exports_all_three_odpc_forms():
    export_handover(complete_portfolio_with_confirmed_odpc_ai_product(), target, reviewer="Jarkko", confirmation="I confirm this reviewed handover is ready for its intended builder.", acknowledge_all_open_decisions=True)
    with zipfile.ZipFile(target) as archive:
        assert "specifications/ai-products/ai-review.odpc.yaml" in archive.namelist()
        assert b'"type": "AIProduct"' in archive.read("specifications/odpg.yaml")
~~~

- [ ] **Step 2: Run the test to verify RED.**

Run: \`python3 -m unittest tests.test_design_handover -v\`

Expected: current \`KentaroAIProductDefinition\` and \`Agent\` expectations fail.

- [ ] **Step 3: Implement the mapping and strict replacement.**

Pin \`pyproject.toml\` to Task 4's exact published SDK version. Replace the private JSON loop with coverage-aware profile generation. Complete products write the profile, an inline \`aiProduct\` node, a \`productReference\`, and an \`AIProduct\` graph node. Incomplete products write only \`governance/ai-product-specification-status.json\` and a clearly local graph reference, never a dangling ODPC path.

Replace \`validate_odps\` with generic SDK validation that retains \`spec\`, \`kind\`, \`version\`, errors, and SDK version. Call the SDK bundle validator after output generation. Set \`HANDOVER_SCHEMA_VERSION = 2\`; retain strict manifest checking so version 1 is rejected.

- [ ] **Step 4: Run the test to verify GREEN.**

Run: \`python3 -m unittest tests.test_design_handover -v\`

Expected: partial coverage is explicit, complete artifacts validate, tampering fails, and v1 packages are rejected.

- [ ] **Step 5: Commit.**

~~~bash
git add pyproject.toml kentaro/design/reports.py kentaro/design/specifications.py kentaro/design/handover.py tests/test_design_handover.py
git commit -m "feat: export ODPC v1.1 AI product handovers"
~~~

### Task 7: Replace rendered delivery language, fixtures, and guidance

**Files:**

- Modify: \`kentaro/design/render.py\`, \`tests/test_design.py\`, and \`tests/fixtures/business_design_validation/\`
- Modify: \`README.md\`, \`docs/\`, and \`.agents/skills/kentaro-ai-product-design/SKILL.md\`

- [ ] **Step 1: Write the failing rendered-output assertion.**

~~~python
def test_canvas_shows_odpc_v1_1_coverage_without_claiming_validation():
    canvas = render_canvas(portfolio_with_proposed_ai_product())
    assert "ODPC v1.1 AI-product input required" in canvas
    assert "Kentaro AI-product definition" not in canvas
~~~

- [ ] **Step 2: Run it to verify RED.**

Run: \`python3 -m unittest tests.test_design -v\`

Expected: old private-definition wording causes failure.

- [ ] **Step 3: Render and document the same coverage state used by handover generation.**

Display \`awaiting_odpc_input\`, \`invalid\`, or \`validated\` and its targeted next question. Remove every reference to \`KentaroAIProductDefinition\`. Update docs and the skill to require human-supplied ODPC fields, preserve provenance, and distinguish validation from approval, access, implementation readiness, and production readiness.

- [ ] **Step 4: Regenerate fixtures and verify GREEN.**

Run: \`python3 -m unittest tests.test_design tests.test_end_to_end_business_design -v\`

Expected: deterministic fixtures are regenerated from the revised implementation and pass.

- [ ] **Step 5: Commit.**

~~~bash
git add kentaro/design/render.py tests/test_design.py tests/fixtures/business_design_validation README.md docs .agents/skills/kentaro-ai-product-design/SKILL.md
git commit -m "docs: adopt ODPC v1.1 AI product workflow"
~~~

### Task 8: Verify the Kentaro release candidate

**Files:**

- Test: all tracked tests and clean wheel behavior.

- [ ] **Step 1: Run the complete Kentaro test suite.**

Run: \`python3 -m unittest discover -s tests -v\`

Expected: exit code 0.

- [ ] **Step 2: Check whitespace.**

Run: \`git diff --check\`

Expected: no output and exit code 0.

- [ ] **Step 3: Build a clean wheel.**

Run: \`PYTHONDONTWRITEBYTECODE=1 python3 -m build\`

Expected: wheel and source distribution build successfully.

- [ ] **Step 4: Smoke-test the installed Kentaro wheel outside the checkout.**

Run: \`python3 -m venv /private/tmp/kentaro-odpc-v11-smoke && /private/tmp/kentaro-odpc-v11-smoke/bin/pip install dist/*.whl && /private/tmp/kentaro-odpc-v11-smoke/bin/kentaro doctor\`

Expected: the installed package reports the Task 4 SDK version and validates its packaged resources without the source checkout.

- [ ] **Step 5: Commit only verified release metadata through the existing release process.**

~~~bash
git add pyproject.toml RELEASE_NOTES.md
git commit -m "release: publish Kentaro ODPC v1.1 AI product support"
~~~

## Plan self-review

- The upstream SDK validates the official profile and catalog before Kentaro changes its dependency.
- Kentaro intake, non-blocking questions, artifact coverage, strict schema replacement, rendered output, and documentation have dedicated test-first tasks.
- No task writes Maysano, auto-approves a decision, infers governance values, or provides compatibility for retired handover schemas.
