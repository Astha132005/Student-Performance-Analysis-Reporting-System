import pandas as pd
from db import get_connection


def upload_students():

    # ------------------------------
    # READ FILE
    # ------------------------------
    df = pd.read_excel("ML.xlsx", header=0)

    # CLEAN COLUMN NAMES
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    print("Detected Columns:", df.columns.tolist())

    # ------------------------------
    # FIND REQUIRED COLUMNS
    # ------------------------------
    def find_col(keyword):
        for col in df.columns:
            if keyword in col:
                return col
        return None

    reg_col = find_col("REG")
    name_col = find_col("NAME")

    if not reg_col or not name_col:
        raise Exception("❌ Could not detect REG or NAME column")

    print("Using REG column:", reg_col)
    print("Using NAME column:", name_col)

    # ------------------------------
    # CONNECT DB
    # ------------------------------
    conn = get_connection()
    cursor = conn.cursor(buffered=True)

    # INSERT SUBJECT (once)
    cursor.execute("""
        INSERT INTO subjects (subject_name, semester)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE subject_name=subject_name
    """, ("OS", 3))

    conn.commit()

    # ------------------------------
    # INSERT STUDENTS
    # ------------------------------
    count = 0

    for _, row in df.iterrows():

        try:
            reg_val = row[reg_col]

            if pd.isna(reg_val):
                continue

            reg_no = str(int(reg_val))
            name = str(row[name_col]).strip()

            print("Inserting:", reg_no, name)

            cursor.execute("""
                INSERT INTO students (reg_no, name, branch, semester, pass_year)
                VALUES (%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE name=name
            """, (reg_no, name, "AIML", 3, 2028))

            count += 1

        except Exception as e:
            print("⚠️ Skipped row:", e)

    conn.commit()
    conn.close()

    print(f"✅ {count} students uploaded successfully")


if __name__ == "__main__":
    upload_students()