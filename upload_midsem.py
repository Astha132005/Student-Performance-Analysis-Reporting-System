import pandas as pd
from db import get_connection


def upload_midsem():

    # ------------------------------
    # READ FILE
    # ------------------------------
    df = pd.read_excel("MIDSEM.xlsx")

    # ------------------------------
    # CLEAN COLUMNS
    # ------------------------------
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    print("Detected Columns:", df.columns.tolist())

    # ------------------------------
    # FIND REG COLUMN
    # ------------------------------
    reg_col = None
    for col in df.columns:
        if "REG" in col:
            reg_col = col
            break

    if not reg_col:
        raise Exception("❌ REG column not found")

    print("Using REG column:", reg_col)

    # ------------------------------
    # FIND CO COLUMNS
    # ------------------------------
    co_cols = []

    for col in df.columns:
        if "CO" in col:
            num = ''.join(filter(str.isdigit, col))
            if num:
                co_cols.append((int(num), col))

    co_cols = [col for _, col in sorted(co_cols)]

    print("Detected CO columns:", co_cols)

    if len(co_cols) < 5:
        raise Exception("❌ CO columns not properly detected")

    # ------------------------------
    # CONNECT DB (FIXED HERE)
    # ------------------------------
    conn = get_connection()
    cursor = conn.cursor(buffered=True)   

    # ------------------------------
    # GET SUBJECT ID
    # ------------------------------
    cursor.execute(
        "SELECT subject_id FROM subjects WHERE subject_name=%s",
        ("OS",)
    )
    res = cursor.fetchone()

    if not res:
        raise Exception("❌ Subject not found in DB")

    subject_id = res[0]

    count = 0

    # ------------------------------
    # INSERT DATA
    # ------------------------------
    for _, row in df.iterrows():
        try:
            reg_val = row[reg_col]

            if pd.isna(reg_val):
                continue

            reg = str(int(reg_val))

            # ---- GET STUDENT ----
            cursor.execute(
                "SELECT student_id FROM students WHERE reg_no=%s",
                (reg,)
            )
            res = cursor.fetchone()

            if not res:
                print("❌ Student not found:", reg)
                continue

            student_id = res[0]

            # ---- GET CO VALUES ----
            values = [
                float(row[c]) if pd.notna(row[c]) else 0
                for c in co_cols[:5]
            ]

            print("MIDSEM INSERT:", reg, values)

            # ---- INSERT ----
            cursor.execute("""
                INSERT INTO midsem (
                    student_id, subject_id,
                    co1, co2, co3, co4, co5
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (student_id, subject_id, *values))

            count += 1

        except Exception as e:
            print("⚠️ Skipped row:", e)

    # ------------------------------
    # COMMIT
    # ------------------------------
    conn.commit()
    conn.close()

    print(f"✅ MIDSEM uploaded successfully: {count} rows")


if __name__ == "__main__":
    upload_midsem()