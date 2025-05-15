import pandas as pd

# File paths
excel_path = '/home/mobase/Rasp/final/MKBD_selected_Diag_01.xlsx'
txt_path = 'final_allservices_testcase_.txt'

# Read the Excel file
df = pd.read_excel(excel_path)

# Filter rows where column I contains "checkbox is enabled"
filtered_df = df[df.iloc[:, 8].astype(str).str.upper() == "TRUE"]

# Select and reorder specific columns: A, F, E, C, G
df_subset = filtered_df.iloc[:, [0, 5, 2, 4, 6]]

# Format each row with '-' after the first column
def format_row(row):
    row = row.astype(str).tolist()
    return f"{row[0]} , {' , '.join(row[1:])}"

# Format header
header = df_subset.columns.astype(str).tolist()
header_line = f"{header[0]} , {' , '.join(header[1:])}"

# Format data rows
data_lines = df_subset.apply(format_row, axis=1).tolist()

# Combine header and data
all_lines = [header_line] + data_lines

# Write to text file
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write('#')
    for line in all_lines:
        f.write(line + '\n')

print(f"✅ Filtered rows where checkbox is enabled saved to: {txt_path}")
