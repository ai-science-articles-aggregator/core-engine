from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel, Field

app = FastAPI()

class Data(BaseModel):
    name: str = None
    article: str = None

@app.post('/forward')
async def root(
    data: str = Form({}),
    file: UploadFile = File(None, description="Image file")
):

    return { 'file': file }