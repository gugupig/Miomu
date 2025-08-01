# 测试 G2P 管理器功能
print("🧪 测试 G2P 管理器...")

try:
    from app.core.g2p.g2p_manager import G2PManager, G2PEngineType
    
    # 创建管理器
    manager = G2PManager()
    print("✅ G2P管理器创建成功")
    
    # 获取可用引擎
    available = manager.get_available_engines()
    print(f"📋 可用引擎数量: {len(available)}")
    
    for engine_type, config in available:
        print(f"  - {config['name']} ({engine_type.value})")
        
    # 获取最佳引擎
    try:
        engine = manager.get_best_available_engine()
        info = manager.get_current_engine_info()
        print(f"✅ 当前引擎: {info['name']} (语言: {info['language']})")
        
        # 测试转换
        test_text = "Bonjour"
        result = engine.convert(test_text)
        print(f"🔤 测试转换: '{test_text}' -> [{result}]")
        
    except Exception as e:
        print(f"❌ 引擎测试失败: {e}")
        
except Exception as e:
    print(f"❌ G2P管理器测试失败: {e}")
    import traceback
    traceback.print_exc()

print("🏁 G2P管理器测试完成")
