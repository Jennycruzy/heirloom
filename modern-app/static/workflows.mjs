const IDENTIFIERS = {
  customer: ["customer_number"],
  motor: ["policy_number", "customer_number"],
};

export function createWorkflow(entity, operation) {
  if (!IDENTIFIERS[entity]) throw new Error(`Unknown workflow entity: ${entity}`);
  return { entity, operation, phase: operation === "update" ? "load" : "ready" };
}

export function markLoaded(workflow) {
  if (workflow.operation !== "update") return workflow;
  return { ...workflow, phase: "edit" };
}

export function enabledFields(workflow, fields) {
  const identifiers = IDENTIFIERS[workflow.entity];
  if (workflow.operation === "add") {
    const generated = workflow.entity === "customer" ? "customer_number" : "policy_number";
    return fields.filter((field) => field !== generated);
  }
  if (workflow.operation === "inquire" || workflow.operation === "delete") {
    return identifiers;
  }
  if (workflow.operation === "update" && workflow.phase === "load") {
    return identifiers;
  }
  if (workflow.operation === "update" && workflow.phase === "edit") {
    const immutable = workflow.entity === "customer" ? "customer_number" : "policy_number";
    return fields.filter((field) => field !== immutable);
  }
  return fields;
}

export function requestIntent(workflow) {
  if (workflow.operation === "update") {
    return workflow.phase === "load" ? "load-update" : "submit-update";
  }
  return workflow.operation;
}
