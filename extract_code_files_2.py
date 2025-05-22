#!/usr/bin/env python3
import os
import sys
import re

def get_input_arguments():
    """Parse command-line arguments or prompt for missing input."""
    if len(sys.argv) >= 2:
        return sys.argv[1]
    
    input_file = input("Enter the path to the compacted input file: ")
    return input_file

def is_readable_text_file(file_path):
    """Check if the file exists and is a readable text file."""
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    if not os.path.isfile(file_path):
        return False, "Not a regular file"
    
    # Check for binary content
    try:
        with open(file_path, 'rb') as f:
            data = f.read(1024)
            if b'\0' in data:  # Null bytes indicate binary file
                return False, "File appears to be binary"
        
        # Try reading with common encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'utf-16']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return True, encoding
            except UnicodeDecodeError:
                continue
        
        return False, "Could not determine text encoding"
    except Exception as e:
        return False, str(e)

def normalize_path(path_str):
    """Normalize path by handling quotes and escapes."""
    # Remove surrounding quotes if present
    if (path_str.startswith("'") and path_str.endswith("'")) or \
       (path_str.startswith("`") and path_str.endswith("`")):
        path_str = path_str[1:-1]
    
    # Handle escaped spaces
    path_str = path_str.replace("\\ ", " ")
    
    return path_str.strip()

def ensure_directory_exists(file_path):
    """Create directory for the file if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"  Created directory: {directory}")
            return True
        except Exception as e:
            print(f"  Error creating directory {directory}: {e}")
            return False
    return True

def extract_files(input_file_path, encoding):
    """Extract individual files from the compacted input file."""
    # Statistics
    blocks_found = 0
    successful_extractions = 0
    rejected_blocks = []
    overwrites = []
    
    # RegEx patterns
    heading_pattern = re.compile(r'^#\s+(.*?)$')
    code_fence_start_pattern = re.compile(r'^```(\w*)$')
    code_fence_end_pattern = re.compile(r'^```$')
    comment_filename_pattern = re.compile(r'^//\s+(.*?)$')
    
    # Track created files to detect overwrites
    created_files = set()
    
    try:
        # Read all lines from input file
        with open(input_file_path, 'r', encoding=encoding) as input_file:
            lines = input_file.readlines()
        
        # Process all lines
        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\r\n')
            
            # Check for code fence start
            code_fence_match = code_fence_start_pattern.match(line)
            if code_fence_match:
                blocks_found += 1
                file_extension = code_fence_match.group(1)
                filename = None
                
                # Check preceding line for Format 1 (# path/filename)
                if i > 0:
                    prev_line = lines[i-1].rstrip('\r\n')
                    heading_match = heading_pattern.match(prev_line)
                    if heading_match:
                        filename = normalize_path(heading_match.group(1))
                
                # If no filename yet, check next line for Format 2 (// path/filename)
                if not filename and i+1 < len(lines):
                    next_line = lines[i+1].rstrip('\r\n')
                    comment_match = comment_filename_pattern.match(next_line)
                    if comment_match:
                        filename = normalize_path(comment_match.group(1))
                        # Do not skip this line, so it will be included in the content
                
                # If no valid filename found, reject this block
                if not filename:
                    rejected_blocks.append((f"Block at line {i+1}", "No valid filename marker found"))
                    # Skip to end of this block or file
                    while i < len(lines):
                        if code_fence_end_pattern.match(lines[i].rstrip('\r\n')):
                            break
                        i += 1
                    i += 1
                    continue
                
                # Collect content until closing fence
                content_lines = []
                has_closing_fence = False
                start_i = i + 1
                
                while i+1 < len(lines):
                    i += 1
                    line = lines[i].rstrip('\r\n')
                    if code_fence_end_pattern.match(line):
                        has_closing_fence = True
                        break
                    content_lines.append(line)
                
                # If no closing fence found, reject this block
                if not has_closing_fence:
                    rejected_blocks.append((filename, "Missing closing code fence"))
                    i += 1
                    continue
                
                # Process the valid block
                if ensure_directory_exists(filename):
                    # Check for overwrites
                    if filename in created_files:
                        overwrites.append(filename)
                        print(f"  Warning: Overwriting previously extracted file: {filename}")
                    
                    try:
                        with open(filename, 'w', encoding='utf-8') as output_file:
                            output_file.write('\n'.join(content_lines))
                        
                        created_files.add(filename)
                        print(f"Extracted: {filename}")
                        successful_extractions += 1
                    except Exception as e:
                        error_msg = f"Error writing file: {e}"
                        print(f"  Failed: {filename} - {error_msg}")
                        rejected_blocks.append((filename, error_msg))
                else:
                    rejected_blocks.append((filename, "Failed to create directory"))
            
            i += 1
        
        return blocks_found, successful_extractions, rejected_blocks, overwrites
    
    except Exception as e:
        print(f"Error processing input file: {e}")
        sys.exit(1)

def main():
    # Get input file path
    input_file_path = get_input_arguments()
    
    print(f"Processing compacted file: {input_file_path}")
    
    # Validate input file
    is_valid, result = is_readable_text_file(input_file_path)
    if not is_valid:
        print(f"Error: {result}")
        sys.exit(1)
    
    encoding = result
    print(f"Input file encoding detected as: {encoding}")
    
    # Extract files
    blocks_found, successful_extractions, rejected_blocks, overwrites = extract_files(input_file_path, encoding)
    
    # Print summary statistics
    print("\nExtraction complete!")
    print(f"Total code blocks found: {blocks_found}")
    print(f"Files successfully extracted: {successful_extractions}")
    
    if rejected_blocks:
        print(f"Blocks rejected: {len(rejected_blocks)}")
        print("\nRejected blocks:")
        for block_id, reason in rejected_blocks:
            print(f"  - {block_id}: {reason}")
    
    if overwrites:
        print(f"\nFiles overwritten: {len(overwrites)}")
        print("Note: Multiple code blocks with the same filename were found.")
        print("Each file contains the content from the last matching block.")
    
if __name__ == "__main__":
    main()
