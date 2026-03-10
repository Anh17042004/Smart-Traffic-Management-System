function connectRoadWS(road,card){

const safeRoad = encodeURIComponent(road)

const wsFrame = new WebSocket(
`ws://localhost:8000/api/v1/ws/roads/${safeRoad}/frames`
)

wsFrame.binaryType = "blob"

wsFrame.onmessage = (event)=>{

const img = card.querySelector(".road-video")

const url = URL.createObjectURL(event.data)

img.onload = ()=>URL.revokeObjectURL(url)

img.src = url

}

const wsInfo = new WebSocket(
`ws://localhost:8000/api/v1/ws/roads/${safeRoad}/info`
)

wsInfo.onmessage = (event)=>{

const data = JSON.parse(event.data)

card.querySelector(".count-car")
.innerText = data.count_car || 0

card.querySelector(".count-motor")
.innerText = data.count_motor || 0

card.querySelector(".speed")
.innerText = (data.speed_car || 0) + " km/h"

card.querySelector(".status")
.innerText = data.density_status || "-"

}

}