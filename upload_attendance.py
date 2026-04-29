import pandas as pd
from db import get_connection


def upload_attendance():

    # READ FILE
    df = pd.read_excel("ATTENDANCE.xlsx")

    # CLEAN COLUMNS
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(".", "", regex=False)
    )

    print("Columns:", df.columns.tolist())

    # EXACT COLUMN NAMES FROM YOUR FILE
    reg_col = "REGD NO"
    co_cols = ["CO1", "CO2", "CO3", "CO4", "CO5"]

    # DB CONNECTION
    conn = get_connection()
    cursor = conn.cursor(buffered=True)

    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", ("OS",))
    subject_id = cursor.fetchone()[0]

    count = 0

    # INSERT
    for _, row in df.iterrows():
        try:
            if pd.isna(row[reg_col]):
                continue

            reg = str(int(row[reg_col]))

            cursor.execute(
                "SELECT student_id FROM students WHERE reg_no=%s",
                (reg,)
            )
            res = cursor.fetchone()

            if not res:
                continue

            student_id = res[0]

            values = [
                float(row[c]) if pd.notna(row[c]) else 0
                for c in co_cols
            ]

            print("ATTEND INSERT:", reg, values)

            cursor.execute("""
                INSERT INTO attendance (
                    student_id, subject_id,
                    co1, co2, co3, co4, co5
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (student_id, subject_id, *values))

            count += 1

        except Exception as e:
            print("Skipped:", e)

    conn.commit()
    conn.close()

    print("✅ ATTENDANCE uploaded:", count)


if __name__ == "__main__":
    upload_attendance()