import sys
import json
import re

# Global variables to store input and output file paths

global input_value 
global output_value
global metering_procedure
global output_data

def init_globals():
    global input_value
    global output_value
    global metering_procedure
    global output_data

    input_value = None
    output_value = None
    metering_procedure = 'RLM'
    output_data = []

init_globals()

def read_json_file(file_path):
    """
    Read a JSON file and return the content as a dictionary.
    Args:
        file_path (str): The path to the JSON file.
    Returns:
        dict: The content of the JSON file as a dictionary.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        data = json.load(file)
    return data

def check_param():
    global input_value
    global output_value
    global metering_procedure
    """
    Main function to process command-line arguments for input and output file paths.
    The function expects command-line arguments in the format:
    - in=<input_file>
    - out=<output_file>
    It validates the presence of these arguments and ensures the input file has a .json extension.
    If the input file does not have a .json extension, it appends the extension.
    Prints:
        - The input and output parameters if provided.
        - Error messages if the parameters are missing or invalid.
    Exits:
        - With status code 1 if the input file has an invalid extension.
    """
    for arg in sys.argv[1:]:
        if arg.startswith("in="):
            input_value = arg.split("=", 1)[1]
        elif arg.startswith("out="):
            output_value = arg.split("=", 1)[1]
        elif arg.startswith("meteringProcedure="):
            metering_procedure = arg.split("=", 1)[1]   

    if input_value:
        print(f"Input from: {input_value}")
    else:
        print("No input parameter found. Use 'in=' to specify an input file")
        sys.exit(1)

    if not input_value.endswith(".json"):
        if "." in input_value:
            print("Error: Input file has an invalid extension. Only .json files are supported")
            sys.exit(1)
        else:
            input_value += ".json"

    if output_value:
        print(f"Output to: {output_value}")
    else:
        print("No output parameter found. Use 'out=' to specify an output file")
        sys.exit(1)

    if not output_value.endswith(".csv"):
        if "." in output_value:
            print("Error: Output file has an invalid extension. Only .json files are supported")
            sys.exit(1)
        else:
            output_value += ".csv"

    print(f"Metering Procedure: {metering_procedure}. Use 'meteringProcedure=' to specify SLP or RLM")

def parse_for_each(entry, malo, rule, exp):
    global metering_procedure
    global output_data

    if not rule['meteringProcedure_code'] == metering_procedure:
        print(f"{entry['idText']} / malo {malo['idText']} / {rule['meteringProcedure_code']} contains 'forEach': Ignored due to metering procedure")    
        return
    print(f"{entry['idText']} / malo {malo['idText']} / {rule['meteringProcedure_code']} contains 'forEach': {exp}")

    # Extract the melo from the forEach
    match = re.search(r'forEach\((Z[^,]*),', exp)
    if match:
        melo = match.group(1).strip()
        mapping = f"{entry['idText']}, {melo}, {malo['idText']}"
        print(f"OUT {mapping}")
        output_data.append(mapping)

def parse_substitute_market_locations(entry, malo, rule, exp):
    global metering_procedure

    if not rule['meteringProcedure_code'] == metering_procedure:
        print(f"{entry['idText']} / malo {malo['idText']} / {rule['meteringProcedure_code']} contains 'substituteMarketLocations': Ignored due to metering procedure")    
        return
    print(f"Model {entry['idText']}, malo {malo['idText']}, procedure {rule['meteringProcedure_code']} contains 'substituteMarketLocations': {exp}")

    # Extract the melo from the substituteMarketLocations
    match = re.search(r'-substituteMarketLocations\((Z[^_]*)_', exp)
    if match:
        melo = match.group(1).strip()
        mapping = f"{entry['idText']}, {melo}, {malo['idText']}"
        print(f"OUT {mapping}")
        output_data.append(mapping)

def parse_entry(entry, entry_index): 
    if 'idText' not in entry:
        print("Entry does not have 'idText' attribute")
        return

    idText = entry['idText']    
    print(f"Entry ({entry_index}): {idText}")

    if 'marketLocations' in entry and isinstance(entry['marketLocations'], list):
        for malo in entry['marketLocations']:
            maloIdText = malo.get('idText')
            if 'calculationRules' in malo and isinstance(malo['calculationRules'], list):
                for rule in malo['calculationRules']:
                    exp = rule['formula']['expressionSubstituted']
                    if 'substituteMarketLocations(' in exp:
                        parse_substitute_market_locations(entry, malo, rule, exp)
                    elif 'forEach(' in exp:
                        parse_for_each(entry, malo, rule, exp)


if __name__ == "__main__":
    init_globals()
    check_param()
    data = read_json_file(input_value)
    print(f"Type of data: {type(data)}")
    print(f"Length of data: {len(data)}")
    for entry in data:
        entry_index = data.index(entry)
        if entry.get('conceptType_code') == "SAPTEMPLATE":
            continue
        parse_entry(entry, entry_index)
    
    # print the output data
    print(f"Writing output data to {output_value}")
    
    with open(output_value, 'w', encoding='utf-8') as file:
        for line in output_data:
            file.write(f"{line}\n")
    print("Done")
