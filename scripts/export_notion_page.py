#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv('NOTION_TOKEN'))

page_id = sys.argv[1] if len(sys.argv) > 1 else '31a62152-0e3f-8156-8aff-fe792120c3da'

def get_text(rich_text):
    return ''.join([t.get('plain_text', '') for t in rich_text])

def read_blocks(block_id, indent=0):
    content = []
    blocks = notion.blocks.children.list(block_id=block_id)
    for block in blocks['results']:
        btype = block['type']
        b = block[btype]
        prefix = '  ' * indent
        line = ''
        if btype == 'paragraph':
            text = get_text(b.get('rich_text', []))
            if text:
                line = prefix + text
        elif btype.startswith('heading_'):
            level = int(btype[-1])
            text = get_text(b.get('rich_text', []))
            line = prefix + '#' * level + ' ' + text
        elif btype == 'bulleted_list_item':
            text = get_text(b.get('rich_text', []))
            line = prefix + '- ' + text
        elif btype == 'numbered_list_item':
            text = get_text(b.get('rich_text', []))
            line = prefix + '1. ' + text
        elif btype == 'quote':
            text = get_text(b.get('rich_text', []))
            line = prefix + '> ' + text
        elif btype == 'callout':
            text = get_text(b.get('rich_text', []))
            line = prefix + '> 💡 ' + text
        elif btype == 'divider':
            line = prefix + '---'
        if line:
            content.append(line)
        if block.get('has_children'):
            content.extend(read_blocks(block['id'], indent))
    return content

lines = read_blocks(page_id)
print('\n'.join(lines))
