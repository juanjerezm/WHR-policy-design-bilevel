import pandas as pd



length = 73


start_element = list(range(9, 17))

start_element = [element + 48 for element in start_element]

# start_element = 11 # for a length of 730, maximum value is 12

spacing = 8760 // length
# spacing = 120
# elements = list(range(start_element, 8761, spacing))

for hour in start_element:

    elements = list(range(hour, 8761, spacing))
    print(f"--> Hour: {hour}")

    files = [
        'data/common/timeseries/master/ts-electricity-carbon.csv',
        'data/common/timeseries/master/ts-electricity-price.csv',
        'data/common/timeseries/master/ts-demand-heat.csv',
    ]

    for file in files:
        df = pd.read_csv(file, header=None, names=["time", "price"])

        df_short = df[df.iloc[:, 0].isin([f"T{i:04}" for i in elements])]

        # calculate total mean and short mean

        total_mean = df["price"].mean()
        short_mean = df_short["price"].mean()
        total_std = df["price"].std()
        short_std = df_short["price"].std()
        print(df_short.head(5))

        # print the difference in percent
        print(f"File: {file}")
        # print(f"Total mean: {total_mean}")
        # print(f"Short mean: {short_mean}")
        print(f"Difference: {100 * (short_mean - total_mean) / total_mean:.2f}%")
        print(f"Diff std: {100 * (short_std - total_std) / total_std:.2f}%")
        # print(f"spacing: {spacing}")
        # print(f"length: {length}")

    print("--------")
