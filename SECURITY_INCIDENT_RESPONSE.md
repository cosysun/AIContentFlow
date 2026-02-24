# 🚨 API Key泄露应急响应文档

## 📋 泄露情况

- **泄露的Key**: `BSA*********************` (Brave Search API - 已脱敏)
- **泄露位置**: GitHub仓库 `cosysun/AIContentFlow`
- **影响范围**: 初始提交 (ec3ab67) 及历史记录
- **发现时间**: 2026-02-24
- **修复状态**: 当前代码已清理，但历史记录仍包含

---

## ✅ 已完成的修复

1. ✅ 从所有当前代码中删除硬编码API Key
2. ✅ 创建 `.env.example` 模板
3. ✅ 更新 `.gitignore` 防止未来泄露
4. ✅ 提交修复：commit b364bdb
5. ✅ 推送到GitHub

---

## ⚠️ 仍需执行的关键步骤

### 🔥 步骤1：立即撤销泄露的API Key（最高优先级）

**操作步骤**：
1. 访问：https://brave.com/search/api/
2. 登录账户
2. 找到泄露的Key（已脱敏显示）
4. **点击"删除"或"撤销"按钮**
5. 生成新的API Key
6. 将新Key保存到本地（不要提交到Git）

**设置新Key**：
```bash
# 临时设置（当前终端会话有效）
export BRAVE_API_KEY="your_new_key_here"

# 永久设置（添加到 ~/.bashrc）
echo 'export BRAVE_API_KEY="your_new_key_here"' >> ~/.bashrc
source ~/.bashrc
```

---

### 🧹 步骤2：清理GitHub历史记录

由于仓库只有2个提交，最简单的方法是**删除仓库并重新创建**。

#### **方案A：删除并重建仓库（推荐）**

1. **在GitHub上删除仓库**：
   - 访问：https://github.com/cosysun/AIContentFlow/settings
   - 滚动到底部"Danger Zone"
   - 点击"Delete this repository"
   - 输入仓库名确认删除

2. **重新创建仓库**：
   ```bash
   cd /data/workspace/AIContentFlow
   
   # 删除现有的Git历史
   rm -rf .git
   
   # 重新初始化（创建全新的历史）
   git init
   git add -A
   git commit -m "feat: AIContentFlow - AI内容创作工作流系统

   初始功能：
   - 热点监控（V2EX、GitHub Trending等）
   - 内容创作工具
   - 发布管理
   - 配置化数据源管理
   
   安全改进：
   - 使用环境变量管理API Key
   - 添加.env.example模板
   - 完善.gitignore规则"
   
   # 添加远程仓库（需要在GitHub重新创建后）
   git remote add origin https://github.com/cosysun/AIContentFlow.git
   git branch -M main
   git push -u origin main
   ```

#### **方案B：使用BFG Repo-Cleaner（技术方案）**

如果不想删除仓库，可以使用工具清理历史：

```bash
# 1. 安装BFG（需要Java环境）
cd /tmp
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# 2. 创建替换规则
echo "LEAKED_API_KEY==>***REMOVED***" > /tmp/passwords.txt

# 3. 清理仓库
cd /data/workspace/AIContentFlow
java -jar /tmp/bfg-1.14.0.jar --replace-text /tmp/passwords.txt .

# 4. 清理refs
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. 强制推送
git push origin --force --all
```

---

### 📢 步骤3：通知协作者（如果有）

如果有其他人克隆了仓库，需要通知他们：

```markdown
【重要通知】AIContentFlow仓库已重建

由于安全原因，仓库历史已被重写。请执行以下操作：

1. 删除本地仓库
2. 重新克隆：git clone https://github.com/cosysun/AIContentFlow.git
3. 设置环境变量：export BRAVE_API_KEY="联系我获取新Key"
```

---

## 🔒 未来防护措施

### 1. 使用pre-commit Hook

创建 `.git/hooks/pre-commit`：
```bash
#!/bin/bash
# 检测敏感信息

if git diff --cached | grep -E '(api[_-]?key|password|secret|token).*=.*["\047][^"\047]{20,}'; then
    echo "❌ 检测到可能的敏感信息！"
    echo "请使用环境变量代替硬编码"
    exit 1
fi
```

### 2. 使用GitHub Secret Scanning

GitHub已自动启用密钥扫描，如果检测到泄露会发送警告邮件。

### 3. 定期审计

```bash
# 检查是否有硬编码的敏感信息
cd /data/workspace/AIContentFlow
git grep -E '(BSA[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{40,})'
```

---

## 📊 损害评估

### 潜在风险：
- ✅ **低风险**：仓库刚创建（2026-02-24），可能尚未被爬虫索引
- ⚠️ **中等风险**：如果有人已克隆仓库，可能已获取Key
- 🔥 **高风险**：Brave API Key可用于消耗配额或发起请求

### 检查是否被滥用：
1. 登录Brave API控制台
2. 查看API使用量统计
3. 检查是否有异常请求

---

## ✅ 最终检查清单

- [ ] 在Brave网站撤销旧API Key
- [ ] 生成新API Key
- [ ] 设置本地环境变量
- [ ] 删除并重建GitHub仓库（或使用BFG清理）
- [ ] 验证新仓库不包含敏感信息
- [ ] 测试工作流是否正常运行
- [ ] 设置pre-commit hook
- [ ] 更新文档说明环境变量配置

---

## 📞 紧急联系

如果API Key已被滥用，立即：
1. 联系Brave支持：https://brave.com/support/
2. 请求冻结账户或撤销所有Key
3. 检查是否有资金损失

---

**创建时间**: 2026-02-24  
**文档版本**: 1.0  
**紧急程度**: 🔥 高
