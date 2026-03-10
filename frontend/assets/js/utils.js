function createRoadCard(name){

const div = document.createElement("div")

div.className = "road-card"

div.innerHTML = `

<h3>${name}</h3>

<img class="road-video">

<div class="stats">

<div>🚗 Car: <span class="count-car">0</span></div>

<div>🏍 Motor: <span class="count-motor">0</span></div>

<div>⚡ Speed: <span class="speed">0</span></div>

<div class="status">Loading...</div>

</div>

`

return div

}