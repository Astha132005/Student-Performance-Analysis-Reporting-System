import pandas as pd
from db import get_connection


def upload_component(file_stream, component, subject_name):
    """
    Parse an uploaded .xlsx file and insert CO data into the correct table.

    Args:
        file_stream: file-like object (from request.files)
        component: 'midsem' | 'quiz' | 'assignment' | 'attendance'
        subject_name: e.g. 'ML', 'DVA'

    Returns:
        dict with 'success', 'count', 'errors', 'skipped'
    """

    VALID_COMPONENTS = ('midsem', 'quiz', 'assignment', 'attendance')
    if component not in VALID_COMPONENTS:
        return {"success": False, "count": 0, "errors": [f"Invalid component: {component}"], "skipped": 0}

    # ---- READ EXCEL ----
    try:
        df = pd.read_excel(file_stream)
    except Exception as e:
        return {"success": False, "count": 0, "errors": [f"Cannot read Excel file: {str(e)}"], "skipped": 0}

    # ---- CLEAN COLUMNS ----
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    # ---- FIND REG COLUMN ----
    reg_col = None
    for col in df.columns:
        if "REG" in col:
            reg_col = col
            break

    if not reg_col:
        return {"success": False, "count": 0, "errors": ["REG column not found in Excel file"], "skipped": 0}

    # ---- FIND CO COLUMNS ----
    co_cols = []
    for col in df.columns:
        if "CO" in col:
            num = ''.join(filter(str.isdigit, col))
            if num:
                co_cols.append((int(num), col))

    co_cols = [col for _, col in sorted(co_cols)]

    if len(co_cols) < 5:
        return {"success": False, "count": 0,
                "errors": [f"Need at least 5 CO columns, found {len(co_cols)}: {co_cols}"], "skipped": 0}

    # ---- DB CONNECTION ----
    conn = get_connection()
    cursor = conn.cursor(buffered=True)

    # ---- GET SUBJECT ID ----
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (subject_name,))
    res = cursor.fetchone()

    if not res:
        conn.close()
        return {"success": False, "count": 0, "errors": [f"Subject '{subject_name}' not found in database"], "skipped": 0}

    subject_id = res[0]

    count = 0
    skipped = 0
    errors = []

    # ---- INSERT DATA ----
    for idx, row in df.iterrows():
        try:
            reg_val = row[reg_col]

            if pd.isna(reg_val):
                skipped += 1
                continue

            reg = str(int(reg_val))

            # GET STUDENT
            cursor.execute("SELECT student_id FROM students WHERE reg_no=%s", (reg,))
            res = cursor.fetchone()

            if not res:
                errors.append(f"Row {idx + 2}: Student {reg} not found in database")
                skipped += 1
                continue

            student_id = res[0]

            # GET CO VALUES
            values = [
                float(row[c]) if pd.notna(row[c]) else 0
                for c in co_cols[:5]
            ]

            # INSERT OR UPDATE
            cursor.execute(f"""
                INSERT INTO {component} (
                    student_id, subject_id,
                    co1, co2, co3, co4, co5
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    co1=VALUES(co1), co2=VALUES(co2), co3=VALUES(co3),
                    co4=VALUES(co4), co5=VALUES(co5)
            """, (student_id, subject_id, *values))

            count += 1

        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
            skipped += 1

    conn.commit()

    # ---- UPDATE UPLOAD STATUS ----
    from datetime import datetime
    cursor.execute("""
        INSERT INTO upload_status (subject_id, component, uploaded_at, combined)
        VALUES (%s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE uploaded_at=%s, combined=0
    """, (subject_id, component, datetime.now(), datetime.now()))

    conn.commit()
    conn.close()

    return {"success": True, "count": count, "errors": errors, "skipped": skipped}
