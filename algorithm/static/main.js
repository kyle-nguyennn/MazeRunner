var table = document.getElementById("arena");
var robot = document.getElementById("robot");
var mdfPart1 = document.getElementById("mdfPart1");
var mdfPart2 = document.getElementById("mdfPart2");
var mdfList = document.getElementById("mdfList");
var tabEditMode = document.getElementById("tabEditMode");
var tabSimMode = document.getElementById("tabSimMode");
var tabActualMode = document.getElementById("tabActualMode");
var editOptions = document.getElementById("editOptions");
var cardConnect = document.getElementById("cardConnect");
var cardArena = document.getElementById("cardArena");
var cardFastestPath = document.getElementById("cardFastestPath");
var cardExploration = document.getElementById("cardExploration");
var btnConnect = document.getElementById("btnConnect");
var btnDisconnect = document.getElementById("btnDisconnect");
var robotPosRow = document.getElementById("robotPosRow");
var robotPosCol = document.getElementById("robotPosCol");
var robotHead = document.getElementById("robotHead");
var robotSpeed = document.getElementById("robotSpeed");
var exploreTime = document.getElementById("exploreTime");
var errorRate = document.getElementById("errorRate");
var floatTable = document.getElementById("floatingArena");
var lblStatus = document.getElementById("lblStatus");
var floatTable = document.getElementById("floatingArena");

var cellMovt;
var cellAni;
var exploreStatusAni;

var arenaHeight = 694;
var cellSize = 33;
var robotSize = 100;

if (table != null) {
    for (var x = 0; x < table.rows.length; x++) {
        for (var y = 0; y < table.rows[x].cells.length; y++) {
            table.rows[x].cells[y].onclick = function () {
                updateCanvas(this);
            };
        }
    }
}
switchEditMode();
getMode();
moveRobot("");

mdfPart1.oninput = function () { mdfToArray(); };
mdfPart2.oninput = function () { mdfToArray(); };
mdfList.oninput = function () { loadFromList(); };
robotPosRow.oninput = function () { setRobotPosition(robotPosRow.value, robotPosCol.value, robotHead.value); };
robotPosCol.oninput = function () { setRobotPosition(robotPosRow.value, robotPosCol.value, robotHead.value); };
robotHead.oninput = function () { setRobotPosition(robotPosRow.value, robotPosCol.value, robotHead.value); };

function loadFromList() {
    var str = mdfList.options[mdfList.selectedIndex].text;
    var mdfParts = str.split("|");
    mdfPart1.value = mdfParts[0];
    mdfPart2.value = mdfParts[1];
    mdfToArray();
}


function updateCanvas(cell) {
    if (document.getElementById("optObstacle").checked) {
        cell.className = "obstacle";
    } else if (document.getElementById("optEmpty").checked) {
        cell.className = "empty";
    } else if (document.getElementById("optUnknown").checked) {
        cell.className = "unknown";
    }
    arrayToMdf();
}

function tableToArray() {
    if (table != null) {
        var mapArr = new Array(table.rows.length);
        for (var x = 0; x < table.rows.length - 1; x++) {
            mapArr[x] = new Array(table.rows[x].cells.length);
            for (var y = 1; y < table.rows[x].cells.length; y++) {
                if (table.rows[x].cells[y].className == "empty") {
                    mapArr[x][y - 1] = 0;
                } else if (table.rows[x].cells[y].className == "obstacle") {
                    mapArr[x][y - 1] = 1;
                } else if (table.rows[x].cells[y].className == "unknown") {
                    mapArr[x][y - 1] = -1;
                }
            }
        }
        return mapArr;
    }
    return null;
}

function drawCanvas(display, arena) {
    if (display != null) {
        for (var x = 0; x < display.rows.length - 1; x++) {
            for (var y = 1; y < display.rows[x].cells.length; y++) {
                if (arena[x][y - 1] == -1)
                    display.rows[x].cells[y].className = "unknown";
                else if (arena[x][y - 1] == 0)
                    display.rows[x].cells[y].className = "empty";
                else if (arena[x][y - 1] == 1)
                    display.rows[x].cells[y].className = "obstacle"
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

    var currentH = arenaHeight - cellSize - robotSize;
    var currentW = cellSize;
    var currentD = 0;
    var step = 0;

    setActualRobotPosition(currentH, currentW, currentD);

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
                    posH = currentH - cellSize;
                else if (currentD == 90)
                    posW = currentW + cellSize;
                else if (currentD == 180)
                    posH = currentH + cellSize;
                else if (currentD == 270)
                    posW = currentW - cellSize;
            }
            else if (action == 'B') {
                if (currentD == 0)
                    posH = currentH + cellSize;
                else if (currentD == 90)
                    posW = currentW - cellSize;
                else if (currentD == 180)
                    posH = currentH - cellSize;
                else if (currentD == 270)
                    posW = currentW + cellSize;
            }
            else if (action == 'R')
                posD = currentD + 90;

            else if (action == 'L')
                posD = currentD - 90;

            cellAni = setInterval(animateRobot, 8);

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

                    setActualRobotPosition(currentH, currentW, currentD);
                }
            }
            step++;
        }
    }
}

function updateExploreStatus() {

    clearInterval(exploreStatusAni);

    $.get("/get_explore_status", function (data, status) {
        if (data == "N") {
            clearInterval(exploreStatusAni);
            showSimControls();
            floatTable.style.visibility = 'hidden';
            return
        }

        hideSimControls();

        floatTable.style.visibility = 'visible';
        $.get("/get_original_arena", function (data, status) {
            var original = jQuery.parseJSON(data);
            drawCanvas(floatTable, original);
        });

        var refreshRate = robotSpeed.value * 500;
        exploreStatusAni = setInterval(getExploreStatus, refreshRate);
        function getExploreStatus() {
            $.get("/get_explore_status", function (data, status) {
                if (data == "N") {
                    clearInterval(exploreStatusAni);
                    showSimControls();
                    floatTable.style.visibility = 'hidden';
                }
                var obj = jQuery.parseJSON(data);
                var arena = obj[0];
                var robot = obj[1];
                var status = obj[2];
                lblStatus.textContent = "Robot Status: " + status;
                drawCanvas(table, arena);
                setRobotPosition(robot[0], robot[1], robot[2]);
            });
        }
    });
}

function setRobotPosition(h, w, d) {
    setActualRobotPosition(arenaHeight - (h * cellSize) - robotSize, cellSize * w, d);
}

function setActualRobotPosition(h, w, d) {
    d = normalizeDirection(d);
    robot.style.top = h + 'px';
    robot.style.left = w + 'px';
    robot.style.transform = 'rotate(' + d + 'deg)';
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

function saveArena() {
    $.post("/save_arena", {
        part1: mdfPart1.value,
        part2: mdfPart2.value
    }, function (data, status) {
        window.location.replace("/");
    });
}

function arrayToMdf() {
    $.ajax({
        type: 'POST',
        data: JSON.stringify(tableToArray()),
        contentType: 'application/json',
        url: '/array_to_mdf',
        success: function (data) {
            var obj = jQuery.parseJSON(data);
            mdfPart1.value = obj.part1;
            mdfPart2.value = obj.part2;
        }
    });
}

function mdfToArray() {
    $.post("/mdf_to_array", {
        part1: mdfPart1.value,
        part2: mdfPart2.value
    }, function (data, status) {
        drawCanvas(table, JSON.parse(data));
    });
}

function getMode() {
    $.get("/current_mode", function (data, status) {
        // btnConnect.style.visibility = 'visible';
        // btnDisconnect.style.visibility = 'hidden';
        if (data == 1) {
            switchSimMode();
        }
        else if (data == 2) {
            switchActualMode();
            // btnConnect.style.visibility = 'hidden';
            // btnDisconnect.style.visibility = 'visible';
        }
    });
}

function switchEditMode() {
    tabEditMode.className = "nav-link active";
    tabSimMode.className = "nav-link";
    tabActualMode.className = "nav-link";

    lblStatus.style.visibility = 'hidden';
    floatTable.style.visibility = 'hidden';

    showEditControls();
    hideSimControls();
    hideActualControls();

    clearInterval(exploreStatusAni);
    mdfToArray();
    setFopVisible(false);
}

function switchSimMode() {
    tabSimMode.className = "nav-link active";
    tabEditMode.className = "nav-link";
    tabActualMode.className = "nav-link";

    lblStatus.style.visibility = 'visible';
    floatTable.style.visibility = 'hidden';

    hideEditControls();
    showSimControls();
    hideActualControls();
    setFopVisible(true);

    updateExploreStatus();
}

function switchActualMode() {
    tabActualMode.className = "nav-link active";
    tabSimMode.className = "nav-link";
    tabEditMode.className = "nav-link";

    lblStatus.style.visibility = 'visible';
    floatTable.style.visibility = 'hidden';

    hideEditControls();
    hideSimControls();
    showActualControls();
    setFopVisible(true);

    updateExploreStatus();
}

function hideEditControls() {
    editOptions.style.visibility = 'hidden';
    cardArena.style.visibility = 'hidden';
    cardArena.style.position = 'absolute';
    cardArena.style.top = '0';
}

function hideSimControls() {
    cardExploration.style.visibility = 'hidden';
    cardFastestPath.style.visibility = 'hidden';
    cardExploration.style.position = 'absolute';
    cardFastestPath.style.position = 'absolute';
    cardExploration.style.top = '0';
    cardFastestPath.style.top = '0';
}

function hideActualControls() {
    cardConnect.style.visibility = 'hidden';
    cardConnect.style.position = 'absolute';
    cardConnect.style.top = '0';
}

function showEditControls() {
    editOptions.style.visibility = 'visible';
    cardArena.style.visibility = 'visible';
    cardArena.style.position = '';
}

function showSimControls() {
    cardExploration.style.visibility = 'visible';
    cardFastestPath.style.visibility = 'visible';
    cardExploration.style.position = '';
    cardFastestPath.style.position = '';
}

function showActualControls() {
    cardConnect.style.visibility = 'visible';
    cardConnect.style.position = '';
}


$(document).ready(function () {

    $('#tabEditMode').click(function (e) {
        e.preventDefault();
        switchEditMode();
        return false;
    });

    $('#tabSimMode').click(function (e) {
        e.preventDefault();
        switchSimMode();
        getMode();
        return false;
    });

    $('#tabActualMode').click(function (e) {
        e.preventDefault();
        switchActualMode();
        getMode();
        return false;
    });

    $("#btnLoadArena").click(function () {
        mdfToArray();
    });

    $("#btnExportArena").click(function () {
        arrayToMdf();
    });

    $("#btnSaveArena").click(function () {
        saveArena();
    });

    $("#btnConnect").click(function () {
        $.get("/connect_to_pi", function (data, status) {
        });
    });

    $("#btnDisconnect").click(function () {
        $.get("/disconnect_from_pi", function (data, status) {
        });
    });

    $("#btnFastestPath").click(function () {
        x = $("#waypointRow").val()
        y = $("#waypointCol").val()
        data = [tableToArray(), x, y];
        $.ajax({
            type: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            url: '/fastest_path_sim',
            success: function (data) {
                var obj = jQuery.parseJSON(data);
                switchSimMode();
                moveRobot(obj.instructions);
            }
        });
    });

    $("#btnExploration").click(function () {
        data = [tableToArray(), robotPosRow.value, robotPosCol.value, robotHead.value, robotSpeed.value, exploreTime.value, explorePercent.value, errorRate.value];
        $.ajax({
            type: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            url: '/exploration_sim',
            success: function (data) {
                switchSimMode();
            }
        });
    });

    $("#btnExploreStart").click(function () {
        $.get("/exploration_start", function (data, status) {
            switchActualMode();
        });
    });
});

$(function () {
    $("#floatingArena").draggable();
});