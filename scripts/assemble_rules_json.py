import json
import os
import re

def assemble_json():
    base_dir = r"d:/Work/Meaw - Q/Scraper/pmanager-scrape/docs/manual/sections"
    output_file = r"d:/Work/Meaw - Q/Scraper/pmanager-scrape/docs/pmanager_rules.json"
    
    sections = []
    
    for i in range(1, 35):
        filename = f"section_{i:02d}.md"
        filepath = os.path.join(base_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found.")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            continue
            
        # Extract title from the first line: "# 1. Introduction" -> "1. Introduction"
        title_line = lines[0].strip()
        title_match = re.match(r'^#\s*(.*)$', title_line)
        if title_match:
            title = title_match.group(1)
        else:
            title = title_line
            
        # Content is everything after the title line
        content = "".join(lines[1:]).strip()
        
        sections.append({
            "section": i,
            "title": title,
            "content": content
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully assembled {len(sections)} sections into {output_file}")

if __name__ == "__main__":
    assemble_json()
