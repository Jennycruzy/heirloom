import {
  createWorkflow,
  enabledFields,
  markLoaded,
  requestIntent,
} from "/static/workflows.mjs";

const customerFields = [
  "customer_number", "first_name", "last_name", "date_of_birth", "house_name",
  "house_number", "postcode", "home_phone", "mobile_phone", "email",
];
const motorFields = [
  "policy_number", "customer_number", "issue_date", "expiry_date", "car_make",
  "car_model", "car_value", "registration", "car_colour", "engine_cc",
  "manufacture_date", "accident_count", "policy_premium",
];

function requireElement(selector) {
  const element = document.querySelector(selector);
  if (!element) throw new Error(`Missing required DOM element: ${selector}`);
  return element;
}

const status = requireElement("#app-status");
const customerForm = requireElement("#customer-form");
const customerOperation = requireElement("#customer-operation");
const customerSubmit = requireElement("#customer-submit");
const customerResult = requireElement("#customer-result dl");
const motorForm = requireElement("#motor-form");
const motorOperation = requireElement("#motor-operation");
const motorSubmit = requireElement("#motor-submit");
const motorResult = requireElement("#motor-result dl");

for (const field of customerFields) requireElement(`#customer-${field}`);
for (const field of motorFields) requireElement(`#motor-${field}`);

let customerWorkflow = createWorkflow("customer", customerOperation.value);
let motorWorkflow = createWorkflow("motor", motorOperation.value);

function setStatus(message, kind = "") {
  status.textContent = message;
  status.classList.remove("status--success", "status--error");
  if (kind) status.classList.add(`status--${kind}`);
}

async function request(method, url, payload) {
  const options = { method, headers: { Accept: "application/json" } };
  if (payload !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(payload);
  }
  const response = await fetch(url, options);
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`Server returned HTTP ${response.status} without valid JSON`);
  }
  if (!response.ok) throw new Error(body.error || `Request failed with HTTP ${response.status}`);
  return body.data;
}

function values(form, fields) {
  const formData = new FormData(form);
  return Object.fromEntries(fields.map((field) => [field, String(formData.get(field) ?? "")]));
}

function populate(prefix, record) {
  for (const [field, value] of Object.entries(record)) {
    const input = document.querySelector(`#${prefix}-${field}`);
    if (input) input.value = value;
  }
}

function renderResult(container, record) {
  const nodes = [];
  for (const [field, value] of Object.entries(record)) {
    const term = document.createElement("dt");
    term.textContent = field.replaceAll("_", " ");
    const description = document.createElement("dd");
    description.textContent = value;
    nodes.push(term, description);
  }
  container.replaceChildren(...nodes);
}

function applyWorkflow(prefix, fields, workflow, submit) {
  const active = new Set(enabledFields(workflow, fields));
  for (const field of fields) {
    const input = requireElement(`#${prefix}-${field}`);
    const inactive = !active.has(field);
    input.disabled = inactive;
    input.closest(".form-group").classList.toggle("field--inactive", inactive);
  }
  const intent = requestIntent(workflow);
  if (intent === "load-update") submit.textContent = "Load current record";
  else if (workflow.entity === "customer") submit.textContent = "Run customer task";
  else submit.textContent = "Run motor policy task";
}

function requireValue(selector, label) {
  const value = requireElement(selector).value.trim();
  if (!value) throw new Error(`${label} is required`);
  return value;
}

function motorUrl(policyNumber, customerNumber) {
  const query = new URLSearchParams({ customer_number: customerNumber });
  return `/api/motor-policies/${encodeURIComponent(policyNumber)}?${query}`;
}

customerOperation.addEventListener("change", () => {
  customerWorkflow = createWorkflow("customer", customerOperation.value);
  applyWorkflow("customer", customerFields, customerWorkflow, customerSubmit);
});

motorOperation.addEventListener("change", () => {
  motorWorkflow = createWorkflow("motor", motorOperation.value);
  applyWorkflow("motor", motorFields, motorWorkflow, motorSubmit);
});

customerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const intent = requestIntent(customerWorkflow);
  customerSubmit.disabled = true;
  try {
    let record;
    if (intent === "add") {
      record = await request(
        "POST",
        "/api/customers",
        values(customerForm, customerFields.filter((field) => field !== "customer_number")),
      );
      populate("customer", record);
      renderResult(customerResult, record);
      setStatus(`Customer ${record.customer_number} added.`, "success");
      return;
    }

    const identifier = requireValue("#customer-customer_number", "Customer number");
    if (intent === "inquire" || intent === "load-update") {
      record = await request("GET", `/api/customers/${encodeURIComponent(identifier)}`);
      populate("customer", record);
      renderResult(customerResult, record);
      if (intent === "load-update") {
        customerWorkflow = markLoaded(customerWorkflow);
        applyWorkflow("customer", customerFields, customerWorkflow, customerSubmit);
        setStatus(`Customer ${identifier} loaded for update.`, "success");
      } else {
        setStatus(`Customer ${identifier} loaded.`, "success");
      }
      return;
    }

    record = await request(
      "PUT",
      `/api/customers/${encodeURIComponent(identifier)}`,
      values(customerForm, customerFields.filter((field) => field !== "customer_number")),
    );
    populate("customer", record);
    renderResult(customerResult, record);
    setStatus(`Customer ${identifier} updated.`, "success");
  } catch (error) {
    setStatus(`Customer task failed: ${error.message}`, "error");
  } finally {
    customerSubmit.disabled = false;
  }
});

motorForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const intent = requestIntent(motorWorkflow);
  motorSubmit.disabled = true;
  try {
    let record;
    if (intent === "add") {
      requireValue("#motor-customer_number", "Customer number");
      record = await request(
        "POST",
        "/api/motor-policies",
        values(motorForm, motorFields.filter((field) => field !== "policy_number")),
      );
      populate("motor", record);
      renderResult(motorResult, record);
      setStatus(`Motor policy ${record.policy_number} added.`, "success");
      return;
    }

    const policyNumber = requireValue("#motor-policy_number", "Policy number");
    const customerNumber = requireValue("#motor-customer_number", "Customer number");
    const url = motorUrl(policyNumber, customerNumber);

    if (intent === "inquire" || intent === "load-update") {
      record = await request("GET", url);
      populate("motor", record);
      renderResult(motorResult, record);
      if (intent === "load-update") {
        motorWorkflow = markLoaded(motorWorkflow);
        applyWorkflow("motor", motorFields, motorWorkflow, motorSubmit);
        setStatus(`Motor policy ${policyNumber} loaded for update.`, "success");
      } else {
        setStatus(`Motor policy ${policyNumber} loaded.`, "success");
      }
      return;
    }

    if (intent === "submit-update") {
      record = await request(
        "PUT",
        `/api/motor-policies/${encodeURIComponent(policyNumber)}`,
        values(motorForm, motorFields.filter((field) => field !== "policy_number")),
      );
      populate("motor", record);
      renderResult(motorResult, record);
      setStatus(`Motor policy ${policyNumber} updated.`, "success");
      return;
    }

    record = await request("DELETE", url);
    renderResult(motorResult, record);
    for (const field of motorFields) requireElement(`#motor-${field}`).value = "";
    setStatus(`Motor policy ${policyNumber} deleted.`, "success");
  } catch (error) {
    setStatus(`Motor policy task failed: ${error.message}`, "error");
  } finally {
    motorSubmit.disabled = false;
  }
});

function handleReset(form, result, operation, prefix, fields, submit, setWorkflow) {
  form.addEventListener("reset", () => {
    setTimeout(() => {
      result.replaceChildren();
      setStatus("");
      const workflow = createWorkflow(prefix, operation.value);
      setWorkflow(workflow);
      applyWorkflow(prefix, fields, workflow, submit);
    }, 0);
  });
}

handleReset(
  customerForm, customerResult, customerOperation, "customer", customerFields,
  customerSubmit, (workflow) => { customerWorkflow = workflow; },
);
handleReset(
  motorForm, motorResult, motorOperation, "motor", motorFields,
  motorSubmit, (workflow) => { motorWorkflow = workflow; },
);

applyWorkflow("customer", customerFields, customerWorkflow, customerSubmit);
applyWorkflow("motor", motorFields, motorWorkflow, motorSubmit);
setStatus("Ready. Use the invented identifiers CUST000001 and POL001 with customer CUST000001 to inquire.", "success");
