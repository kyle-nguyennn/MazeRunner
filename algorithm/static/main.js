var table = document.getElementById("arena");
var cellMovt;
var cellAni;

if (table != null) {
    for (var x = 0; x < table.rows.length; x++) {
        for (var y = 0; y < table.rows[x].cells.length; y++) {
            table.rows[x].cells[y].onclick = function () {
                updateCanvas(this);
            };
        }
    }
}

function updateCanvas(cell) {
    if (document.getElementById("optObstacle").checked) {
        cell.className = "obstacle";
    } else if (document.getElementById("optEmpty").checked) {
        cell.className = "empty";
    } else if (document.getElementById("optUnknown").checked) {
        cell.className = "unknown";
    }
}

function tableToArray() {
    if (table != null) {
        var mapArr = new Array(table.rows.length);
        for (var x = 0; x < table.rows.length; x++) {
            mapArr[x] = new Array(table.rows[x].cells.length);
            for (var y = 0; y < table.rows[x].cells.length; y++) {
                if (table.rows[x].cells[y].className == "empty") {
                    mapArr[x][y] = 0;
                } else if (table.rows[x].cells[y].className == "obstacle") {
                    mapArr[x][y] = 1;
                } else if (table.rows[x].cells[y].className == "unknown") {
                    mapArr[x][y] = -1;
                }
            }
        }
        return mapArr;
    }
    return null;
}

function drawCanvas(arena) {
    if (table != null) {
        for (var x = 0; x < table.rows.length; x++) {
            for (var y = 0; y < table.rows[x].cells.length; y++) {
                if (arena[x][y] == -1)
                    table.rows[x].cells[y].className = "unknown";
                else if (arena[x][y] == 0)
                    table.rows[x].cells[y].className = "empty";
                else if (arena[x][y] == 1)
                    table.rows[x].cells[y].className = "obstacle"
            }
        }
    }
}

function setFopVisible(visible) {
    var fop = document.getElementById("robot-fop");
    if (visible)
        fop.style.visibility = 'visible';
    else
        fop.style.visibility = 'hidden';
}

function moveRobot(actions) {
    clearInterval(cellMovt);
    clearInterval(cellAni);

    setFopVisible(true);

    var currentH = 661 - 100;
    var currentW = 0;
    var currentD = 0;
    var step = 0;

    setRobotPosition(currentH, currentW, currentD);

    cellMovt = setInterval(displayRobot, 500);

    function displayRobot() {
        if (step == actions.length) {
            clearInterval(cellMovt);
        }
        else {
            currentD = normalizeDirection(currentD);

            var posH = currentH;
            var posW = currentW;
            var posD = currentD;

            var action = actions.charAt(step);
            if (action == 'F') {
                if (currentD == 0)
                    posH = currentH - 33;
                else if (currentD == 90)
                    posW = currentW + 33;
                else if (currentD == 180)
                    posH = currentH + 33;
                else if (currentD == 270)
                    posW = currentW - 33;
            }
            else if (action == 'R')
                posD = currentD + 90;

            else if (action == 'L')
                posD = currentD - 90;

            cellAni = setInterval(animateRobot, 10);

            function animateRobot() {
                if (currentH == posH && currentW == posW && currentD == posD) {
                    clearInterval(cellAni);
                }
                else {
                    if (currentH < posH)
                        currentH++;
                    else if (currentH > posH)
                        currentH--;
                    else if (currentW < posW)
                        currentW++;
                    else if (currentW > posW)
                        currentW--;
                    else if (currentD < posD)
                        currentD += 3;
                    else if (currentD > posD)
                        currentD -= 3;

                    setRobotPosition(currentH, currentW, currentD);
                }
            }
            step++;
        }
    }
}

function setRobotPosition(h, w, d) {
    d = normalizeDirection(d);
    var elem = document.getElementById("robot");
    elem.style.top = h + 'px';
    elem.style.left = w + 'px';
    elem.style.transform = 'rotate(' + d + 'deg)';
}

function normalizeDirection(deg) {
    console.log(deg);
    if (deg < 0)
        deg += 360;
    else if (deg >= 360)
        deg -= 360;
    console.log(deg);
    return deg;
}


$(document).ready(function () {
    $("#btnLoadArena").click(function () {
        $.post("/desc_to_array", {
            part1: $("#mdfPart1").val(),
            part2: $("#mdfPart2").val()
        }, function (data, status) {
            drawCanvas(JSON.parse(data));
        });
    });

    $("#btnExportArena").click(function () {
        $.ajax({
            type: 'POST',
            data: JSON.stringify(tableToArray()),
            contentType: 'application/json',
            url: '/array_to_desc',
            success: function (data) {
                var obj = jQuery.parseJSON(data);
                document.getElementById("mdfPart1").value = obj.part1;
                document.getElementById("mdfPart2").value = obj.part2;
            }
        });
    });

    $("#btnFastesPath").click(function () {
        x = $("#waypointRow").val()
        y = $("#waypointCol").val()
        data = [tableToArray(), x, y];
        $.ajax({
            type: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            url: '/fastest_path',
            success: function (data) {
                var obj = jQuery.parseJSON(data);
                moveRobot(obj.instructions);
            }
        });
    });
});