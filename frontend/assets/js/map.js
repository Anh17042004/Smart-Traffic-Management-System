const map = L.map('map').setView([21.0285,105.8542], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
async function loadRoads(){
  const res = await fetch("http://localhost:8000/api/v1/roads")
  const data = await res.json()
  data.roads.forEach(r=>{
    const marker = L.marker([r.lat,r.lng]).addTo(map)
    marker.bindPopup(`
      <h3>${r.name}</h3>
      <p>Status: ${r.status}</p>
    `)
  })
}
loadRoads()