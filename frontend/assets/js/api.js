async function api(url,options={}){

    options.credentials="include"

    const res=await fetch(
        "http://localhost:8000/api/v1"+url,
        options
    )

    if(!res.ok){

        throw new Error("API error")

    }

    return res.json()

}