var w = window.outerWidth;
var h = window.outerHeight;
var sidenav = document.getElementById("sidenav");
var menuBar = document.getElementById("menuBar");
var content = document.getElementById("content");
var opt = document.getElementsByClassName("Option");
var custom = document.getElementById("custom_content");
var close = document.getElementById("closeBtn").clientHeight;
var link = document.getElementById("other_city").clientHeight;
var mrgn = (h - close - link) / 4;
const APIURL = "https://backend-ifn.yankyhermawan.xyz/api/data";
sidenav.style.marginTop = "0px";
for (var i = 0; i < opt.length; i++) {
	opt[i].style.marginTop = mrgn / 15 + "px";
	opt[i].style.marginBottom = mrgn / 15 + "px";
}
async function colorChange() {
	var low = document.getElementById("low_color").value;
	var mid = document.getElementById("mid_color").value;
	var high = document.getElementById("high_color").value;
	const data = await getData();
	eval(data.data);
	document.getElementById("city").innerHTML = city;
	document.getElementById("country").innerHTML = country;
	document.getElementById("population").innerHTML = pop;
}
function sideNav() {
	sidenav.style.width = "200px";
	sidenav.style.marginRight = 0.01 * w + "px";
	menuBar.style.right = "225px";
	content.style.border = "1px solid #000000";
	content.style.opacity = "1";
	content.style.height = 0.98 * h + "px";
	content.style.marginTop = 0.01 * h + "px";
	content.style.marginBottom = 0.01 * h + "px";
	menuBar.style.display = "none";
	custom.style.display = "none";
}
function closeButton() {
	sidenav.style.width = "0px";
	menuBar.style.right = "25px";
	content.style.border = "none";
	content.style.opacity = "0";
	menuBar.style.display = "block";
	content.style.transitionDuration = "1s";
	custom.style.display = "none";
}

var scale = 1,
	panning = false,
	pointX = 0,
	pointY = 0,
	start = { x: 0, y: 0 },
	zoom = document.getElementById("zoom");

function setTransform() {
	zoom.style.transform =
		"translate(" + pointX + "px, " + pointY + "px) scale(" + scale + ")";
}

zoom.onmousedown = function (e) {
	e.preventDefault();
	start = { x: e.clientX - pointX, y: e.clientY - pointY };
	panning = true;
};

zoom.onmouseup = function (e) {
	panning = false;
};

zoom.onmousemove = function (e) {
	e.preventDefault();
	if (!panning) {
		return;
	}
	pointX = e.clientX - start.x;
	pointY = e.clientY - start.y;
	setTransform();
};

zoom.onwheel = function (e) {
	e.preventDefault();
	var xs = (e.clientX - pointX) / scale,
		ys = (e.clientY - pointY) / scale,
		delta = e.wheelDelta ? e.wheelDelta : -e.deltaY;
	delta > 0 ? (scale *= 1.2) : (scale /= 1.2);
	pointX = e.clientX - xs * scale;
	pointY = e.clientY - ys * scale;

	setTransform();
};

async function getData() {
	const params = new URLSearchParams(window.location.search);
	const cityName = params.get("q");

	const response = await fetch(APIURL, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			city: cityName,
			height: h,
			width: w,
		}),
	});
	const data = response.json();
	return data;
}

window.onload = colorChange();
