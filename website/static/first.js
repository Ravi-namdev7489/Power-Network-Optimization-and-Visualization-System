$(document).ready(function () {
    $("#upload-form").on("submit", function (e) {
        e.preventDefault();
        let formData = new FormData(this);

        $.ajax({
            url: "/upload",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                alert("Files uploaded successfully!");
                loadCSVTables(response.files);
            },
            error: function () {
                alert("File upload failed.");
            }
        });
    });

    function loadCSVTables(files) {
        $("#csv-tables").empty();

        files.forEach(file => {
            $.get("/static/uploads/" + file, function (data) {
                Papa.parse(data, {
                    header: true,
                    dynamicTyping: true,
                    complete: function (results) {
                        let table = createTable(results.data);
                        $("#csv-tables").append(table);
                    }
                });
            });
        });
    }

    function createTable(data) {
        let table = $("<table class='table table-bordered table-striped'></table>");
        let thead = $("<thead><tr></tr></thead>");
        let tbody = $("<tbody></tbody>");

        let headers = Object.keys(data[0]);
        headers.forEach(header => {
            thead.find("tr").append(`<th>${header}</th>`);
        });

        data.forEach(row => {
            let tr = $("<tr></tr>");
            headers.forEach(header => {
                tr.append(`<td contenteditable="true">${row[header] || ""}</td>`);
            });
            tbody.append(tr);
        });

        table.append(thead).append(tbody);
        return table;
    }

    $("#save-csv").click(function () {
        let editedData = [];
        $("#csv-tables table tbody tr").each(function () {
            let row = {};
            $(this).find("td").each(function (index) {
                row[$("#csv-tables table thead th").eq(index).text()] = $(this).text();
            });
            editedData.push(row);
        });

        $.ajax({
            url: "/process_csv",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ data: editedData }),
            success: function (response) {
                alert(response.message);
            }
        });
    });
});
