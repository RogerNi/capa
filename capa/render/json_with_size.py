from collections import defaultdict
import json
import csv



class JsonWithSize:
    def __init__(self):
        self.data = defaultdict(list)
        self.all_features = set()
        self.all_characteristics_desc = set()
        self.size_book = None
        self.string_map = None
        
    def change_scope(self, scope_name, scope_offset):
        self.scope = (scope_name, scope_offset)
        
    def add(self, feature_offset, feature_name, feature_desc=None):
        if len(feature_offset) == 0 or feature_name is "match":
            return
        self.data[self.scope].append((feature_offset, feature_name, feature_desc, self.decide_scope(feature_name, feature_desc)))
        self.all_features.add(feature_name)
        if feature_name is "characteristic":
            self.all_characteristics_desc.add(feature_desc)
        
    def decide_scope(self, feature_name, feature_desc):
        if feature_name in ["offset"]:
            return "instruction"
        elif feature_name in ["characteristic"]:
            if feature_desc in ["tight loop", "stack string"]:
                return "basic_block"
            elif feature_desc in ["embedded pe"]:
                return "embedded_pe"
            elif feature_desc in ["calls to"]:
                return "function_calls_to"
            elif feature_desc in ["loop"]:
                return "function"
            else:
                return "instruction"
        else:
            return "instruction"
        
    def load_size_and_string_map(self, size_book_path, string_map_path):
        # csv files
        size_book = {}
        with open(size_book_path, "r") as size_book_file:
            reader = csv.reader(size_book_file)
            for row in reader:
                if len(row) == 3:
                    key_raw, feature_type, size_str = row
                    size = int(size_str)
                    if "string:" in feature_type:
                        feature_type = "string"

                    if key_raw.startswith("file("):
                        key_type = "file"
                    elif key_raw.startswith("absolute("):
                        key_type = "absolute"
                    else:
                        raise ValueError(f"Unknown address type in: {key_raw}")

                    addr_str = key_raw.split("(")[1].rstrip(")")
                    address = int(addr_str, 16)

                    key = (key_type, address, feature_type)
                    size_book[key] = size

        addr_link_map = {} # string_virtual_addr -> list of (pointer_addr, file_offset_addr)

        with open(string_map_path, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 4:
                    continue  # skip malformed lines

                # Extract and convert hex addresses
                addr1_str = parts[0].split("(")[1].rstrip(")")
                addr2_str = parts[1].split("(")[1].rstrip(")")
                addr3_str = parts[2].split("(")[1].rstrip(")")

                addr1 = int(addr1_str, 16)
                addr2 = int(addr2_str, 16)
                addr3 = int(addr3_str, 16)

                # Map: first -> (second, third)
                addr_link_map[addr1] = (addr2, addr3)
                
        self.size_book = size_book 
        self.string_map = addr_link_map
        
    def find_all_sizes(self):
        if self.size_book is None:
            raise ValueError("Size book not loaded. Please load size book first.")
        new_self_data = {}
        for key, entries in self.data.items():
            new_entries = []
            for entry in entries:
                addr_info_list = entry[0]
                scope = entry[3]
                new_addr_info_list = []
                for addr_info in addr_info_list:
                    new_addr_info_list.append(addr_info.model_dump())
                new_entries.append((new_addr_info_list, entry[1], entry[2], entry[3]))
                for i, addr_info in enumerate(addr_info_list):
                    if addr_info.type == "absolute":
                        addr = addr_info.value
                        new_entries[-1][0][i]["size"] = self.size_book.get(("absolute", addr, scope), None)
            new_self_data[key] = new_entries
        self.data = new_self_data
        
    def dereference_all_string(self):
        if self.string_map is None:
            raise ValueError("String map not loaded. Please load string map first.")
        new_self_data = {}
        for key, entries in self.data.items():
            new_entries = []
            for entry in entries:
                addr_info_list = entry[0]
                scope = entry[3]
                new_addr_info_list = []
                for addr_info in addr_info_list:
                    new_addr_info_list.append(addr_info)
                new_entries.append((new_addr_info_list, entry[1], entry[2], entry[3]))
                if "string" in entry[1]:
                    for i, addr_info in enumerate(addr_info_list):
                        if addr_info["type"] == "absolute":
                            addr = addr_info["value"]
                            if addr in self.string_map:
                                str_virtual_addr = self.string_map[addr][0]
                                str_file_offset_addr = self.string_map[addr][1]
                                new_entries[-1][0][i]["str_virt_addr"] = str_virtual_addr
                                new_entries[-1][0][i]["str_file_offset_addr"] = str_file_offset_addr
                                str_size = self.size_book.get(("file", str_file_offset_addr, "string"), None)
                                new_entries[-1][0][i]["str_size"] = str_size
            new_self_data[key] = new_entries
        self.data = new_self_data
        
        
    def write_to(self, file_path):
        self.find_all_sizes()
        self.dereference_all_string()
        def convert_keys_to_str(obj):
            if isinstance(obj, dict):
                return {str(k): convert_keys_to_str(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_keys_to_str(i) for i in obj]
            else:
                return obj

        with open(file_path, "w") as jsonfile:
            json.dump(convert_keys_to_str(self.data), jsonfile, indent=4, default=vars)
            
        print(f"All features: {self.all_features}")
        print(f"All characteristics description: {self.all_characteristics_desc}")
            
    def __str__(self):
        output = []
        for (scope, scope_offset), features in self.data.items():
            output.append(f"{scope}, {scope_offset}:")
            for feature_offset, feature_name in features:
                output.append(f"  - {feature_offset}: {feature_name}")
        return "\n".join(output)
    
_instance = None

def get_json_with_size():
    global _instance
    if _instance is None:
        _instance = JsonWithSize()
    return _instance