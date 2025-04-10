# This module is used to record the sizes of components in the binary.
# Each entry includes the following fields: 
#   - address offset
#   - component type
#   - component size
#   - the extracting function that retrieved the component

import csv

class SizeBook:
    def __init__(self):
        self.book = []
        
    def add(self, offset, component_type, size):
        entry = (offset, component_type, size)
        self.book.append(entry)
        
    def dedup(self):
        # deduplicate based on offset and component type
        seen = set()
        deduped = []
        for entry in self.book:
            if (entry[0], entry[1]) not in seen:
                seen.add((entry[0], entry[1]))
                deduped.append(entry)
        self.book = deduped
        
    def write_to(self, file_path):
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self.book)
            
    def __str__(self):
        output = []
        for entry in self.book:
            output.append(f"{entry['offset']}, {entry['component_type']}, {entry['size']}")
        return "\n".join(output)

_instance = None

def get_book():
    global _instance
    if _instance is None:
        _instance = SizeBook()
    return _instance