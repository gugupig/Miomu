from typing import List
from .base import G2PConverter

try:
    from transformers import T5ForConditionalGeneration, AutoTokenizer
    import torch
    CHARSIU_AVAILABLE = True
except ImportError:
    T5ForConditionalGeneration = None
    AutoTokenizer = None
    torch = None
    CHARSIU_AVAILABLE = False

class CharsiuG2P(G2PConverter):
    """
    基于 CharsiuG2P (ByT5) 的多语言 G2P 转换器
    支持 100 种语言的字素到音素转换
    使用 Hugging Face Transformers 和预训练的 ByT5 模型
    """
    
    def __init__(self, model_name: str = 'charsiu/g2p_multilingual_byT5_tiny_16_layers_100', language: str = 'eng-us'):
        """
        初始化 CharsiuG2P 转换器
        
        Args:
            model_name: 预训练模型名称，可选：
                       - 'charsiu/g2p_multilingual_byT5_tiny_8_layers_100'
                       - 'charsiu/g2p_multilingual_byT5_tiny_12_layers_100'
                       - 'charsiu/g2p_multilingual_byT5_tiny_16_layers_100' (默认)
                       - 'charsiu/g2p_multilingual_byT5_small_100'
            language: 语言代码，格式基于 ISO-639，例如：
                     - 'eng-us': 美式英语
                     - 'fra': 法语
                     - 'deu': 德语
                     - 'spa': 西班牙语
                     - 'cmn': 中文（普通话）
                     - 'jpn': 日语
                     - 'kor': 韩语
        """
        if not CHARSIU_AVAILABLE:
            raise ImportError(
                "CharsiuG2P dependencies not available. Please install: "
                "pip install transformers torch"
            )
        
        self.model_name = model_name
        self.language = language
        self.device = 'cuda' if torch and torch.cuda.is_available() else 'cpu'
        
        print(f"[CharsiuG2P] Initializing model: {model_name}")
        print(f"[CharsiuG2P] Language: {language}")
        print(f"[CharsiuG2P] Device: {self.device}")
        
        try:
            # 加载模型和分词器
            if not CHARSIU_AVAILABLE:
                raise ImportError("Dependencies not available")
            self.model = T5ForConditionalGeneration.from_pretrained(model_name)  # type: ignore
            self.tokenizer = AutoTokenizer.from_pretrained('google/byt5-small')  # type: ignore
            
            # 移动到设备
            self.model.to(self.device)
            self.model.eval()  # 设置为评估模式
            
            print(f"[CharsiuG2P] Model loaded successfully")
            
        except Exception as e:
            print(f"[CharsiuG2P] Failed to load model: {e}")
            print(f"💡 提示:")
            print(f"  • 首次使用需要下载模型，可能需要一些时间")
            print(f"  • 确保网络连接正常")
            print(f"  • 模型大小约几百MB，请确保存储空间充足")
            raise

    def convert(self, text: str) -> str:
        """
        转换单个文本字符串为音素
        
        Args:
            text: 输入文本（单词）
            
        Returns:
            IPA 音素字符串
        """
        if not text or not text.strip():
            return ""
        
        try:
            # 添加语言前缀（CharsiuG2P 要求的格式）
            formatted_text = f'<{self.language}>: {text.strip()}'
            
            # 分词
            inputs = self.tokenizer(
                [formatted_text], 
                padding=True, 
                add_special_tokens=False, 
                return_tensors='pt'
            )
            
            # 移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 生成预测
            with torch.no_grad():  # type: ignore
                preds = self.model.generate(
                    **inputs,
                    num_beams=1,  # 贪婪解码，文档建议不使用束搜索
                    max_length=50,
                    do_sample=False
                )
            
            # 解码结果
            phonemes = self.tokenizer.batch_decode(
                preds.tolist(), 
                skip_special_tokens=True
            )[0]
            
            return phonemes.strip()
            
        except Exception as e:
            print(f"[CharsiuG2P] Error converting '{text}': {e}")
            # 失败时返回原文本作为后备
            return text.strip()

    def batch_convert(self, texts: List[str]) -> List[str]:
        """
        批量转换文本列表为音素列表
        
        Args:
            texts: 输入文本列表
            
        Returns:
            IPA 音素字符串列表
        """
        if not texts:
            return []
        
        try:
            # 过滤空文本
            non_empty_texts = [text.strip() for text in texts if text.strip()]
            if not non_empty_texts:
                return [''] * len(texts)
            
            # 批量添加语言前缀
            formatted_texts = [f'<{self.language}>: {text}' for text in non_empty_texts]
            
            # 批量分词
            inputs = self.tokenizer(
                formatted_texts,
                padding=True,
                add_special_tokens=False,
                return_tensors='pt'
            )
            
            # 移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 批量生成预测
            with torch.no_grad():  # type: ignore
                preds = self.model.generate(
                    **inputs,
                    num_beams=1,
                    max_length=50,
                    do_sample=False
                )
            
            # 批量解码结果
            phonemes_list = self.tokenizer.batch_decode(
                preds.tolist(),
                skip_special_tokens=True
            )
            
            # 处理原始文本中的空白
            result = []
            non_empty_idx = 0
            for text in texts:
                if text.strip():
                    result.append(phonemes_list[non_empty_idx].strip())
                    non_empty_idx += 1
                else:
                    result.append('')
            
            return result
            
        except Exception as e:
            print(f"[CharsiuG2P] Error in batch conversion: {e}")
            # 失败时逐个转换作为后备
            return [self.convert(text) for text in texts]
    
    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言代码列表
        
        Returns:
            支持的语言代码列表（部分常用语言）
        """
        # CharsiuG2P 支持 100 种语言，这里列出一些常用的
        return [
            'eng-us',    # 美式英语
            'eng-uk',    # 英式英语
            'fra',       # 法语
            'deu',       # 德语
            'spa',       # 西班牙语
            'ita',       # 意大利语
            'por',       # 葡萄牙语
            'rus',       # 俄语
            'cmn',       # 中文（普通话）
            'jpn',       # 日语
            'kor',       # 韩语
            'ara',       # 阿拉伯语
            'hin',       # 印地语
            'tha',       # 泰语
            'vie',       # 越南语
            'nld',       # 荷兰语
            'swe',       # 瑞典语
            'nor',       # 挪威语
            'dan',       # 丹麦语
            'fin',       # 芬兰语
            'pol',       # 波兰语
            'ces',       # 捷克语
            'hun',       # 匈牙利语
            'tur',       # 土耳其语
            'heb',       # 希伯来语
        ]
    
    def change_language(self, new_language: str):
        """
        更改目标语言
        
        Args:
            new_language: 新的语言代码
        """
        self.language = new_language
        print(f"[CharsiuG2P] Language changed to: {new_language}")
    
    def get_model_info(self) -> dict:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典
        """
        return {
            'model_name': self.model_name,
            'language': self.language,
            'device': self.device,
            'supported_languages': len(self.get_supported_languages()),
            'architecture': 'ByT5 (Byte-level T5)',
            'parameters': 'Tiny/Small variants available',
            'multilingual': True
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'model'):
            del self.model
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()  # type: ignore
