#!/usr/bin/env node
/**
 * mdnice_formatter.js
 * 功能：将 Markdown 文件排版为微信公众号 HTML（模拟 mdnice 效果）
 * 原理：markdown-it 解析 Markdown → juice 内联 mdnice 主题 CSS
 * 用法：node mdnice_formatter.js <input.md> [output.html] [--theme=normal]
 */

const fs = require('fs');
const path = require('path');
const MarkdownIt = require('markdown-it');
const juice = require('juice');

// ============================================================================
// 主题配置
// ============================================================================

const THEMES_DIR = path.join(__dirname, 'mdnice_themes');

const THEME_MAP = {
  normal:      'normal.css',
  default:     'normal.css',
  orangeheart: 'orangeheart.css',
  purple:      'purple.css',
  green:       'green.css',
  blue:        'blue.css',
  lanqing:     'lanqing.css',
};

function loadCSS(filename) {
  const fullPath = path.join(THEMES_DIR, filename);
  if (!fs.existsSync(fullPath)) return '';
  return fs.readFileSync(fullPath, 'utf8');
}

function getThemeCSS(themeName) {
  const basicCSS = loadCSS('basic.css');
  const themeFile = THEME_MAP[themeName] || THEME_MAP['normal'];
  const themeCSS = loadCSS(themeFile);
  return basicCSS + '\n' + themeCSS;
}

// ============================================================================
// Markdown 解析配置
// ============================================================================

const md = new MarkdownIt({
  html: true,
  breaks: false,
  linkify: true,
  typographer: true,
});

// 自定义渲染：代码块加上微信公众号友好的样式
const defaultFence = md.renderer.rules.fence || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.fence = function(tokens, idx, options, env, self) {
  const token = tokens[idx];
  const lang = token.info ? token.info.trim() : '';
  const code = token.content;
  const langLabel = lang ? `<span class="code-lang">${lang}</span>` : '';
  return `<pre class="code-block"><code class="language-${lang}">${escapeHtml(code)}</code>${langLabel}</pre>\n`;
};

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ============================================================================
// 核心转换函数
// ============================================================================

function convertToWechatHTML(markdownContent, themeName = 'normal') {
  // Step 1: 去掉第一行 # 标题（公众号标题单独设置，不放正文）
  const lines = markdownContent.split('\n');
  let startLine = 0;
  if (lines[0] && lines[0].startsWith('# ')) {
    startLine = 1;
    // 跳过标题后的空行
    while (startLine < lines.length && lines[startLine].trim() === '') {
      startLine++;
    }
  }
  const bodyContent = lines.slice(startLine).join('\n');

  // Step 2: markdown-it 解析为 HTML
  const rawHTML = md.render(bodyContent);

  // Step 3: 包裹在 #nice div 中（mdnice 的约定容器）
  const wrappedHTML = `<div id="nice">\n${rawHTML}\n</div>`;

  // Step 4: 加载主题 CSS
  const themeCSS = getThemeCSS(themeName);

  if (!themeCSS.trim()) {
    console.error(`⚠️  主题 CSS 未找到，将输出无样式 HTML`);
    return wrappedHTML;
  }

  // Step 5: juice 内联 CSS
  const options = {
    removeStyleTags: true,
    applyStyleTags: true,
    applyAttributesTableElements: false,
    preserveMediaQueries: false,
    preserveFontFaces: false,
  };

  const styledHTML = juice.inlineContent(wrappedHTML, themeCSS, options);

  return styledHTML;
}

// ============================================================================
// 命令行入口
// ============================================================================

function parseArgs() {
  const args = process.argv.slice(2);
  let inputFile = null;
  let outputFile = null;
  let theme = 'normal';

  for (const arg of args) {
    if (arg.startsWith('--theme=')) {
      theme = arg.split('=')[1];
    } else if (!inputFile) {
      inputFile = arg;
    } else if (!outputFile) {
      outputFile = arg;
    }
  }

  return { inputFile, outputFile, theme };
}

function main() {
  const { inputFile, outputFile, theme } = parseArgs();

  if (!inputFile) {
    console.error('用法: node mdnice_formatter.js <input.md> [output.html] [--theme=normal]');
    console.error('可用主题: normal, orangeheart, purple, green, blue');
    process.exit(1);
  }

  if (!fs.existsSync(inputFile)) {
    console.error(`❌ 文件不存在: ${inputFile}`);
    process.exit(1);
  }

  const markdownContent = fs.readFileSync(inputFile, 'utf8');
  console.error(`📖 读取文件: ${inputFile} (${markdownContent.length} 字符)`);
  console.error(`🎨 使用主题: ${theme}`);

  const html = convertToWechatHTML(markdownContent, theme);

  // 确定输出路径
  const finalOutput = outputFile || inputFile.replace(/\.md$/, '_wechat.html');

  fs.writeFileSync(finalOutput, html, 'utf8');
  console.error(`✅ 排版完成: ${finalOutput} (${html.length} 字符)`);

  // stdout 输出文件路径，供调用方捕获
  console.log(finalOutput);
}

main();
