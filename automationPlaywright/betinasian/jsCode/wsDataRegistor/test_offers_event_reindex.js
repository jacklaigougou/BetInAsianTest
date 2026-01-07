/**
 * 测试 Offers Event 重索引逻辑
 *
 * 测试场景:
 * 1. 第一次更新: 添加 ah 的 line 20, 22
 * 2. 第二次更新: ah 的 line 变成 22, 24 (删除 20, 新增 24)
 * 3. 验证索引中只包含 22, 24,不包含 20
 */

function testOffersEventReindex() {
    console.log('\n========== 测试 Offers Event 重索引 ==========\n');

    // 确保依赖存在
    if (!window.__offersEventStore || !window.__offersEventManager || !window.__offersHandler) {
        console.error('❌ 依赖未加载');
        return;
    }

    const eventKey = 'test_event_123';

    // 第一次更新: ah 有 line 20, 22
    console.log('📝 第一次更新: ah 有 line 20, 22');
    const update1 = {
        type: 'offers_event',
        sportPeriod: null,
        eventKey: eventKey,
        data: {
            "ah": [
                [20, [["a", 1.877], ["h", 1.862]]],
                [22, [["a", 1.888], ["h", 1.851]]]
            ]
        }
    };

    window.__offersHandler.handle(update1);

    // 验证第一次更新后的状态
    let lineIds = window.__offersEventManager.getLineIds(eventKey, 'ah');
    console.log(`✅ 第一次更新后 line_ids: [${lineIds.join(', ')}]`);
    console.log(`   - hasLine(20): ${window.__offersEventManager.hasLine(eventKey, 'ah', 20)}`);
    console.log(`   - hasLine(22): ${window.__offersEventManager.hasLine(eventKey, 'ah', 22)}`);
    console.log(`   - hasLine(24): ${window.__offersEventManager.hasLine(eventKey, 'ah', 24)}`);

    // 检查索引
    const expectedLines1 = [20, 22];
    const actualLines1 = lineIds.sort((a, b) => a - b);
    const passed1 = JSON.stringify(actualLines1) === JSON.stringify(expectedLines1);
    console.log(`\n🔍 验证: ${passed1 ? '✅ PASS' : '❌ FAIL'} - 预期 [20, 22], 实际 [${actualLines1.join(', ')}]`);

    // 第二次更新: ah 的 line 变成 22, 24 (删除 20, 新增 24)
    console.log('\n📝 第二次更新: ah 有 line 22, 24 (删除 20, 新增 24)');
    const update2 = {
        type: 'offers_event',
        sportPeriod: null,
        eventKey: eventKey,
        data: {
            "ah": [
                [22, [["a", 1.888], ["h", 1.851]]],
                [24, [["a", 1.900], ["h", 1.840]]]
            ]
        }
    };

    window.__offersHandler.handle(update2);

    // 验证第二次更新后的状态
    lineIds = window.__offersEventManager.getLineIds(eventKey, 'ah');
    console.log(`✅ 第二次更新后 line_ids: [${lineIds.join(', ')}]`);
    console.log(`   - hasLine(20): ${window.__offersEventManager.hasLine(eventKey, 'ah', 20)} (应该是 false)`);
    console.log(`   - hasLine(22): ${window.__offersEventManager.hasLine(eventKey, 'ah', 22)} (应该是 true)`);
    console.log(`   - hasLine(24): ${window.__offersEventManager.hasLine(eventKey, 'ah', 24)} (应该是 true)`);

    // 检查索引 - 关键测试: line 20 应该已经被移除
    const expectedLines2 = [22, 24];
    const actualLines2 = lineIds.sort((a, b) => a - b);
    const passed2 = JSON.stringify(actualLines2) === JSON.stringify(expectedLines2);
    const hasOldLine = window.__offersEventManager.hasLine(eventKey, 'ah', 20);

    console.log(`\n🔍 验证: ${passed2 && !hasOldLine ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`   - 预期 line_ids: [22, 24]`);
    console.log(`   - 实际 line_ids: [${actualLines2.join(', ')}]`);
    console.log(`   - 旧 line 20 已清理: ${!hasOldLine ? '✅' : '❌'}`);

    // 测试异常数据防御
    console.log('\n📝 测试异常数据防御');
    const update3 = {
        type: 'offers_event',
        sportPeriod: null,
        eventKey: 'test_event_456',
        data: null  // 异常: data 是 null
    };

    try {
        window.__offersHandler.handle(update3);
        console.log('✅ 异常数据防御测试通过 - 不会 crash');
    } catch (error) {
        console.error('❌ 异常数据防御测试失败 - crash 了:', error);
    }

    // 总结
    console.log('\n========== 测试完成 ==========');
    if (passed1 && passed2 && !hasOldLine) {
        console.log('✅ 所有测试通过! 重索引逻辑正常工作');
    } else {
        console.log('❌ 部分测试失败,请检查修复');
    }
}

// 导出到 window
if (typeof window !== 'undefined') {
    window.testOffersEventReindex = testOffersEventReindex;
    console.log('[Test] Offers Event Reindex 测试已加载,运行 window.testOffersEventReindex() 开始测试');
}
