import assert from "node:assert/strict";

import {
  createWorkflow,
  enabledFields,
  markLoaded,
  requestIntent,
} from "../static/workflows.mjs";


const customerFields = [
  "customer_number",
  "first_name",
  "last_name",
  "date_of_birth",
  "house_name",
  "house_number",
  "postcode",
  "home_phone",
  "mobile_phone",
  "email",
];

const motorFields = [
  "policy_number",
  "customer_number",
  "issue_date",
  "expiry_date",
  "car_make",
  "car_model",
  "car_value",
  "registration",
  "car_colour",
  "engine_cc",
  "manufacture_date",
  "accident_count",
  "policy_premium",
];

const checks = [];

function check(name, run) {
  checks.push({ name, run });
}

check("customer add hides the generated customer number", () => {
  const customerAdd = createWorkflow("customer", "add");
  assert.deepEqual(
    enabledFields(customerAdd, customerFields),
    customerFields.filter((field) => field !== "customer_number"),
    "customer Add must not accept a clerk-entered identifier",
  );
  assert.equal(requestIntent(customerAdd), "add");
});

check("customer update loads before editable fields open", () => {
  let customerUpdate = createWorkflow("customer", "update");
  assert.deepEqual(enabledFields(customerUpdate, customerFields), ["customer_number"]);
  assert.equal(requestIntent(customerUpdate), "load-update");
  customerUpdate = markLoaded(customerUpdate);
  assert.deepEqual(
    enabledFields(customerUpdate, customerFields),
    customerFields.filter((field) => field !== "customer_number"),
  );
  assert.equal(requestIntent(customerUpdate), "submit-update");
});

check("motor add hides the generated policy number", () => {
  const motorAdd = createWorkflow("motor", "add");
  assert.deepEqual(
    enabledFields(motorAdd, motorFields),
    motorFields.filter((field) => field !== "policy_number"),
    "motor Add must not accept a clerk-entered policy number",
  );
});

check("motor inquiry and delete accept both identifiers", () => {
  for (const operation of ["inquire", "delete"]) {
    const workflow = createWorkflow("motor", operation);
    assert.deepEqual(
      enabledFields(workflow, motorFields),
      ["policy_number", "customer_number"],
      `motor ${operation} must accept both identifiers`,
    );
  }
});

check("motor update loads with both identifiers before editing", () => {
  let motorUpdate = createWorkflow("motor", "update");
  assert.deepEqual(
    enabledFields(motorUpdate, motorFields),
    ["policy_number", "customer_number"],
  );
  assert.equal(requestIntent(motorUpdate), "load-update");
  motorUpdate = markLoaded(motorUpdate);
  assert.equal(requestIntent(motorUpdate), "submit-update");
  assert.ok(
    !enabledFields(motorUpdate, motorFields).includes("policy_number"),
    "the loaded policy number must stay locked while editing",
  );
});

for (const { name, run } of checks) {
  run();
  console.log(`ok - ${name}`);
}

console.log(`Workflow regression tests passed: ${checks.length}/${checks.length}.`);
