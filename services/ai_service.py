import os
import json
from PIL import Image
import io
from config.settings import settings_manager

class AIService:
    def __init__(self):
        self._gemini_initialized = False
        self._openai_client = None

    def _init_gemini(self):
        api_key = settings_manager.get("api_key")
        if api_key:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._gemini_initialized = True

    def _init_openai(self) -> bool:
        api_key = settings_manager.get("api_key")
        base_url = settings_manager.get("openai_base_url", "https://api.openai.com/v1")
        if api_key:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=api_key, base_url=base_url)
            return True
        return False

    def get_system_prompt(self, target_lang: str) -> str:
        return f"""Bạn là một trợ lý dịch thuật chuyên nghiệp, thông minh và có kiến thức sâu rộng về ngôn ngữ.
Nhiệm vụ của bạn là dịch văn bản được cung cấp sang ngôn ngữ '{target_lang}'.

Yêu cầu xuất ra kết quả dịch dưới định dạng JSON với cấu trúc chính xác như sau:
{{
  "detected_lang": "Tên ngôn ngữ gốc được phát hiện (ví dụ: English, Japanese, French...)",
  "translated_text": "Bản dịch chính thức phù hợp ngữ cảnh, tự nhiên và mượt mà nhất",
  "phonetic": "Phiên âm IPA (International Phonetic Alphabet) hoặc phiên âm quốc tế giúp phát âm (chỉ áp dụng nếu là từ đơn hoặc cụm từ cực ngắn, nếu là câu dài thì để trống '')",
  "explanation": "Giải thích nghĩa từ, loại từ (danh từ, động từ...), phân tích cấu trúc ngữ pháp quan trọng trong câu, hoặc gợi ý ngữ cảnh sử dụng phù hợp",
  "synonyms": ["Từ đồng nghĩa 1", "Từ đồng nghĩa 2", "Từ đồng nghĩa 3"] (liệt kê các từ/cụm từ đồng nghĩa phổ biến, nếu là câu dài thì để mảng rỗng []) ,
  "examples": [
    {{"original": "Câu ví dụ gốc chứa từ/cụm từ đó", "translated": "Bản dịch câu ví dụ"}}
  ] (cung cấp 2 ví dụ thực tế sử dụng từ/cụm từ này, đối với câu dài thì có thể đặt ví dụ minh họa cách viết câu tương tự)
}}

Lưu ý quan trọng:
1. Đảm bảo phản hồi chỉ chứa một chuỗi JSON hợp lệ, không bọc trong ```json và ```, không có văn bản thừa trước hoặc sau JSON.
2. Bản dịch phải tự nhiên và dịch đúng thuật ngữ chuyên ngành (nếu có).
"""

    def translate(self, text: str, source_lang: str = "Auto", target_lang: str = "Vietnamese") -> dict:
        """Dịch đoạn văn bản bằng AI và trả về kết quả dạng JSON."""
        provider = settings_manager.get("provider", "gemini")
        
        # Nếu không có API Key, trả về thông báo yêu cầu cấu hình
        if not settings_manager.get("api_key"):
            return self._get_error_response("Vui lòng cấu hình API Key trong Dashboard cài đặt để sử dụng dịch vụ dịch AI.")

        if provider == "gemini":
            return self._translate_gemini(text, source_lang, target_lang)
        elif provider == "openai":
            return self._translate_openai(text, source_lang, target_lang)
        else:
            return self._get_error_response(f"Không hỗ trợ nhà cung cấp dịch vụ '{provider}'")

    def translate_image(self, pil_image: Image.Image, target_lang: str = "Vietnamese") -> dict:
        """Nhận diện chữ trong ảnh (OCR) và dịch trực tiếp bằng Gemini API (Multimodal)."""
        provider = settings_manager.get("provider", "gemini")
        if provider != "gemini":
            return self._get_error_response("Tính năng dịch hình ảnh trực tiếp qua AI hiện tại chỉ hỗ trợ với Gemini.")
        
        if not settings_manager.get("api_key"):
            return self._get_error_response("Vui lòng cấu hình API Key trong Dashboard cài đặt để dịch hình ảnh.")

        try:
            self._init_gemini()
            import google.generativeai as genai
            
            model_name = settings_manager.get("gemini_model", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            
            # Chuyển đổi PIL Image sang bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            image_part = {
                "mime_type": "image/png",
                "data": img_bytes
            }
            
            system_prompt = self.get_system_prompt(target_lang)
            prompt = "Hãy nhận diện toàn bộ chữ có trong bức ảnh này, trích xuất nó, dịch nó và trả về JSON theo yêu cầu hệ thống."
            
            response = model.generate_content([
                system_prompt,
                image_part,
                prompt
            ])
            
            return self._parse_json_response(response.text)
        except Exception as e:
            return self._get_error_response(f"Lỗi khi dịch hình ảnh bằng Gemini: {str(e)}")

    def _translate_gemini(self, text: str, source_lang: str, target_lang: str) -> dict:
        try:
            self._init_gemini()
            import google.generativeai as genai
            
            model_name = settings_manager.get("gemini_model", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            
            system_prompt = self.get_system_prompt(target_lang)
            prompt = f"Ngôn ngữ nguồn yêu cầu: {source_lang}. Hãy dịch văn bản sau: {text}"
            
            # Sử dụng JSON schema mode nếu được hỗ trợ để đảm bảo cấu trúc
            response = model.generate_content(
                [system_prompt, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            return self._parse_json_response(response.text)
        except Exception as e:
            return self._get_error_response(f"Lỗi kết nối Gemini API: {str(e)}")

    def _translate_openai(self, text: str, source_lang: str, target_lang: str) -> dict:
        try:
            if not self._init_openai():
                return self._get_error_response("Không thể khởi tạo OpenAI client. Vui lòng kiểm tra API Key.")
                
            model_name = settings_manager.get("openai_model", "gpt-4o-mini")
            system_prompt = self.get_system_prompt(target_lang)
            prompt = f"Ngôn ngữ nguồn yêu cầu: {source_lang}. Hãy dịch văn bản sau: {text}"
            
            response = self._openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return self._parse_json_response(response.choices[0].message.content)
        except Exception as e:
            return self._get_error_response(f"Lỗi kết nối OpenAI API: {str(e)}")

    def _parse_json_response(self, raw_text: str) -> dict:
        """Phân tích chuỗi JSON trả về từ AI một cách an toàn."""
        clean_text = raw_text.strip()
        # Loại bỏ các markdown block ```json và ``` nếu AI tự động chèn vào bất kể hệ thống nhắc nhở
        if clean_text.startswith("```"):
            lines = clean_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_text = "\n".join(lines).strip()
            
        try:
            return json.loads(clean_text)
        except Exception as e:
            # Fallback nếu JSON bị lỗi cú pháp
            return {
                "detected_lang": "Unknown",
                "translated_text": raw_text, # Trả về text thô làm bản dịch tạm thời
                "phonetic": "",
                "explanation": f"Lỗi phân tích cú pháp JSON của AI: {str(e)}",
                "synonyms": [],
                "examples": []
            }

    def _get_error_response(self, error_message: str) -> dict:
        return {
            "detected_lang": "N/A",
            "translated_text": "LỖI DỊCH THUẬT",
            "phonetic": "",
            "explanation": error_message,
            "synonyms": [],
            "examples": []
        }

# Instance toàn cục của AIService
ai_service = AIService()
