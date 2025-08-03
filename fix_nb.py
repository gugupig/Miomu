import json

# 读取带 BOM 的文件
with open('playground.ipynb', 'r', encoding='utf-8-sig') as f:
    nb = json.load(f)

# 写回不带 BOM 的文件
with open('playground.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('Fixed notebook encoding - removed BOM')
