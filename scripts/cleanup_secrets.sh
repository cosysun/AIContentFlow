#!/bin/bash
# 清理GitHub历史中的敏感API Key

echo "🔒 开始清理Git历史中的敏感信息..."

cd /data/workspace/AIContentFlow

# 备份当前仓库
echo "📦 创建备份..."
cd /data/workspace
cp -r AIContentFlow AIContentFlow_backup_$(date +%Y%m%d_%H%M%S)

cd /data/workspace/AIContentFlow

# 方法1：使用git filter-branch清理敏感字符串
echo "🧹 使用 git filter-branch 清理..."
git filter-branch --force --index-filter \
  "git grep -l 'LEAKED_API_KEY_PATTERN' | xargs -r sed -i 's/LEAKED_API_KEY_PATTERN/[REDACTED_API_KEY]/g'" \
  --prune-empty --tag-name-filter cat -- --all

# 清理refs
echo "🗑️  清理refs..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送
echo "⚠️  准备强制推送到远程仓库..."
echo "⚠️  这将重写GitHub历史！"
echo "⚠️  按任意键继续，或 Ctrl+C 取消..."
read -n 1

git push origin --force --all

echo "✅ 清理完成！"
echo ""
echo "📌 后续步骤："
echo "1. 访问 https://brave.com/search/api/ 撤销旧API Key"
echo "2. 生成新的API Key"
echo "3. 设置环境变量：export BRAVE_API_KEY='new_key_here'"
echo "4. 通知所有协作者重新克隆仓库"
