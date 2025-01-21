import pandas as pd
from pathlib import Path



def filter_timeseries(nickname, elements):
    # Create the output directory
    directory = Path('data/common/timeseries/master')
    output_directory = directory.parent / nickname
    output_directory.mkdir(parents=True, exist_ok=True)
    
    for file in directory.glob('*.csv'):
        # Read the original CSV file
        df = pd.read_csv(file, header=None)

        
        # If the first cell is "T0001", we assume the file has no header
        if df.iloc[0, 0] == "T0001":
            include_header = False
        else:
            df.columns = df.iloc[0]
            df.columns = [""] + list(df.columns[1:])
            df = df.iloc[1:]
            include_header= True
        
        # # Filter the dataframe based on the elements parameter
        if isinstance(elements, int):
            df = df.head(elements)
        elif isinstance(elements, list):
            df = df[df.iloc[:, 0].isin([f"T{i:04}" for i in elements])]


        # Write the filtered dataframe to the output directory
        output_file_path = output_directory / file.name
        df.to_csv(output_file_path, index=False, header=include_header)



# lengths = [48, 72, 91, 96, 121, 365, 730]
# start_element = 12 # for a length of 730, maximum value is 12

lengths = [73]
start_element = 58 # for a length of 730, maximum value is 12

for length in lengths:
    spacing = 8760 // length
    elements = list(range(start_element, 8761, spacing))

    # If the last element is beyond 8760, remove it
    if elements[-1] > 8760:
        elements.pop()

    # name = f"test_{length:03d}"
    name = f"spacing_120"


    print(f' >> legnth: {length}')
    print(f' >> spacing: {spacing}')
    print(f' >> name: {name}')

    print(elements[0])
    filter_timeseries(name, elements)
