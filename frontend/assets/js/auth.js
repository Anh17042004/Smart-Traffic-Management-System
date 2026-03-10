async function requireAuth(){

    const res = await fetch(
        "http://localhost:8000/api/v1/auth/me",
        {
            credentials: "include"
        }
    )

    if(!res.ok){

        window.location.href="/"

        return

    }

    return await res.json()
}