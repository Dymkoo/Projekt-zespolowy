from fastapi import FastAPI, HTTPException

app = FastAPI()
full_names = []

@app.get("/")
def root():
    return {"Hello": "World"}

@app.post("/personal-data")
def create_name(full_name: str):
    full_names.append(full_name)
    return full_names

@app.get("/personal-data")
def list_names(limit: int = 10):
    return full_names[0:limit]

@app.get("/personal-data/{personal_id}")
def get_name(name_id: int) -> str:
    if name_id < len(full_names):
        return full_names[name_id]
    else:
        raise HTTPException(status_code=404, detail="Person not found")