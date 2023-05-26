var t1 = document.getElementById("table1");
var t2 = document.getElementById("table2");

var ram = navigator.deviceMemory;
var with_cong = document.getElementById("with_Congestion");
var APIURL = "http://localhost:5000/api/getall";
var url = "http://localhost:5500/scenario/scenario.html";

async function getData() {
	const data = await fetch(APIURL);
	const response = data.json();
	console.log(response);
}
window.onload = getData();
function scenario() {
	t1.style.marginLeft = "25%";
	t1.style.transitionDuration = "1s";
	t2.hidden = false;
	t2.style.marginLeft = "50%";
	t2.style.opacity = "1";
	t2.style.transitionDuration = "0.5s";
	document.getElementById("noSCC").disabled = true;
	document.getElementById("isSCC").checked = true;
	document.getElementById("new2").style.opacity = "0.3";
	document.getElementById("new2").style.transitionDuration = "1s";
	document
		.getElementById("new2")
		.setAttribute("title", "Calculation Must Be Strongly Connected");
	document.getElementById("click").style.visibility = "visible";
}

async function postData(event) {
	event.preventDefault();
	const cityName = document
		.getElementById("cityname")
		.value.toLowerCase()
		.replace(" ", "_");
	const scenarioURL = url + `?q=${cityName}`;
	window.location.href = scenarioURL;
}

document
	.getElementById("myForm")
	.addEventListener("submit", (e) => postData(e));
