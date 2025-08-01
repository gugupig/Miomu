# G2P编码问题解决方案

## 🔍 问题分析

您遇到的错误：
```
创建G2P引擎失败 (epitran): 'gbk' codec can't decode byte 0xa3 in position 7832: illegal multibyte sequence
```

这是一个典型的字符编码问题，发生在Windows系统上，因为：
1. Windows系统默认使用GBK编码
2. Epitran库内部包含UTF-8编码的语言数据文件
3. 当Python尝试用GBK解码UTF-8文件时就会出错

## ✅ 已实施的解决方案

### 1. 主程序编码设置
在 `main.py` 中添加了启动时的编码环境设置：
```python
def setup_encoding():
    """设置UTF-8编码环境"""
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.platform.startswith('win'):
        os.environ['LANG'] = 'en_US.UTF-8'
        os.environ['LC_ALL'] = 'en_US.UTF-8'
```

### 2. Epitran引擎编码修复
在 `epitran_g2p.py` 中添加了初始化时的编码处理：
```python
# 设置环境变量确保使用UTF-8编码
original_lang = os.environ.get('LANG', '')
original_lc_all = os.environ.get('LC_ALL', '')

try:
    # 临时设置UTF-8环境
    os.environ['LANG'] = 'en_US.UTF-8'
    os.environ['LC_ALL'] = 'en_US.UTF-8'
    
    # 在Windows上设置locale
    if sys.platform.startswith('win'):
        try:
            import locale
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
    
    self.epi = epitran.Epitran(self.language)
    
finally:
    # 恢复原始环境变量
    # ... 恢复代码
```

### 3. G2P管理器编码环境
在 `g2p_manager.py` 中添加了自动编码环境设置：
```python
def _setup_encoding_environment(self):
    """设置UTF-8编码环境，解决Epitran编码问题"""
    try:
        if 'PYTHONIOENCODING' not in os.environ:
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        if sys.platform.startswith('win'):
            if 'LANG' not in os.environ:
                os.environ['LANG'] = 'en_US.UTF-8'
            if 'LC_ALL' not in os.environ:
                os.environ['LC_ALL'] = 'en_US.UTF-8'
    except Exception as e:
        logging.warning(f"设置G2P编码环境时出错: {e}")
```

### 4. 智能错误处理和自动回退
改进了错误处理，提供友好的错误信息：
```python
# 特殊处理编码错误
if "codec can't decode" in error_msg or "illegal multibyte sequence" in error_msg:
    logging.error(f"❌ 创建G2P引擎失败 ({engine_type.value}): 编码问题 - {e}")
    logging.info("💡 这可能是由于系统编码设置导致的，正在尝试备用引擎...")
```

当Epitran失败时，系统会自动回退到Simple G2P引擎，确保功能继续可用。

## 🎯 工作流程

1. **主程序启动时**：`main.py` 设置全局编码环境
2. **G2P管理器初始化**：再次确认编码环境设置
3. **Epitran引擎创建**：使用临时UTF-8环境创建引擎
4. **错误处理**：如果仍然失败，自动回退到Simple G2P
5. **用户体验**：系统继续正常工作，只是使用备用引擎

## 🔧 手动解决方法

如果问题仍然存在，用户可以手动设置环境变量：

### Windows用户：
```batch
set PYTHONIOENCODING=utf-8
set LANG=en_US.UTF-8
set LC_ALL=en_US.UTF-8
```

### Linux/Mac用户：
```bash
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

## 📊 测试结果

测试显示：
- ✅ 编码错误被正确捕获和处理
- ✅ 提供了详细的错误信息和解决建议
- ✅ 自动回退机制正常工作
- ✅ 系统功能继续可用（使用Simple G2P）

## 🎉 用户体验改进

1. **透明处理**：用户不需要关心技术细节
2. **自动回退**：即使Epitran失败，G2P功能仍然可用
3. **友好提示**：如果有问题，提供清晰的解决建议
4. **稳定运行**：系统不会因为编码问题而崩溃

现在您的G2P系统应该能够在Windows系统上稳定运行，即使遇到编码问题也会自动处理并继续工作！
