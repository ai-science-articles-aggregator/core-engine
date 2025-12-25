from fastapi import APIRouter, Request, Depends, File, UploadFile, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from domain.schemas import ForwardRequest, ForwardResponse
from services import SummarizationService

# TODO(delete): Удалить после сдачи чекпоинта, для моделей будет отдельный микросервис

router = APIRouter(prefix="/forward", tags=["forward"])

def get_ml_service(request: Request) -> SummarizationService:
    return request.app.state.ml_service

@router.post('/')
async def forward(
    request: Request,
    service: SummarizationService = Depends(get_ml_service),

    image: Optional[UploadFile] = File(None),
    x_text: Optional[str] = Header(None, alias="X-Text"),
    x_max_length: Optional[int] = Header(None, alias="X-Max-Length"),
    x_min_length: Optional[int] = Header(None, alias="X-Min-Length") 
):
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        if not image:
            raise HTTPException(status_code=400, detail="bad request")
        
        if not x_text:
            raise HTTPException(status_code=400, detail="bad request")

        image_bytes = await image.read()
        
        summary, img_b64 = service.generate_image_summary(
            image_bytes,
            text=x_text,
            max_length=x_max_length or 512,
            min_length=x_min_length or 100
        )
        
        if summary is None:
            raise HTTPException(status_code=403, detail="модель не смогла обработать данные")
        return {"summary": summary, "image": img_b64}
    elif "application/json" in content_type:
        try:
            data = await request.json()
            req_data = ForwardRequest(**data)
            
            result = service.generate_summary(
                req_data.text, 
                req_data.max_length, 
                req_data.min_length
            )
            
            if result is None:
                raise HTTPException(status_code=403, detail="модель не смогла обработать данные")
            
            return ForwardResponse(summary=result)
        except Exception:
            raise HTTPException(status_code=400, detail="bad request")

    raise HTTPException(status_code=400, detail="bad request")
