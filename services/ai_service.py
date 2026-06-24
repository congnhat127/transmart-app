import json
import os
import base64
from io import BytesIO
import google.generativeai as genai
from openai import OpenAI

from config.settings import settings_manager

class AIService:
    """Kết nối với API Gemini hoặc OpenAI để thực hiện dịch thuật và xuất JSON."""
    
    def __init__(self):
        pass

    def translate(self, text: str, source_lang: str = "Auto", target_lang: str = "Vietnamese") -> dict:
        """
        Dịch đoạn văn bản bằng API Gemini hoặc OpenAI dựa trên cài đặt hiện tại.
        Trả về một dict chứa: translation, explanation, và detected_lang.
        """
        # Đọc các cấu hình mới nhất từ SettingsManager
        settings = settings_manager.load_settings()
        provider = settings.get("provider", "gemini")
        
        # Định nghĩa Prompt hệ thống yêu cầu phản hồi JSON nghiêm ngặt
        prompt = f"""You are a highly skilled professional translator and linguist.
Translate the following text into the target language.
You MUST respond ONLY with a valid JSON object matching the following structure:
{{
  "translation": "Only the translated text. Maintain formatting if applicable.",
  "explanation": "A very brief explanation (1-2 sentences) of any key vocabulary, idioms, grammar points, or cultural context from the source text (written in the target language). If the text is simple, this can be empty or a simple note.",
  "summary": "If the source text is long (more than 30 words), provide a 1-sentence summary of the main idea in the target language. Otherwise, leave it as an empty string.",
  "detected_lang": "The 2-letter ISO code of the detected source language (e.g., 'en', 'ja', 'ko', 'zh')."
}}

Target Language: {target_lang}
Source Language Hint: {source_lang} (If "Auto", automatically detect it)

Text to translate:
{text}
"""

        try:
            if provider == "gemini":
                api_key = settings.get("gemini_api_key", "").strip()
                if not api_key:
                    return {
                        "translation": "Chưa cấu hình Gemini API Key!",
                        "explanation": "Vui lòng mở bảng Cài đặt (biểu tượng bánh răng ⚙️) và nhập API Key của bạn để sử dụng dịch vụ.",
                        "detected_lang": "unknown"
                    }
                
                model_name = settings.get("gemini_model", "gemini-1.5-flash")
                
                # Cấu hình API cho Google Generative AI
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                response = model.generate_content(prompt)
                
                if not response or not response.text:
                    raise Exception("Không nhận được phản hồi từ Gemini API.")
                    
                result = json.loads(response.text.strip())
                return result
                
            else:  # openai
                api_key = settings.get("openai_api_key", "").strip()
                if not api_key:
                    return {
                        "translation": "Chưa cấu hình OpenAI API Key!",
                        "explanation": "Vui lòng mở bảng Cài đặt (biểu tượng bánh răng ⚙️) và nhập API Key của bạn để sử dụng dịch vụ.",
                        "detected_lang": "unknown"
                    }
                
                model_name = settings.get("openai_model", "gpt-4o-mini")
                base_url = settings.get("openai_base_url", "https://api.openai.com/v1").strip()
                
                # Khởi tạo OpenAI client
                client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise Exception("Không nhận được phản hồi từ OpenAI API.")
                    
                result = json.loads(content.strip())
                return result

        except Exception as e:
            print(f"[AIService] Lỗi dịch thuật: {e}")
            return {
                "translation": "Đã xảy ra lỗi khi kết nối với máy chủ AI.",
                "explanation": f"Chi tiết lỗi: {str(e)}\n\nVui lòng kiểm tra lại kết nối mạng hoặc tính hợp lệ của API Key.",
                "detected_lang": "unknown"
            }

    def translate_image(self, image, target_lang: str) -> dict:
        """
        Nhận diện văn bản trong ảnh (OCR) và dịch sang ngôn ngữ đích thông qua Gemini hoặc OpenAI.
        Trả về một dict chứa: source_text, translation, explanation, summary, và detected_lang.
        """
        settings = settings_manager.load_settings()
        provider = settings.get("provider", "gemini")
        
        prompt = f"""You are a professional OCR engine and language translator.
Analyze the provided image containing text. Perform the following steps:
1. Transcribe the text from the image as accurately as possible, preserving line breaks. This will be the "source_text".
2. Detect the source language.
3. Translate this text into the target language: {target_lang}.
4. Provide a brief explanation of any key words, idioms, grammar points, or cultural context from the source text (written in the target language).

You MUST respond ONLY with a valid JSON object matching the following structure:
{{
  "source_text": "The exact transcribed original text from the image",
  "translation": "Only the translated text. Maintain formatting if applicable.",
  "explanation": "A very brief explanation (1-2 sentences) of any key vocabulary, idioms, grammar points, or cultural context from the source text.",
  "summary": "If the source text is long (more than 30 words), provide a 1-sentence summary of the main idea in the target language. Otherwise, leave it as an empty string.",
  "detected_lang": "The 2-letter ISO code of the detected source language (e.g., 'en', 'ja', 'ko', 'zh')."
}}
"""

        try:
            if provider == "gemini":
                api_key = settings.get("gemini_api_key", "").strip()
                if not api_key:
                    return {
                        "source_text": "Chưa cấu hình Gemini API Key!",
                        "translation": "Chưa cấu hình Gemini API Key!",
                        "explanation": "Vui lòng mở bảng Cài đặt (biểu tượng bánh răng ⚙️) và nhập API Key của bạn để sử dụng dịch vụ.",
                        "detected_lang": "unknown"
                    }
                
                model_name = settings.get("gemini_model", "gemini-1.5-flash")
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # Gemini hỗ trợ truyền trực tiếp đối tượng PIL Image trong danh sách nội dung
                response = model.generate_content([image, prompt])
                
                if not response or not response.text:
                    raise Exception("Không nhận được phản hồi từ Gemini API.")
                    
                result = json.loads(response.text.strip())
                return result
                
            else:  # openai
                api_key = settings.get("openai_api_key", "").strip()
                if not api_key:
                    return {
                        "source_text": "Chưa cấu hình OpenAI API Key!",
                        "translation": "Chưa cấu hình OpenAI API Key!",
                        "explanation": "Vui lòng mở bảng Cài đặt (biểu tượng bánh răng ⚙️) và nhập API Key của bạn để sử dụng dịch vụ.",
                        "detected_lang": "unknown"
                    }
                
                model_name = settings.get("openai_model", "gpt-4o-mini")
                base_url = settings.get("openai_base_url", "https://api.openai.com/v1").strip()
                
                # Chuyển đổi Pillow image thành chuỗi base64 PNG data URL
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                data_url = f"data:image/png;base64,{img_str}"
                
                client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_url
                                    }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise Exception("Không nhận được phản hồi từ OpenAI API.")
                    
                result = json.loads(content.strip())
                return result

        except Exception as e:
            print(f"[AIService] Lỗi OCR dịch ảnh: {e}")
            return {
                "source_text": "Lỗi quét ảnh OCR",
                "translation": "Đã xảy ra lỗi khi kết nối với máy chủ AI.",
                "explanation": f"Chi tiết lỗi: {str(e)}\n\nVui lòng kiểm tra lại kết nối mạng hoặc tính hợp lệ của API Key.",
                "detected_lang": "unknown"
            }
