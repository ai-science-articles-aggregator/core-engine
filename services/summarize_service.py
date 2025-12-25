import torch
import base64
from transformers import LEDForConditionalGeneration, LEDTokenizer

# TODO(delete): Удалить после сдачи чекпоинта, для моделей будет отдельный микросервис

class SummarizationService:
    def __init__(self, model_path: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

    def load_model(self):
        print(f"Loading model to {self.device}...")

        self.tokenizer = LEDTokenizer.from_pretrained(self.model_path)
        self.model = LEDForConditionalGeneration.from_pretrained(
            self.model_path, 
            return_dict_in_generate=True,
            use_safetensors=True
        ).to(self.device)

        print("Model loaded.")

    def generate_summary(self, text: str, max_length: int, min_length: int) -> str:
        if not self.model:
            raise RuntimeError("Model is not loaded. Call load_model() first.")

        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids, 
                max_length=max_length,
                min_length=min_length
            )
        
        return self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)

    def generate_image_summary(self, image_bytes: bytes, text: str, max_length: int, min_length: int) -> tuple[str, str]:
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            summary = self.generate_summary(text, max_length, min_length)

            return summary, base64_image 
        except Exception:
            return None, None
