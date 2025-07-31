# 编辑模式架构改进文档

## 概述

根据您的建议，我们已经成功地将编辑模式从 `QTableWidget` 改为使用 `QTableView` + `ScriptTableModel`（QAbstractTableModel子类）的架构。这一改进实现了真正的 MVC 分离，大幅提升了编辑功能的可扩展性和性能。

## 架构变化

### 之前的架构（QTableWidget）
```
[UI显示] ←→ [QTableWidget] ←→ [直接操作表格项]
```
- 数据和显示紧密耦合
- 编辑操作直接修改表格项
- 难以实现复杂的数据验证和批量操作
- 撤销/重做功能实现困难

### 改进后的架构（MVC模式）
```
[UI显示：QTableView] ←→ [数据模型：ScriptTableModel] ←→ [数据源：List[Cue]]
```
- 完全的数据与显示分离
- 所有编辑操作都在数据模型层处理
- 支持复杂的数据验证、批量操作、撤销/重做
- 更好的性能和内存管理

## 新增功能

### 1. ScriptTableModel 核心特性

**数据管理**
- `set_cues()` / `get_cues()`: 批量设置/获取台词数据
- `is_modified()` / `mark_saved()`: 修改状态追踪
- `save_snapshot()` / `restore_snapshot()`: 撤销功能支持

**编辑操作**
- `add_cue()`: 添加新台词
- `remove_cue()`: 删除台词
- `duplicate_cue()`: 复制台词
- `move_cue()`: 移动台词位置

**批量操作**
- `batch_update_character()`: 批量修改角色名称
- `refresh_phonemes()`: 批量刷新音素
- `search_cues()`: 搜索功能

**数据验证**
- 实时数据验证
- `validationError` 信号通知验证错误
- 字段长度和内容检查

### 2. 用户界面改进

**编辑工具栏**
```
[加载剧本] [保存剧本] [添加台词] [删除台词] [复制台词] [刷新音素]
```

**右键菜单**
- 基本编辑操作（添加、删除、复制）
- 批量操作子菜单
- 角色名称批量修改

**表格功能**
- 多选支持（Ctrl/Shift选择）
- 列排序功能
- 行选择模式
- 只读列（ID、音素）显示区分

### 3. 信号机制

**数据模型信号**
- `dataModified`: 数据修改时发出
- `cueAdded` / `cueRemoved`: 台词增删时发出
- `validationError`: 数据验证错误时发出

**UI响应信号**
- 窗口标题显示修改状态（*标记）
- 按钮状态根据选择自动启用/禁用
- 实时同步编辑模式和剧场模式数据

## 技术实现细节

### 关键文件

1. **app/models/script_table_model.py**
   - 完整的 QAbstractTableModel 实现
   - 支持所有标准表格操作
   - 内置数据验证和批量操作

2. **app/views/main_console.py** (改进部分)
   - 编辑模式使用 QTableView + ScriptTableModel
   - 剧场模式仍使用 QTableWidget（纯显示）
   - 新增编辑操作方法和信号处理

3. **app/data/script_data.py** (扩展)
   - 新增 `save_to_file()` 方法

### 兼容性保证

- 剧场模式仍使用原有的 QTableWidget，保证显示性能
- 数据在两种模式间自动同步
- 原有的播放器和对齐器功能完全兼容

## 使用示例

### 基本编辑操作
```python
# 添加新台词
model.add_cue("新角色", "新台词内容")

# 批量修改角色名称
count = model.batch_update_character("旧角色", "新角色")

# 搜索台词
matches = model.search_cues("关键词")

# 刷新音素
model.refresh_phonemes(g2p_converter)
```

### 数据状态管理
```python
# 检查修改状态
if model.is_modified():
    # 提示保存
    
# 保存后标记为已保存
model.mark_saved()

# 撤销到上次保存状态
model.restore_snapshot()
```

## 性能优势

1. **内存效率**: 数据只存储一份，视图只是显示层
2. **更新效率**: 只刷新变化的部分，不需要重建整个表格
3. **批量操作**: 在数据层处理，避免逐个UI更新
4. **排序性能**: 直接在数据模型中排序，视图自动同步

## 扩展能力

这种架构为未来功能扩展奠定了基础：

1. **撤销/重做系统**: 基于快照机制易于实现
2. **数据验证框架**: 可扩展更复杂的验证规则
3. **插件系统**: 数据模型可被不同的视图和插件使用
4. **导入/导出**: 统一的数据接口便于格式转换
5. **协作编辑**: 数据变更信号支持实时同步

## 总结

通过引入 `ScriptTableModel`，我们实现了：

✅ **真正的 MVC 分离** - 数据逻辑与显示逻辑完全分离  
✅ **强大的编辑功能** - 支持复杂的编辑操作和批量处理  
✅ **优秀的扩展性** - 为未来功能扩展提供了坚实基础  
✅ **更好的性能** - 高效的数据管理和UI更新机制  
✅ **完整的兼容性** - 与现有功能无缝集成  

这一改进显著提升了编辑模式的专业性和可用性，同时保持了剧场模式的简洁高效。
