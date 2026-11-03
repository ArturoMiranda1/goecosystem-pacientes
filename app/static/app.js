const $ = (id) => document.getElementById(id);

let token = sessionStorage.getItem("access_token");
let page = 1;
let editingId = null;
let loading = false;
const pageSize = 20;
let filters = {};

let messageTimeout = null;

function showMessage(text, error = false) {
  clearTimeout(messageTimeout);

  const element = $("message");
  element.textContent = text;
  element.className = error ? "error" : "success";
  element.hidden = false;

  if (!error) {
    messageTimeout = setTimeout(() => {
      element.hidden = true;
      element.textContent = "";
      messageTimeout = null;
    }, 5000);
  }
}

function showLogin() {
  $("login-view").hidden = false;
  $("app-view").hidden = true;
  $("logout").hidden = true;

  if ($("patient-dialog").open) {
    $("patient-dialog").close();
  }
}

function logout() {
  token = null;
  sessionStorage.removeItem("access_token");
  $("login-form").reset();
  $("patients-body").replaceChildren();
  $("dashboard").replaceChildren();
  showLogin();
}

function errorText(body) {
  if (Array.isArray(body.detail)) {
    return body.detail.map((error) => {
      const field = error.loc.slice(1).join(".");
      return `${field}: ${error.msg}`;
    }).join(" · ");
  }

  return typeof body.detail === "string"
    ? body.detail
    : "No se pudo completar la operación.";
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body) {
    headers.set("Content-Type", "application/json");
  }

  let response;

  try {
    response = await fetch(path, { ...options, headers });
  } catch {
    throw new Error("No se pudo conectar con el servidor.");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));

    if (response.status === 401 && path !== "/auth/login") {
      logout();
      throw new Error("Tu sesión terminó. Inicia sesión nuevamente.");
    }

    throw new Error(errorText(body));
  }

  return response.status === 204 ? null : response.json();
}

async function loadDashboard() {
  const data = await api("/dashboard");

  const metrics = [
    ["Registrados", data.total_patients],
    ["Pendientes", data.pending_patients],
    ["En atención", data.in_care_patients],
    ["Atendidos", data.attended_patients],
    ["Prioridad alta", data.high_priority_patients],
  ];

  $("dashboard").replaceChildren();

  for (const [label, value] of metrics) {
    const card = document.createElement("article");
    card.className = "metric";

    const title = document.createElement("span");
    title.textContent = label;

    const number = document.createElement("strong");
    number.textContent = value;

    card.append(title, number);
    $("dashboard").append(card);
  }
}

async function loadEPS() {
  const items = await api("/catalogs/eps");
  $("eps-select").replaceChildren();

  for (const eps of items) {
    const option = document.createElement("option");
    option.value = eps.code;
    option.textContent = eps.name;
    $("eps-select").append(option);
  }
}

function addCell(row, text) {
  const cell = document.createElement("td");
  cell.textContent = text;
  row.append(cell);
  return cell;
}

function renderPatients(items) {
  const body = $("patients-body");
  body.replaceChildren();

  if (!items.length) {
    const row = document.createElement("tr");
    const cell = addCell(row, "No se encontraron pacientes.");
    cell.colSpan = 6;
    body.append(row);
    return;
  }

  for (const patient of items) {
    const row = document.createElement("tr");

    addCell(row, patient.full_name);
    addCell(row, `${patient.document_type} ${patient.document}`);
    addCell(row, patient.eps.name);

    const priorityCell = addCell(row, "");
    const badge = document.createElement("span");
    const color = { Alta: "high", Media: "medium", Baja: "low" };
    badge.className = `badge ${color[patient.priority] || ""}`;
    badge.textContent = patient.priority;
    priorityCell.append(badge);

    addCell(row, patient.status);

    const actionsCell = addCell(row, "");
    const actions = document.createElement("div");
    actions.className = "actions";

    const edit = document.createElement("button");
    edit.textContent = "Editar";
    edit.className = "secondary";
    edit.addEventListener("click", () => openEditor(patient.id));

    const remove = document.createElement("button");
    remove.textContent = "Eliminar";
    remove.className = "danger";
    remove.addEventListener("click", () => deletePatient(patient, remove));

    actions.append(edit, remove);
    actionsCell.append(actions);
    body.append(row);
  }
}

async function loadPatients() {
  loading = true;
  $("previous").disabled = true;
  $("next").disabled = true;

  try {
    const params = new URLSearchParams({
      ...filters,
      page: String(page),
      page_size: String(pageSize),
    });

    let data = await api(`/patients?${params}`);
    const lastPage = Math.max(1, Math.ceil(data.total / pageSize));

    // Si se eliminó el último registro de una página, retrocede.
    if (page > lastPage) {
      page = lastPage;
      params.set("page", String(page));
      data = await api(`/patients?${params}`);
    }

    renderPatients(data.items);
    $("page-info").textContent =
      `${data.total} pacientes · Página ${page} de ${lastPage}`;

    $("previous").disabled = page <= 1;
    $("next").disabled = page >= lastPage;
  } finally {
    loading = false;
  }
}

async function refreshData() {
  await loadDashboard();
  await loadPatients();
}

async function startApp() {
  const user = await api("/auth/me");
  await loadEPS();
  await refreshData();

  $("welcome").textContent = `Bienvenido, ${user.full_name}`;
  $("login-view").hidden = true;
  $("app-view").hidden = false;
  $("logout").hidden = false;
}

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  $("message").hidden = true;

  try {
    const credentials = Object.fromEntries(
      new FormData(event.currentTarget)
    );

    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });

    token = result.access_token;
    sessionStorage.setItem("access_token", token);
    page = 1;
    filters = {};
    $("filter-form").reset();
    await startApp();
    $("login-form").reset();
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("logout").addEventListener("click", () => {
  logout();
  $("message").hidden = true;
});

$("filter-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (loading) return;

  filters = {};
  if ($("search").value.trim()) filters.search = $("search").value.trim();
  if ($("status-filter").value) filters.status = $("status-filter").value;
  if ($("priority-filter").value) filters.priority = $("priority-filter").value;
  page = 1;

  try {
    await loadPatients();
  } catch (error) {
    showMessage(error.message, true);
  }
});

$("clear-filters").addEventListener("click", () => {
  if (loading) return;
  $("filter-form").reset();
  $("filter-form").requestSubmit();
});

async function changePage(delta) {
  if (loading) return;
  const previousPage = page;
  page += delta;

  try {
    await loadPatients();
  } catch (error) {
    page = previousPage;
    showMessage(error.message, true);
  }
}

$("previous").addEventListener("click", () => changePage(-1));
$("next").addEventListener("click", () => changePage(1));

function prepareForm() {
  $("patient-form").reset();
  $("form-error").hidden = true;

  const today = new Date();
  const localDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");

  $("patient-form").elements.namedItem("birth_date").max = localDate;
}

$("new-patient").addEventListener("click", () => {
  editingId = null;
  prepareForm();
  $("dialog-title").textContent = "Registrar paciente";
  $("patient-dialog").showModal();
});

async function openEditor(id) {
  try {
    const patient = await api(`/patients/${id}`);
    prepareForm();

    for (const element of $("patient-form").elements) {
      if (element.name && Object.hasOwn(patient, element.name)) {
        element.value = patient[element.name] ?? "";
      }
    }

    editingId = id;
    $("dialog-title").textContent = "Editar paciente";
    $("patient-dialog").showModal();
  } catch (error) {
    showMessage(error.message, true);
  }
}

$("cancel-dialog").addEventListener("click", () => {
  $("patient-dialog").close();
});

$("patient-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("save-patient").disabled = true;
  $("form-error").hidden = true;

  try {
    const data = Object.fromEntries(new FormData(event.currentTarget));
    data.email = data.email.trim() || null;
    data.city = data.city.trim() || null;

    const updating = editingId !== null;

    await api(updating ? `/patients/${editingId}` : "/patients", {
      method: updating ? "PUT" : "POST",
      body: JSON.stringify(data),
    });

    $("patient-dialog").close();
    showMessage(updating ? "Paciente actualizado." : "Paciente registrado.");

    // El guardado ya terminó. Un fallo al refrescar no debe invitar
    // a reenviar el formulario y crear un duplicado.
    try {
      await refreshData();
    } catch (error) {
      showMessage(
        `El paciente se guardó, pero no se pudo actualizar la vista: ${error.message}`,
        true
      );
    }
  } catch (error) {
    if ($("patient-dialog").open) {
      $("form-error").textContent = error.message;
      $("form-error").hidden = false;
    } else {
      showMessage(error.message, true);
    }
  } finally {
    $("save-patient").disabled = false;
  }
});

async function deletePatient(patient, button) {
  if (!confirm(`¿Eliminar a ${patient.full_name}? Esta acción es permanente.`)) {
    return;
  }

  button.disabled = true;

  try {
    await api(`/patients/${patient.id}`, { method: "DELETE" });
    showMessage("Paciente eliminado.");

    try {
      await refreshData();
    } catch (error) {
      showMessage(
        `El paciente fue eliminado, pero no se pudo actualizar la vista: ${error.message}`,
        true
      );
    }
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
}

if (token) {
  startApp().catch((error) => {
    showLogin();
    showMessage(error.message, true);
  });
}