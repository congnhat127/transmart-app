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

        # Ánh xạ ngôn ngữ của TransMart sang mã ngôn ngữ Google Translate Web API
        lang_map = {
            "Auto": "auto",
            "Vietnamese": "vi",
            "English": "en",
            "Japanese": "ja",
            "Korean": "ko",
            "Chinese": "zh-CN",
            "French": "fr",
            "German": "de",
            "Russian": "ru",
            "Spanish": "es"
        }

        try:
            if provider == "google":
                import requests
                src_code = lang_map.get(source_lang, "auto")
                tgt_code = lang_map.get(target_lang, "vi")
                
                url = "https://translate.googleapis.com/translate_a/single"
                params = {
                    "client": "gtx",
                    "sl": src_code,
                    "tl": tgt_code,
                    "dt": "t",
                    "q": text
                }
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                r = requests.get(url, params=params, headers=headers, timeout=10)
                r.raise_for_status()
                data = r.json()
                
                translated_sentences = []
                for sentence in data[0]:
                    if sentence and sentence[0]:
                        translated_sentences.append(sentence[0])
                translation = "".join(translated_sentences)
                
                detected = data[2] if len(data) > 2 else "unknown"
                
                return {
                    "translation": translation,
                    "explanation": "Dịch bởi Google Dịch.",
                    "summary": "",
                    "detected_lang": detected
                }
                
            elif provider == "dictionary":
                import requests
                from urllib.parse import quote
                
                clean_text = text.strip()
                words = clean_text.split()
                
                # Dictionary chỉ hoạt động tốt nhất cho 1-3 từ tiếng Anh
                if len(words) <= 3:
                    try:
                        encoded_word = quote(clean_text)
                        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{encoded_word}"
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                        }
                        r = requests.get(url, headers=headers, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            if isinstance(data, list) and len(data) > 0:
                                entry = data[0]
                                word = entry.get("word", clean_text)
                                phonetic = entry.get("phonetic", "")
                                if not phonetic and entry.get("phonetics"):
                                    for ph in entry.get("phonetics"):
                                        if ph.get("text"):
                                            phonetic = ph.get("text")
                                            break
                                
                                meanings_list = []
                                first_def = ""
                                for m in entry.get("meanings", []):
                                    pos = m.get("partOfSpeech", "")
                                    defs = []
                                    for d in m.get("definitions", []):
                                        definition = d.get("definition", "")
                                        example = d.get("example", "")
                                        if definition:
                                            if not first_def:
                                                first_def = f"[{pos}] {definition}"
                                            if example:
                                                defs.append(f"- {definition}\n  *Ví dụ: {example}*")
                                            else:
                                                defs.append(f"- {definition}")
                                    if defs:
                                        meanings_list.append(f"📌 <b>{pos.upper()}</b>:<br>" + "<br>".join(defs))
                                        
                                explanation = "<br><br>".join(meanings_list)
                                phonetic_str = f" {phonetic}" if phonetic else ""
                                
                                return {
                                    "translation": f"<b>{word}</b>{phonetic_str}<br>{first_def}",
                                    "explanation": explanation,
                                    "summary": "Tra cứu từ điển Anh-Anh thành công.",
                                    "detected_lang": "en"
                                }
                    except Exception as dict_err:
                        print(f"[AIService] Lỗi gọi Free Dictionary API: {dict_err}")
                
                # Fallback sang Google Translate nếu là câu dài hoặc tra cứu từ điển thất bại
                src_code = lang_map.get(source_lang, "auto")
                tgt_code = lang_map.get(target_lang, "vi")
                
                url = "https://translate.googleapis.com/translate_a/single"
                params = {
                    "client": "gtx",
                    "sl": src_code,
                    "tl": tgt_code,
                    "dt": "t",
                    "q": text
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                r = requests.get(url, params=params, headers=headers, timeout=10)
                r.raise_for_status()
                data = r.json()
                
                translated_sentences = []
                for sentence in data[0]:
                    if sentence and sentence[0]:
                        translated_sentences.append(sentence[0])
                translation = "".join(translated_sentences)
                detected = data[2] if len(data) > 2 else "unknown"
                
                return {
                    "translation": translation,
                    "explanation": "Từ này không có trong từ điển Anh-Anh hoặc là một câu dài. Đã tự động dịch bằng Google Dịch.",
                    "summary": "Tự động chuyển hướng dịch thuật.",
                    "detected_lang": detected
                }
                
            elif provider == "gemini":
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

    def _ocr_image(self, image, settings: dict) -> str:
        """Sử dụng Gemini hoặc OpenAI để nhận diện chữ (transcribe) từ ảnh với lượng token tối thiểu."""
        gemini_key = settings.get("gemini_api_key", "").strip()
        openai_key = settings.get("openai_api_key", "").strip()
        
        prompt = "Transcribe the text from this image as accurately as possible. Preserve line breaks. Respond ONLY with the raw transcribed text. Do not add any introduction, explanation, formatting, or metadata."
        
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                model_name = settings.get("gemini_model", "gemini-1.5-flash")
                model = genai.GenerativeModel(model_name=model_name)
                response = model.generate_content([image, prompt])
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"[AIService] Lỗi OCR bằng Gemini: {e}")
                
        if openai_key:
            try:
                # Chuyển đổi Pillow image thành base64 PNG
                from io import BytesIO
                import base64
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                data_url = f"data:image/png;base64,{img_str}"
                
                openai_model = settings.get("openai_model", "gpt-4o-mini")
                base_url = settings.get("openai_base_url", "https://api.openai.com/v1").strip()
                client = OpenAI(api_key=openai_key, base_url=base_url if base_url else None)
                
                response = client.chat.completions.create(
                    model=openai_model,
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
                    temperature=0.1
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as e:
                print(f"[AIService] Lỗi OCR bằng OpenAI: {e}")
                
        raise Exception("Không thể thực hiện nhận dạng chữ. Vui lòng cấu hình ít nhất một API Key (Gemini hoặc OpenAI) hợp lệ trong phần Cài đặt.")

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
            if provider == "google":
                # 1. Thực hiện OCR lấy văn bản nguồn trước
                source_text = self._ocr_image(image, settings)
                if not source_text:
                    raise Exception("Không nhận diện được chữ nào trong vùng ảnh này.")
                
                # 2. Dịch văn bản đó bằng Google Translate
                translate_result = self.translate(source_text, source_lang="Auto", target_lang=target_lang)
                
                return {
                    "source_text": source_text,
                    "translation": translate_result.get("translation", ""),
                    "explanation": "Nhận diện chữ qua AI và dịch bằng Google Dịch (Miễn phí).",
                    "summary": "",
                    "detected_lang": translate_result.get("detected_lang", "unknown")
                }
                
            elif provider == "gemini":
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

    @staticmethod
    def fetch_gemini_models(api_key: str) -> list:
        """Tải danh sách mô hình từ Google Gemini API trực tuyến."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = []
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    name = m.name.replace("models/", "")
                    if "gemini" in name:
                        models.append(name)
            return sorted(list(set(models)))
        except Exception as e:
            print(f"[AIService] Lỗi fetch Gemini models: {e}")
            return []

    @staticmethod
    def fetch_openai_models(api_key: str, base_url: str = None) -> list:
        """Tải danh sách mô hình từ OpenAI API hoặc custom endpoint trực tuyến."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
            models_data = client.models.list()
            models = []
            is_custom = base_url and "api.openai.com" not in base_url
            for m in models_data.data:
                name = m.id
                if is_custom:
                    models.append(name)
                else:
                    if name.startswith("gpt-") or name.startswith("o1-") or name.startswith("o3-"):
                        models.append(name)
            return sorted(list(set(models)))
        except Exception as e:
            print(f"[AIService] Lỗi fetch OpenAI models: {e}")
            return []
