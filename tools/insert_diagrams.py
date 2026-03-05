#!/usr/bin/env python3
"""批量插入Mermaid配图到文章中"""

import re

# 读取文章
with open('../articles/agent_mcp_rules_skills_深度科普.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义所有配图插入规则：(查找文本, 插入位置, 配图内容)
insertions = [
    # 1. MCP传输方式对比图 - 在"### 3.2 MCP协议的核心概念"章节的传输方式部分后
    {
        'find': '### 传输方式选择建议：',
        'diagram': '''
#### 📊 MCP三种传输方式对比

```mermaid
graph LR
    subgraph STDIO["STDIO传输"]
        A1[AI应用] <--> A2[标准输入输出]
        A2 <--> A3[本地MCP进程]
    end
    
    subgraph SSE["SSE传输"]
        B1[AI应用] -->|HTTP请求| B2[SSE端点]
        B2 -->|事件流| B1
        B2 <--> B3[远程MCP服务]
    end
    
    subgraph HTTP["HTTP Stream"]
        C1[AI应用] <-->|双向流| C2[WebSocket/HTTP2]
        C2 <--> C3[远程MCP服务]
    end
    
    style STDIO fill:#d1fae5
    style SSE fill:#dbeafe
    style HTTP fill:#fce7f3
```

'''
    },
    
    # 2. Rules优先级层次图 - 在"### 4.2 Rules的优先级机制"后
    {
        'find': '### 4.2 Rules的优先级机制',
        'diagram': '''

#### 📊 Rules优先级层次

```mermaid
graph TD
    User["🔴 用户临时指令<br/>最高优先级<br/>当前对话有效"]
    Rules["🟡 Rules规范<br/>中优先级<br/>项目/团队规范"]
    System["🟢 System Prompt<br/>低优先级<br/>Agent基础设定"]
    Default["⚪ 模型默认行为<br/>最低优先级<br/>训练数据行为"]
    
    User --> Rules
    Rules --> System
    System --> Default
    
    User -.覆盖.-> Rules
    User -.覆盖.-> System
    Rules -.覆盖.-> System
    
    style User fill:#ef4444,color:#fff
    style Rules fill:#f59e0b,color:#fff
    style System fill:#10b981,color:#fff
    style Default fill:#6b7280,color:#fff
```
'''
    },
    
    # 3. Rules分级体系图
    {
        'find': '### 4.3 如何编写高质量Rules',
        'diagram': '''

#### 📊 Rules分级体系

```mermaid
graph LR
    subgraph P0["🔴 P0: 必须遵守"]
        P0_1[类型注解]
        P0_2[禁用eval]
        P0_3[安全检查]
    end
    
    subgraph P1["🟡 P1: 强烈建议"]
        P1_1[函数长度≤50行]
        P1_2[嵌套≤3层]
        P1_3[必须有文档]
    end
    
    subgraph P2["🟢 P2: 最佳实践"]
        P2_1[列表推导]
        P2_2[f-string]
        P2_3[导入排序]
    end
    
    Input[代码输入] --> P0
    P0 -->|验证| P1
    P1 -->|验证| P2
    P2 --> Output[输出代码]
    
    P0 -.不通过.-> Reject[拒绝输出]
    P1 -.不通过.-> Warning[警告提示]
    
    style P0 fill:#fee2e2
    style P1 fill:#fef3c7
    style P2 fill:#d1fae5
    style Reject fill:#ef4444,color:#fff
    style Warning fill:#f59e0b,color:#fff
```

'''
    },
    
    # 4. Skills按需加载机制
    {
        'find': '### 5.2 Skills的核心特性',
        'diagram': '''

#### 📊 Skills按需加载机制

```mermaid
graph TD
    Start[用户请求] --> Analyze{Agent分析}
    Analyze -->|需要专业流程| LoadSkill[动态加载Skill]
    Analyze -->|简单任务| Direct[直接执行]
    
    LoadSkill --> Check{Skills库}
    Check -->|找到匹配| Load1[加载竞品分析Skill]
    Check -->|找到匹配| Load2[加载代码审查Skill]
    Check -->|找到匹配| Load3[加载文档分析Skill]
    
    Load1 --> Execute[执行Skill流程]
    Load2 --> Execute
    Load3 --> Execute
    Direct --> Execute
    
    Execute --> MCP[调用MCP工具]
    Execute --> Rules[应用Rules]
    
    MCP --> Result[生成结果]
    Rules --> Result
    
    Result --> Unload[卸载Skill]
    Unload --> End[返回用户]
    
    style LoadSkill fill:#a78bfa
    style Execute fill:#60a5fa
    style Result fill:#34d399
```

'''
    },
    
    # 5. Skills vs MCP vs Rules 协同图
    {
        'find': '## 六、四者协同：构建完整AI Agent生态',
        'diagram': '''

#### 📊 Skills、MCP、Rules 三者协同

```mermaid
graph TB
    Task[用户任务:<br/>审查Python代码] --> Agent
    
    Agent{AI Agent<br/>协调中枢}
    
    Agent -->|1. 识别需要| Skill[Skills:<br/>code-review]
    Agent -->|2. 调用工具| MCP[MCP:<br/>read_file, grep_search]
    Agent -->|3. 应用规范| Rules[Rules:<br/>Python编码标准]
    
    Skill -.提供.-> Workflow[审查流程:<br/>1. 扫描安全漏洞<br/>2. 检查性能问题<br/>3. 评估可维护性]
    
    MCP -.提供.-> Tools[工具能力:<br/>• 读取代码文件<br/>• 搜索危险模式<br/>• 分析复杂度]
    
    Rules -.提供.-> Standards[质量标准:<br/>• 必须有类型注解<br/>• 函数≤50行<br/>• 嵌套≤3层]
    
    Workflow --> Execute[执行审查]
    Tools --> Execute
    Standards --> Execute
    
    Execute --> Report[生成审查报告]
    
    style Agent fill:#c4b5fd
    style Skill fill:#34d399
    style MCP fill:#60a5fa
    style Rules fill:#fbbf24
    style Report fill:#d1fae5
```

'''
    },
    
    # 6. 完整生态架构全景图（最重要的图）
    {
        'find': '### 6.1 四者的关系模型',
        'diagram': '''

#### 📊 四者协同架构全景图

```mermaid
graph TB
    User([👤 用户请求<br/>"检查这个项目的代码质量"])
    
    User --> Agent
    
    subgraph Agent["🧠 AI Agent - 决策中枢"]
        LLM[LLM推理引擎]
        Plan[规划执行流程]
        Coord[协调各组件]
        LLM --> Plan --> Coord
    end
    
    Coord --> LoadSkill
    Coord --> CallMCP
    Coord --> ApplyRules
    
    subgraph Skills["🎯 Skills - 专业工作流"]
        SkillLib[(Skills库)]
        CodeReview[代码审查Skill]
        DocAnalysis[文档分析Skill]
        CompAnalysis[竞品分析Skill]
        
        SkillLib -.加载.-> CodeReview
        SkillLib -.加载.-> DocAnalysis
        SkillLib -.加载.-> CompAnalysis
    end
    
    LoadSkill[动态加载Skill] --> CodeReview
    
    subgraph MCP["🔌 MCP - 工具生态"]
        MCPClient[MCP Client]
        
        MCPClient --> GitHub[GitHub MCP]
        MCPClient --> FileSystem[FileSystem MCP]
        MCPClient --> Database[Database MCP]
        
        GitHub --> GitAPI[Git仓库]
        FileSystem --> Files[本地文件]
        Database --> Data[数据库]
    end
    
    CallMCP[调用工具] --> MCPClient
    
    subgraph Rules["📋 Rules - 质量保证"]
        RulesEngine[Rules引擎]
        
        RulesEngine --> P0[P0: 必须规则]
        RulesEngine --> P1[P1: 推荐规则]
        RulesEngine --> P2[P2: 风格规则]
    end
    
    ApplyRules[应用规范] --> RulesEngine
    
    CodeReview -.指引.-> Execute[执行流程]
    GitAPI -.数据.-> Execute
    Files -.数据.-> Execute
    P0 -.约束.-> Execute
    P1 -.约束.-> Execute
    
    Execute --> Output
    
    Output([✅ 高质量输出<br/>• 专业流程<br/>• 外部数据<br/>• 符合规范])
    
    style Agent fill:#c4b5fd
    style Skills fill:#34d399
    style MCP fill:#60a5fa
    style Rules fill:#fbbf24
    style Output fill:#d1fae5
```

'''
    },
    
    # 7. 从零搭建流程图
    {
        'find': '### 7.1 环境准备',
        'diagram': '''

#### 📊 从零搭建六步流程

```mermaid
graph TD
    Start([🚀 开始项目]) --> Step1
    
    Step1[📋 步骤1: 需求分析<br/>• 确定应用场景<br/>• 拆解为Agent/MCP/Skills/Rules]
    
    Step1 --> Step2
    
    Step2[🔌 步骤2: 搭建MCP Server<br/>• 定义工具接口<br/>• 实现调用逻辑<br/>• 安全性检查]
    
    Step2 --> Step3
    
    Step3[📖 步骤3: 创建Skill<br/>• 编写工作流步骤<br/>• 添加异常处理<br/>• 提供示例模板]
    
    Step3 --> Step4
    
    Step4[📋 步骤4: 编写Rules<br/>• 定义质量规范<br/>• 分优先级P0/P1/P2<br/>• 正反示例]
    
    Step4 --> Step5
    
    Step5[🤖 步骤5: 配置Agent<br/>• 连接MCP Server<br/>• 导入Skills<br/>• 应用Rules]
    
    Step5 --> Step6
    
    Step6[🧪 步骤6: 测试验证<br/>• 功能测试<br/>• 异常处理<br/>• 性能优化]
    
    Step6 --> Decision{测试通过?}
    
    Decision -->|否| Debug[🔧 调试修复]
    Debug --> Step5
    
    Decision -->|是| Deploy[🚀 部署上线<br/>• API/网页/企微]
    
    Deploy --> End([✅ 项目完成])
    
    style Step1 fill:#fef3c7
    style Step2 fill:#dbeafe
    style Step3 fill:#d1fae5
    style Step4 fill:#fce7f3
    style Step5 fill:#e0e7ff
    style Step6 fill:#fde68a
    style Deploy fill:#34d399
```

'''
    },
    
    # 8. 问题决策树
    {
        'find': '### 8.1 常见问题与解决方案',
        'diagram': '''

#### 📊 常见问题决策树

```mermaid
graph TD
    Problem{遇到问题}
    
    Problem -->|响应慢| Slow
    Problem -->|输出错误| Wrong
    Problem -->|工具失败| Fail
    Problem -->|上下文溢出| Overflow
    
    subgraph Slow["🐌 响应慢"]
        S1{Token多?}
        S1 -->|是| S2[✅ 分页返回数据]
        S1 -->|否| S3{工具慢?}
        S3 -->|是| S4[✅ 并行调用工具]
        S3 -->|否| S5[✅ 添加缓存]
    end
    
    subgraph Wrong["❌ 输出错误"]
        W1{Rules不明确?}
        W1 -->|是| W2[✅ 增加正反示例]
        W1 -->|否| W3{优先级冲突?}
        W3 -->|是| W4[✅ 分级P0/P1/P2]
    end
    
    subgraph Fail["💥 工具失败"]
        F1{超时?}
        F1 -->|是| F2[✅ 添加重试机制]
        F1 -->|否| F3{权限不足?}
        F3 -->|是| F4[✅ 配置权限]
        F3 -->|否| F5[✅ 参数验证]
    end
    
    subgraph Overflow["🔄 上下文溢出"]
        O1{Skill太长?}
        O1 -->|是| O2[✅ 拆分模块]
        O1 -->|否| O3{历史记录多?}
        O3 -->|是| O4[✅ 智能压缩]
    end
    
    style Slow fill:#fef3c7
    style Wrong fill:#fee2e2
    style Fail fill:#fce7f3
    style Overflow fill:#dbeafe
```

'''
    },
]

# 执行插入
inserted = 0
failed = []

for insertion in insertions:
    find_text = insertion['find']
    diagram = insertion['diagram']
    
    if find_text in content:
        # 找到位置并在其后插入
        content = content.replace(find_text, find_text + diagram, 1)
        inserted += 1
        print(f"✅ 插入配图: {find_text[:50]}...")
    else:
        failed.append(find_text[:50])
        print(f"❌ 未找到: {find_text[:50]}...")

# 保存
with open('../articles/agent_mcp_rules_skills_深度科普.md', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n{'='*60}")
print(f"配图插入完成")
print(f"{'='*60}")
print(f"成功插入: {inserted} 个配图")
print(f"未找到位置: {len(failed)} 个")
if failed:
    print(f"\n未找到的标记:")
    for f in failed:
        print(f"  - {f}...")
print(f"\n文件大小: {len(content)} 字符")
print(f"预估行数: {content.count(chr(10))} 行")
