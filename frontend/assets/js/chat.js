const input=document.getElementById("input")
const messages=document.getElementById("messages")
document.getElementById("send").onclick=async()=>{
  const text=input.value
  const res=await fetch("http://localhost:8000/api/v1/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:text})
  })
  const data=await res.json()
  messages.innerHTML+=`<div class="user">${text}</div>`
  messages.innerHTML+=`<div class="bot">${data.reply}</div>`
  input.value=""
}