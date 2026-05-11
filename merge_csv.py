import csv
import glob
import os
import re
import sys

##Use this script to merge all files into one very large csv

DATA_DIR = "data" #Folder To Save To
OUTPUT_PATH = "merged.csv" #File Name Of Result


##This expects you to have all your folders unzipped in data
##With a path like "\data\On_Time_2002_01\T_ONTIME_REPORTING.csv"
def find_csv_files():
    results = []
    for csv_path in glob.glob(os.path.join(DATA_DIR, "On_Time_*", "*.csv")): #Finds all folders that start with On_Time, all csv's inside those folders
        folder_name = os.path.basename(os.path.dirname(csv_path))
        match = re.search(r"On_Time_(\d{4})_(\d{2})$", folder_name, re.IGNORECASE) #Checks that folder name is formatted like XXXX_XX where every X is a digit
        if not match:
            print(f"  WARNING: Skipping unrecognized folder: {folder_name}")
            continue
        results.append(((int(match.group(1)), int(match.group(2))), folder_name, csv_path))

    results.sort(key=lambda x: x[0]) ## Sort the results, so we merge files in chronological order.
    return [(name, path) for _, name, path in results]


def merge():
    csv_files = find_csv_files()

    if not csv_files:
        sys.exit(f"ERROR: No CSV files found under '{DATA_DIR}' matching On_Time_YYYY_MM pattern.")

    print(f"Found {len(csv_files)} CSV file(s) to merge.")

    expected_header = None
    total_rows = 0
    writer = None

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as out_f:
        for i, (folder_name, csv_path) in enumerate(csv_files):
            print(f"  [{i+1}/{len(csv_files)}] {csv_path}")

            with open(csv_path, "r", newline="", encoding="utf-8", errors="replace") as in_f:
                reader = csv.DictReader(in_f)

                if reader.fieldnames is None:
                    print("WARNING: Empty or header-less file, skipping.")
                    continue

                header = list(reader.fieldnames)

                if expected_header is None:
                    expected_header = header 
                    writer = csv.DictWriter(out_f, fieldnames=header + ["source_folder"], extrasaction="ignore")
                    writer.writeheader()
                else:
                    ##Checking data integrity
                    missing = set(expected_header) - set(header)
                    extra = set(header) - set(expected_header)
                    if missing:
                        print(f"WARNING: Missing columns vs first file: {missing}")
                    if extra:
                        print(f"WARNING: Extra columns vs first file: {extra}")

                file_rows = 0
                for row in reader:
                    row["source_folder"] = folder_name
                    writer.writerow(row)
                    file_rows += 1

                total_rows += file_rows
                print(f"^ {file_rows:,} rows")

    print(f"\nDone. {total_rows:,} rows written to '{OUTPUT_PATH}'.")


if __name__ == "__main__":
    if not os.path.isdir(DATA_DIR):
        sys.exit(f"ERROR: Data directory '{DATA_DIR}' was not found.")
    merge()