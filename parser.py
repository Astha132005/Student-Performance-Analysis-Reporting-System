import pandas as pd


def parse_excel(file_path):

    # ------------------------------
    # STEP 1: Read raw file
    # ------------------------------
    df_raw = pd.read_excel(file_path, header=None)

    # ------------------------------
    # STEP 2: Find header row
    # ------------------------------
    header_row = None

    for i, row in df_raw.iterrows():
        row_str = " ".join([str(x).lower() for x in row if pd.notna(x)])

        if ("reg" in row_str or "regd" in row_str) and "name" in row_str:
            header_row = i
            break

    if header_row is None:
        raise Exception("❌ Header row not found")

    # ------------------------------
    # STEP 3: Reload with header
    # ------------------------------
    df = pd.read_excel(file_path, header=header_row)

    # Clean column names
    df.columns = (
        df.columns.astype(str)
        .str.replace('\n', ' ', regex=True)
        .str.strip()
        .str.lower()
    )

    print("\n📂 FILE:", file_path)
    print("Detected Columns:", df.columns.tolist())

    # ------------------------------
    # STEP 4: Find basic columns
    # ------------------------------
    def find_col(keywords):
        for col in df.columns:
            for key in keywords:
                if key in col:
                    return col
        return None

    reg_col = find_col(["reg", "regd"])
    name_col = find_col(["name"])

    if not reg_col or not name_col:
        raise Exception("❌ Reg/Name column not found")

    # ------------------------------
    # STEP 5: Find "Mark Analysis"
    # ------------------------------
    cols = list(df.columns)

    ma_index = None
    for i, col in enumerate(cols):
        if "mark analysis" in col:
            ma_index = i
            break

    if ma_index is None:
        raise Exception("❌ Mark Analysis section not found")

    # ------------------------------
    # STEP 6: Extract CO + TOTAL columns
    # ------------------------------
    analysis_cols = cols[ma_index + 1:]

    if len(analysis_cols) < 2:
        raise Exception("❌ Not enough columns after Mark Analysis")

    total_col = analysis_cols[-1]

    # 🔥 FIX: Only keep valid CO columns
    co_cols = [col for col in analysis_cols[:-1] if "co" in col]

    # Sort CO columns properly (CO1, CO2, ...)
    def co_sort(x):
        try:
            return int(''.join(filter(str.isdigit, x)))
        except:
            return 999

    co_cols = sorted(co_cols, key=co_sort)

    print("Detected CO Columns:", co_cols)

    # ------------------------------
    # STEP 7: Clean rows
    # ------------------------------
    df = df.dropna(subset=[reg_col])
    df = df[df[reg_col] != 0]

    data = []

    # ------------------------------
    # STEP 8: Extract student data
    # ------------------------------
    for _, row in df.iterrows():
        try:
            reg_value = row[reg_col]

            if pd.isna(reg_value):
                continue

            reg_no = str(int(reg_value))
            name = str(row[name_col]).strip()

            # TOTAL
            total = pd.to_numeric(row[total_col], errors='coerce')
            total = float(total) if pd.notna(total) else 0

            student = {
                "reg_no": reg_no,
                "name": name,
                "total": total
            }

            # ------------------------------
            # CO VALUES (FIXED)
            # ------------------------------
            for i, col in enumerate(co_cols):
                val = pd.to_numeric(row[col], errors='coerce')
                student[f"co{i+1}"] = float(val) if pd.notna(val) else 0

            # ------------------------------
            # 🔥 DO NOT FORCE FAKE ZEROS
            # ------------------------------
            # Only fill if column truly missing
            for i in range(len(co_cols) + 1, 6):
                student[f"co{i}"] = 0

            data.append(student)

        except Exception as e:
            print("⚠️ Row skipped:", e)
            continue

    print(f"✅ Parsed {len(data)} students")

    return data