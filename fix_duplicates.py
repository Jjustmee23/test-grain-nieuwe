#!/usr/bin/env python3
"""
Script to fix duplicate message definitions in Django .po files
"""

import re
from collections import defaultdict

def fix_po_duplicates(po_file_path):
    """Fix duplicate message definitions in a .po file"""
    
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into message blocks
    blocks = re.split(r'\n(?=#:)', content)
    
    # Group by msgid
    msgid_groups = defaultdict(list)
    
    for block in blocks:
        if not block.strip():
            continue
            
        # Extract msgid
        msgid_match = re.search(r'msgid "(.*?)"', block, re.DOTALL)
        if msgid_match:
            msgid = msgid_match.group(1)
            msgid_groups[msgid].append(block)
    
    # Process duplicates
    new_blocks = []
    processed_msgids = set()
    
    for msgid, blocks in msgid_groups.items():
        if len(blocks) == 1:
            # No duplicate, keep as is
            new_blocks.append(blocks[0])
            continue
            
        if msgid in processed_msgids:
            continue
            
        # Consolidate source references
        all_sources = []
        msgstr = None
        
        for block in blocks:
            # Extract source references
            sources = re.findall(r'#: ([^\n]+)', block)
            all_sources.extend(sources)
            
            # Extract msgstr
            msgstr_match = re.search(r'msgstr "(.*?)"', block, re.DOTALL)
            if msgstr_match and not msgstr:
                msgstr = msgstr_match.group(1)
        
        # Create consolidated block
        if all_sources and msgstr is not None:
            consolidated_block = '\n'.join([f'#: {source}' for source in sorted(set(all_sources))])
            consolidated_block += f'\nmsgid "{msgid}"\nmsgstr "{msgstr}"\n'
            new_blocks.append(consolidated_block)
            processed_msgids.add(msgid)
    
    # Write back to file
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_blocks))
    
    print(f"Fixed duplicates in {po_file_path}")

if __name__ == "__main__":
    fix_po_duplicates("locale/ar/LC_MESSAGES/django.po") 