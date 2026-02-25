#!/usr/bin/env python3
"""
AIContentFlow 文章质检脚本
自动检查文章质量并生成质检报告
"""

import re
import sys
from typing import Dict, List, Tuple
from pathlib import Path


class QualityChecker:
    """文章质检器"""
    
    def __init__(self, article_path: str):
        self.article_path = article_path
        with open(article_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        self.word_count = len(self.content)
    
    def check_all(self) -> Dict:
        """执行全部质检"""
        print("\n🔍 开始全方位质检...\n")
        
        results = {
            'tech_accuracy': self.check_tech_accuracy(),
            'logic': self.check_logic(),
            'completeness': self.check_completeness(),
            'code_quality': self.check_code_quality(),
            'readability': self.check_readability(),
            'practicality': self.check_practicality(),
            'format': self.check_format(),
            'no_ai_style': self.check_ai_style(),
            'seo': self.check_seo(),
            'innovation': self.check_innovation()
        }
        
        # 计算总分
        weights = {
            'tech_accuracy': 0.15,
            'logic': 0.10,
            'completeness': 0.10,
            'code_quality': 0.10,
            'readability': 0.10,
            'practicality': 0.10,
            'format': 0.10,
            'no_ai_style': 0.10,
            'seo': 0.10,
            'innovation': 0.05
        }
        
        total = sum(results[k] * weights[k] for k in results)
        results['total_score'] = round(total, 1)
        results['grade'] = self.get_grade(total)
        
        return results
    
    def check_tech_accuracy(self) -> float:
        """检查技术准确性"""
        print("📊 检查技术准确性...")
        score = 10.0
        issues = []
        
        # 检查未标注来源的数据
        numbers = re.findall(r'\d+[KkMm]?\+?\s*(?:Stars?|Forks?|下载|用户)', self.content)
        citations = len(re.findall(r'\[.*?\]\(.*?\)', self.content))
        
        if len(numbers) > citations + 2:
            score -= 1
            issues.append(f"发现{len(numbers)}个数据点，但只有{citations}个引用链接")
        
        # 检查代码块中的常见错误
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', self.content, re.DOTALL)
        for i, code in enumerate(code_blocks):
            if 'import' in code and 'from' not in code and code.count('import') == 1:
                if not re.search(r'^\s*import\s+\w+', code, re.MULTILINE):
                    issues.append(f"代码块{i+1}可能缺少import语句")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print("  ✅ 未发现明显问题")
        
        return max(0, score)
    
    def check_logic(self) -> float:
        """检查逻辑连贯性"""
        print("🔗 检查逻辑连贯性...")
        score = 10.0
        issues = []
        
        # 检查标题层级
        h1_count = len(re.findall(r'^# [^#]', self.content, re.MULTILINE))
        h2_count = len(re.findall(r'^## [^#]', self.content, re.MULTILINE))
        h3_count = len(re.findall(r'^### [^#]', self.content, re.MULTILINE))
        
        if h1_count != 1:
            score -= 1
            issues.append(f"H1标题应有且仅有1个，当前{h1_count}个")
        
        if h2_count < 3:
            score -= 0.5
            issues.append(f"H2标题过少（{h2_count}个），建议≥3个")
        
        # 检查段落突兀跳跃（简单启发式：连续短段落）
        paragraphs = self.content.split('\n\n')
        short_paras = [p for p in paragraphs if 0 < len(p.strip()) < 50 and not p.strip().startswith('#')]
        if len(short_paras) > len(paragraphs) * 0.3:
            score -= 0.5
            issues.append("短段落过多，可能存在内容跳跃")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 结构合理（H1:{h1_count}, H2:{h2_count}, H3:{h3_count}）")
        
        return max(0, score)
    
    def check_completeness(self) -> float:
        """检查内容完整性"""
        print("📝 检查内容完整性...")
        score = 10.0
        issues = []
        
        # 检查字数
        if self.word_count < 2000:
            score -= 3
            issues.append(f"字数不足（{self.word_count}字 < 2000字）")
        elif self.word_count < 3000:
            score -= 1
            issues.append(f"字数偏少（{self.word_count}字 < 3000字）")
        
        # 检查是否有示例/案例
        case_keywords = ['例如', '示例', '案例', 'Example', 'example', 'Case']
        case_count = sum(self.content.count(kw) for kw in case_keywords)
        if case_count < 3:
            score -= 1
            issues.append(f"案例/示例不足（{case_count}个 < 3个）")
        
        # 检查是否有总结
        if not re.search(r'##?\s*(?:总结|小结|结论|Conclusion)', self.content, re.IGNORECASE):
            score -= 0.5
            issues.append("建议增加总结章节")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 内容完整（{self.word_count}字，{case_count}个案例）")
        
        return max(0, score)
    
    def check_code_quality(self) -> float:
        """检查代码质量"""
        print("💻 检查代码质量...")
        score = 10.0
        issues = []
        
        # 检查代码块标注
        code_blocks_with_lang = re.findall(r'```(\w+)', self.content)
        code_blocks_no_lang = re.findall(r'```\n', self.content)
        
        no_lang_count = len(code_blocks_no_lang)
        if no_lang_count > 0:
            score -= no_lang_count * 0.5
            issues.append(f"{no_lang_count}个代码块未标注语言")
        
        # 检查Python代码规范（如果有Python代码）
        python_blocks = [block for block in re.findall(r'```python\n(.*?)```', self.content, re.DOTALL)]
        for i, code in enumerate(python_blocks):
            # 检查缩进一致性（简单检查）
            if '\t' in code:
                score -= 0.5
                issues.append(f"Python代码块{i+1}使用Tab缩进，建议用空格")
        
        total_blocks = len(code_blocks_with_lang) + no_lang_count
        if total_blocks == 0:
            print("  ℹ️  无代码块（非编程类文章可忽略）")
        elif issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 代码规范（{total_blocks}个代码块）")
        
        return max(0, score)
    
    def check_readability(self) -> float:
        """检查可读性"""
        print("👀 检查可读性...")
        score = 10.0
        issues = []
        
        # 检查超长段落
        paragraphs = [p for p in self.content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        long_paras = [p for p in paragraphs if p.count('\n') > 8]
        
        if len(long_paras) > 0:
            score -= len(long_paras) * 0.5
            issues.append(f"{len(long_paras)}个超长段落（>8行）")
        
        # 检查术语是否有解释（启发式：专业词汇后是否有括号/冒号说明）
        # 简化实现：检查是否有适当的解释性文本
        explanation_markers = self.content.count('（') + self.content.count('：即') + self.content.count('，指')
        if explanation_markers < 5:
            score -= 0.5
            issues.append("专业术语解释较少，建议增加")
        
        # 检查是否使用类比
        analogy_keywords = ['就像', '类似', '好比', '相当于', 'like', 'similar to']
        analogy_count = sum(self.content.count(kw) for kw in analogy_keywords)
        if analogy_count == 0:
            score -= 0.5
            issues.append("建议使用类比增强可读性")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 可读性良好")
        
        return max(0, score)
    
    def check_practicality(self) -> float:
        """检查实用性"""
        print("🛠️  检查实用性...")
        score = 10.0
        issues = []
        
        # 检查外部链接
        links = re.findall(r'\[.*?\]\((https?://.*?)\)', self.content)
        if len(links) < 3:
            score -= 1
            issues.append(f"外部链接较少（{len(links)}个 < 3个）")
        
        # 检查是否有实战案例（完整的项目/代码仓库）
        github_links = [l for l in links if 'github.com' in l]
        if len(github_links) == 0:
            score -= 0.5
            issues.append("建议提供GitHub示例代码")
        
        # 检查是否有步骤清单/配置说明
        if '```' not in self.content:
            score -= 1
            issues.append("缺少代码/配置示例")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 实用性强（{len(links)}个链接）")
        
        return max(0, score)
    
    def check_format(self) -> float:
        """检查格式规范"""
        print("📐 检查格式规范...")
        score = 10.0
        issues = []
        
        # 检查中英文间距（简单启发式）
        no_space_matches = re.findall(r'[\u4e00-\u9fa5][a-zA-Z]|[a-zA-Z][\u4e00-\u9fa5]', self.content)
        if len(no_space_matches) > 20:
            score -= 1
            issues.append(f"中英文间距问题较多（{len(no_space_matches)}处）")
        
        # 检查标点符号（中英文混用）
        chinese_comma_in_english = re.findall(r'[a-zA-Z]，', self.content)
        english_comma_in_chinese = re.findall(r'[\u4e00-\u9fa5],(?![0-9])', self.content)
        
        if len(chinese_comma_in_english) + len(english_comma_in_chinese) > 5:
            score -= 0.5
            issues.append("标点符号中英文混用")
        
        # 检查表格对齐（Markdown表格）
        tables = re.findall(r'\|.*\|', self.content)
        if len(tables) > 0:
            # 简单检查：表格是否有分隔行
            table_separators = re.findall(r'\|[\s:-]+\|', self.content)
            if len(table_separators) < len(tables) * 0.3:
                score -= 0.5
                issues.append("表格格式可能不规范")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 格式规范")
        
        return max(0, score)
    
    def check_ai_style(self) -> float:
        """检查AI腔"""
        print("🎨 检查AI腔...")
        score = 10.0
        issues = []
        
        # 检测套话
        cliches = {
            '在当今': 1,
            '随着': 1,
            '值得注意的是': 0.5,
            '需要指出的是': 0.5,
            '毫无疑问': 0.5,
            '显而易见': 0.5,
            '众所周知': 0.5,
            '综上所述': 0.5,
            '总而言之': 0.5
        }
        
        found_cliches = {}
        for cliche, penalty in cliches.items():
            count = self.content.count(cliche)
            if count > 0:
                score -= count * penalty
                found_cliches[cliche] = count
        
        if found_cliches:
            issues.append("发现AI套话：" + ", ".join([f"{k}×{v}" for k, v in found_cliches.items()]))
        
        # 检查过渡词密度
        transition_words = ['然而', '此外', '因此', '另外', '同时']
        transition_count = sum(self.content.count(w) for w in transition_words)
        transition_density = transition_count / (self.word_count / 1000)  # 每千字
        
        if transition_density > 8:
            score -= 1
            issues.append(f"过渡词密度过高（{transition_density:.1f}次/千字 > 8）")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ 语言自然")
        
        return max(0, score)
    
    def check_seo(self) -> float:
        """检查SEO优化"""
        print("🔍 检查SEO优化...")
        score = 10.0
        issues = []
        
        # 获取标题
        h1_match = re.search(r'^# (.+)$', self.content, re.MULTILINE)
        if not h1_match:
            score -= 2
            issues.append("缺少H1标题")
            return max(0, score)
        
        title = h1_match.group(1)
        
        # 检查H2数量
        h2_count = len(re.findall(r'^## [^#]', self.content, re.MULTILINE))
        if h2_count < 3:
            score -= 1
            issues.append(f"H2标题过少（{h2_count}个 < 3个）")
        elif h2_count > 10:
            score -= 0.5
            issues.append(f"H2标题过多（{h2_count}个 > 10个）")
        
        # 检查Meta信息（字数统计、标签等）
        has_meta = bool(re.search(r'(?:字数|阅读时长|标签|Tags)', self.content, re.IGNORECASE))
        if not has_meta:
            score -= 1
            issues.append("建议添加Meta信息（字数、阅读时长、标签）")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"  ✅ SEO友好（{h2_count}个H2）")
        
        return max(0, score)
    
    def check_innovation(self) -> float:
        """检查创新性（主观评分，默认7分）"""
        print("💡 检查创新性...")
        score = 7.0
        
        # 简单启发式：检查是否有独特视角的标志
        innovation_markers = [
            '首次', '首个', '创新', '独特', '新方法', '新思路',
            'novel', 'innovative', 'unique', 'new approach'
        ]
        
        innovation_count = sum(self.content.lower().count(marker.lower()) for marker in innovation_markers)
        
        if innovation_count >= 3:
            score = 9.0
            print(f"  ✅ 创新性较强（{innovation_count}个创新标记）")
        elif innovation_count >= 1:
            score = 8.0
            print(f"  ✅ 有创新点（{innovation_count}个创新标记）")
        else:
            print(f"  ℹ️  创新性一般（可通过独特视角/新案例提升）")
        
        return score
    
    def get_grade(self, score: float) -> str:
        """获取评级"""
        if score >= 90:
            return "A级（可发布）⭐⭐⭐⭐⭐"
        elif score >= 80:
            return "B级（需优化）⭐⭐⭐⭐"
        elif score >= 70:
            return "C级（需重写）⭐⭐⭐"
        else:
            return "D级（不合格）⭐⭐"
    
    def get_stars(self, score: float) -> str:
        """获取星级"""
        if score >= 9:
            return "⭐⭐⭐⭐⭐"
        elif score >= 8:
            return "⭐⭐⭐⭐"
        elif score >= 7:
            return "⭐⭐⭐"
        elif score >= 6:
            return "⭐⭐"
        else:
            return "⭐"


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 quality_checker.py <文章路径>")
        sys.exit(1)
    
    article_path = sys.argv[1]
    
    if not Path(article_path).exists():
        print(f"❌ 文件不存在: {article_path}")
        sys.exit(1)
    
    print(f"\n📋 开始质检文章: {article_path}\n")
    print("=" * 60)
    
    checker = QualityChecker(article_path)
    results = checker.check_all()
    
    print("\n" + "=" * 60)
    print("\n📊 质检结果汇总\n")
    print(f"总分：{results['total_score']}/100")
    print(f"评级：{results['grade']}")
    print(f"\n各维度得分：")
    
    dimension_names = {
        'tech_accuracy': '技术准确性',
        'logic': '逻辑连贯性',
        'completeness': '内容完整性',
        'code_quality': '代码质量',
        'readability': '可读性',
        'practicality': '实用性',
        'format': '格式规范',
        'no_ai_style': '降AI味',
        'seo': 'SEO优化',
        'innovation': '创新性'
    }
    
    for key, name in dimension_names.items():
        score = results[key]
        stars = checker.get_stars(score)
        print(f"  {name:12s}: {score:4.1f}/10 {stars}")
    
    print("\n" + "=" * 60)
    
    # 给出建议
    if results['total_score'] >= 90:
        print("\n🎉 恭喜！文章质量优秀，可以发布！")
    elif results['total_score'] >= 80:
        print("\n⚠️  文章质量良好，建议优化后发布。")
    elif results['total_score'] >= 70:
        print("\n❌ 文章需要重写部分内容才能发布。")
    else:
        print("\n🚫 文章质量不合格，不建议发布。")
    
    print()


if __name__ == '__main__':
    main()
