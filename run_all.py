import upload_students
import upload_midsem
import upload_quiz
import upload_assignment
import upload_attendance
import combine_co

upload_students.upload_students()
upload_midsem.upload_midsem()
upload_quiz.upload_quiz()
upload_assignment.upload_assignment()
upload_attendance.upload_attendance()
combine_co.combine()

print("✅ FULL PIPELINE COMPLETED")