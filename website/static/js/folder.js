let fileData = {};

const requiredFiles = [
  'buses.csv', 'lines.csv', 'loads.csv',
  'loads-p_set.csv', 'loads-q_set.csv', 'transformers.csv',
  'transformer_types.csv', 'generators.csv',
  'generators-p_max_pu.csv', 'snapshots.csv', 'generators-p_set.csv'
];

document.getElementById("folderInput").addEventListener("change", function (event) {
  const files = Array.from(event.target.files);

  if (!files.every(f => f.name.endsWith('.csv'))) {
    alert("❌ Please upload only .csv files.");
    event.target.value = "";
    return;
  }

  const fileSelectorForm = document.getElementById("fileSelectorForm");
  fileSelectorForm.innerHTML = "";
  fileData = {};

  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      const lines = content.split("\n").map(line => line.split(","));
      fileData[file.name] = lines;

      // Create checkbox
      const label = document.createElement("label");
      label.className = "form-check-label";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "form-check-input me-1";
      checkbox.name = "csvSelection";
      checkbox.value = file.name;

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(" " + file.name));
      fileSelectorForm.appendChild(label);
    };
    reader.readAsText(file);
  });

  document.getElementById("fileSelection").style.display = "block";
});

function loadSelectedTables() {
  const selected = Array.from(document.querySelectorAll('input[name="csvSelection"]:checked')).map(cb => cb.value);

  const tablesDiv = document.getElementById("fileTables");
  tablesDiv.innerHTML = "";

  selected.forEach(fileName => {
    const lines = fileData[fileName];
    const tableContainer = document.createElement("div");
    tableContainer.className = "mb-4 p-2 bg-white rounded shadow-sm";

    const title = document.createElement("h5");
    title.textContent = fileName;
    tableContainer.appendChild(title);

    const table = document.createElement("table");
    table.id = fileName;
    table.className = "editable-table table table-sm table-bordered";

    lines.forEach((row, rowIndex) => {
      const tr = document.createElement("tr");
      row.forEach(cell => {
        const td = document.createElement(rowIndex === 0 ? "th" : "td");
        td.contentEditable = rowIndex !== 0;
        td.textContent = cell;
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });

    const btnGroup = document.createElement("div");
    btnGroup.className = "table-controls text-end mt-2";

    const actions = {
      "Insert Row": inserttablerow,
      "Delete Row": deletetablerow,
      "Insert Column": inserttablecolumn,
      "Delete Column": deletetablecolumn
    };

    const buttonTypes = {
      "Insert Row": "insert-btn",
      "Insert Column": "insert-btn",
      "Delete Row": "delete-btn",
      "Delete Column": "delete-btn"
    };

    Object.keys(actions).forEach(action => {
      const btn = document.createElement("button");
      btn.className = `btn btn-sm me-2 ${buttonTypes[action]}`;
      btn.textContent = action;
      btn.onclick = (e) => {
        e.preventDefault();
        actions[action](fileName);
      };
      btnGroup.appendChild(btn);
    });

    tableContainer.appendChild(btnGroup);
    tableContainer.appendChild(table);
    tablesDiv.appendChild(tableContainer);
  });
}

function inserttablerow(tableId) {
  const table = document.getElementById(tableId);
  const position = prompt("Enter row position (0 to " + (table.rows.length - 1) + "):", 0);
  const rowIndex = parseInt(position);

  if (!isNaN(rowIndex) && rowIndex >= 0 && rowIndex <= table.rows.length) {
    const newRow = table.insertRow(rowIndex);
    const colCount = table.rows[0].cells.length;

    for (let i = 0; i < colCount; i++) {
      const newCell = newRow.insertCell(i);
      newCell.contentEditable = true;
    }
    newRow.classList.add("new-row");
  } else {
    alert("Invalid row index.");
  }
}

function deletetablerow(tableId) {
  const table = document.getElementById(tableId);
  const rowIndex = prompt("Enter row position to delete (1 to " + (table.rows.length - 1) + "):", 1);

  if (!isNaN(rowIndex) && rowIndex > 0 && rowIndex < table.rows.length) {
    table.deleteRow(rowIndex);
  } else {
    alert("Invalid row index.");
  }
}

function inserttablecolumn(tableId) {
  const table = document.getElementById(tableId);
  const position = prompt("Enter column position (0 to " + (table.rows[0].cells.length - 1) + "):", 0);
  const colIndex = parseInt(position);

  if (!isNaN(colIndex) && colIndex >= 0 && colIndex <= table.rows[0].cells.length) {
    for (let i = 0; i < table.rows.length; i++) {
      const cell = table.rows[i].insertCell(colIndex);
      if (i === 0) {
        cell.outerHTML = "<th contenteditable='true'>NewCol</th>";
      } else {
        cell.contentEditable = true;
        cell.style.backgroundColor = "#f2f2f2";
      }
    }
  } else {
    alert("Invalid column index.");
  }
}

function deletetablecolumn(tableId) {
  const table = document.getElementById(tableId);
  const colIndex = prompt("Enter column position to delete (1 to " + (table.rows[0].cells.length - 1) + "):", 1);

  if (!isNaN(colIndex) && colIndex > 0 && colIndex < table.rows[0].cells.length) {
    for (let i = 0; i < table.rows.length; i++) {
      table.rows[i].deleteCell(colIndex);
    }
  } else {
    alert("Invalid column index.");
  }
}

function saveAllChanges() {
  Object.keys(fileData).forEach(fileName => {
    const table = document.getElementById(fileName);
    if (!table) return;  // skip unselected files

    const newData = [];
    for (let r = 0; r < table.rows.length; r++) {
      const row = [];
      for (let c = 0; c < table.rows[r].cells.length; c++) {
        row.push(table.rows[r].cells[c].textContent.trim());
      }
      newData.push(row);
    }
    fileData[fileName] = newData;
  });
  alert("✅ All changes saved locally (in memory).");
}

function uploadAllChanges() {
  saveAllChanges();

  const missing = requiredFiles.filter(name => !(name in fileData));
  if (missing.length > 0) {
    alert("❌ Missing, required files:\n" + missing.join("\n"));
    return;
  }

  const form = document.getElementById("uploadForm");
  form.innerHTML = "";

  for (const [fileName, data] of Object.entries(fileData)) {
    const content = data.map(row => row.join(",")).join("\n");
    const blob = new Blob([content], { type: "text/csv" });
    const fileInput = new File([blob], fileName, { type: "text/csv" });

    const dt = new DataTransfer();
    dt.items.add(fileInput);

    const input = document.createElement("input");
    input.type = "file";
    input.name = "csv_files";
    input.files = dt.files;
    form.appendChild(input);
  }

  form.submit();
}
function reloadFolder() {
  fetch("/reload-edited-folder")
    .then(res => {
      if (!res.ok) {
        return res.json().then(err => { throw err; });
      }
      return res.json();
    })
    .then(data => {
      fileData = data;

      const fileSelectorForm = document.getElementById("fileSelectorForm");
      fileSelectorForm.innerHTML = "";

      Object.keys(fileData).forEach(fileName => {
        const label = document.createElement("label");
        label.className = "form-check-label";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "form-check-input me-1";
        checkbox.name = "csvSelection";
        checkbox.value = fileName;

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(" " + fileName));
        fileSelectorForm.appendChild(label);
      });

      document.getElementById("fileSelection").style.display = "block";
      alert("✅ Previously uploaded folder reloaded. Select files to edit.");
    })
    .catch(error => {
      const errorMsg = error.error || error.message || "Unknown error";
      alert("❌ Failed to reload folder. Error: " + errorMsg);
    });
}
