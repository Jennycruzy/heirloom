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

function values(form, fields, excluded = []) {
  const formData = new FormData(form);
  return Object.fromEntries(
    fields
      .filter((field) => !excluded.includes(field))
      .map((field) => [field, String(formData.get(field) ?? "")]),
  );
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

function updateFieldActivity(prefix, fields, operation, identifier) {
  const identifierOnly = operation === "inquire" || operation === "delete";
  for (const field of fields) {
    const input = requireElement(`#${prefix}-${field}`);
    const inactive = identifierOnly && field !== identifier;
    input.disabled = inactive;
    input.closest(".form-group").classList.toggle("field--inactive", inactive);
  }
}

customerOperation.addEventListener("change", () => {
  updateFieldActivity("customer", customerFields, customerOperation.value, "customer_number");
});
motorOperation.addEventListener("change", () => {
  updateFieldActivity("motor", motorFields, motorOperation.value, "policy_number");
});

customerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const operation = customerOperation.value;
  const identifier = requireElement("#customer-customer_number").value.trim();
  customerSubmit.disabled = true;
  try {
    if (!identifier) throw new Error("Customer number is required");
    let record;
    if (operation === "inquire") {
      record = await request("GET", `/api/customers/${encodeURIComponent(identifier)}`);
    } else if (operation === "add") {
      record = await request("POST", "/api/customers", values(customerForm, customerFields));
    } else {
      record = await request(
        "PUT",
        `/api/customers/${encodeURIComponent(identifier)}`,
        values(customerForm, customerFields, ["customer_number"]),
      );
    }
    populate("customer", record);
    renderResult(customerResult, record);
    const verb = operation === "add" ? "added" : operation === "update" ? "updated" : "loaded";
    setStatus(`Customer ${identifier} ${verb}.`, "success");
  } catch (error) {
    setStatus(`Customer task failed: ${error.message}`, "error");
  } finally {
    customerSubmit.disabled = false;
  }
});

motorForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const operation = motorOperation.value;
  const identifier = requireElement("#motor-policy_number").value.trim();
  motorSubmit.disabled = true;
  try {
    if (!identifier) throw new Error("Policy number is required");
    let record;
    if (operation === "inquire") {
      record = await request("GET", `/api/motor-policies/${encodeURIComponent(identifier)}`);
    } else if (operation === "add") {
      record = await request("POST", "/api/motor-policies", values(motorForm, motorFields));
    } else if (operation === "update") {
      record = await request(
        "PUT",
        `/api/motor-policies/${encodeURIComponent(identifier)}`,
        values(motorForm, motorFields, ["policy_number"]),
      );
    } else {
      record = await request("DELETE", `/api/motor-policies/${encodeURIComponent(identifier)}`);
    }
    renderResult(motorResult, record);
    if (operation === "delete") {
      for (const field of motorFields) requireElement(`#motor-${field}`).value = "";
    } else {
      populate("motor", record);
    }
    const verb = operation === "add" ? "added" : operation === "update" ? "updated" : operation === "delete" ? "deleted" : "loaded";
    setStatus(`Motor policy ${identifier} ${verb}.`, "success");
  } catch (error) {
    setStatus(`Motor policy task failed: ${error.message}`, "error");
  } finally {
    motorSubmit.disabled = false;
  }
});

function handleReset(form, result, operation, prefix, fields, identifier) {
  form.addEventListener("reset", () => {
    setTimeout(() => {
      result.replaceChildren();
      setStatus("");
      updateFieldActivity(prefix, fields, operation.value, identifier);
    }, 0);
  });
}

handleReset(customerForm, customerResult, customerOperation, "customer", customerFields, "customer_number");
handleReset(motorForm, motorResult, motorOperation, "motor", motorFields, "policy_number");
updateFieldActivity("customer", customerFields, customerOperation.value, "customer_number");
updateFieldActivity("motor", motorFields, motorOperation.value, "policy_number");
setStatus("Ready. Use the invented identifiers CUST000001 or POL001 to inquire.", "success");
