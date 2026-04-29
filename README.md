# SPARS (Student Performance Analysis and Reporting System)

SPARS is a comprehensive academic management web application built to track, analyze, and visualize student performance. It allows educational institutions to manage student marks, map Course Outcomes (CO) attainments, and generate detailed analytical reports across different batches and subjects. The system features a role-based access control mechanism, providing distinct views and functionalities for Administrators and Faculty members.

## 🚀 Key Features and Modules

### 👑 Administrator Module
The Admin role provides a high-level overview and system management capabilities:
- **Global Overview Dashboard:** Visualize key statistics such as the total number of enrolled students, active subjects, and overall academic averages. View top-performing and bottom-performing students institution-wide.
- **Batch-Wise Analysis:** Compare the performance of different academic batches (e.g., Class of 2027 vs. Class of 2028). Visualizations include interactive stacked bar charts showing average performance by components (Midsem, Quiz, Assignment, Attendance) and attainment distributions.
- **Subject-Wise Deep Dive:** Analyze specific subjects to identify weaknesses. Features a Population Pyramid for Course Outcome (CO) distributions, showing which COs are the weakest.
- **Faculty Management (CRUD):** Directly add, update, and manage teacher profiles. Create new subjects on the fly and securely assign them to faculty members.
- **Student Search & Detailed View:** Search for any student across the institution to view their complete academic footprint, including dynamic graphs showing their performance against class averages.

### 👨‍🏫 Faculty Module
The Faculty role is scoped down strictly to the assigned subject to maintain data privacy:
- **Subject-Specific Dashboard:** An isolated view displaying only the students enrolled in the faculty's assigned subject.
- **Marks Entry System:** An intuitive and robust interface for continuous assessment entry. Supported components:
  - **Mid Semester Examination** (Max: 20 marks)
  - **Quizzes** (Max: 5 marks)
  - **Assignments** (Max: 10 marks)
  - **Attendance** (Max: 5 marks)
- **Automatic Calculations:** The system automatically aggregates the 40 marks total, calculates the percentage out of 100%, and determines the overall **Attainment Level** (High ≥ 70%, Medium 40-69%, Low < 40%).
- **Subject Performance Insights:** Faculty can view the distribution of marks across their class, identifying underperforming students who need additional assistance.

### 📊 Course Outcome (CO) Mapping & Analytics
SPARS integrates an automated mapping system to align raw marks to specific Course Outcomes (CO1 through CO5):
- **Weighted Distributions:** Instead of a flat division, SPARS uses a predefined weighted matrix to distribute marks realistically:
  - *Midsem:* Heavily weighted towards CO1 (60%) and CO2 (40%).
  - *Quiz:* Focused on CO1 (30%), CO3 (70%), and CO5 (20%).
  - *Assignments:* Evaluates CO2 (25%), CO4 (75%), and CO5 (25%).
  - *Attendance:* Relates to consistency, mapped to CO3 (50%) and CO5 (50%).
- **Data Visualizations:** All metrics are rendered using **Matplotlib** on the backend. The generated charts are encoded into Base64 strings, ensuring lightning-fast load times without relying on heavy frontend charting libraries. Dual-chart systems (like Marimekko or Population Pyramids) provide granular details.

## 🛠️ Tech Stack & Architecture

- **Backend Framework:** Python 3.x, Flask (Jinja2 Templating Engine)
- **Database:** Relational schema managed via MySQL, interacting with Python via the `mysql-connector-python` library.
- **Frontend / UI:** 
  - Pure HTML5 and Vanilla CSS with zero external CSS frameworks (no Tailwind/Bootstrap) to maintain complete custom styling control.
  - Implements a modern aesthetic featuring a professional Blue/White color scheme, glassmorphism elements, micro-animations, and dynamic UI state management.
- **Data Visualization Engine:** Matplotlib (`Agg` backend for headless rendering).

## 🗄️ Database Architecture

The system utilizes a relational model consisting of the following primary tables:
1. `users`: Stores authentication credentials and role assignments (`admin`, `faculty`).
2. `students`: Demographic and academic enrollment details (Registration Number, Branch, Semester, Pass Year).
3. `subjects`: Master list of courses mapped to specific semesters and branches.
4. `marks`: The core transactional table tracking all component scores, computed totals, percentages, attainment levels, and specific CO1-CO5 mapped values. Enforces unique constraints to prevent duplicate entries per student-subject pair.
5. `upload_status` & `marks_permission`: Tracking tables for bulk data ingestion limits and status monitoring.

## ⚙️ Local Setup and Installation

Follow these steps to deploy and run the project locally:

### 1. Prerequisites
- Python 3.8+ installed on your system.
- MySQL Server installed and running locally on port 3306.

### 2. Clone the Repository
```bash
git clone <your-github-repo-url>
cd SPARS
```

### 3. Setup Virtual Environment (Highly Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
Install the required Python packages manually:
```bash
pip install Flask mysql-connector-python matplotlib pandas openpyxl
```
*(Note: `pandas` and `openpyxl` are required if you intend to use the bulk Excel upload scripts).*

### 5. Database Configuration
1. Open your MySQL client (CLI or Workbench).
2. Create the target database:
   ```sql
   CREATE DATABASE SPARS;
   ```
3. Open `db.py` in the project root and update the connection credentials to match your environment:
   ```python
   def get_connection():
       return mysql.connector.connect(
           host="localhost",
           user="your_mysql_username",      # e.g., 'root'
           password="your_mysql_password",  # Your local MySQL password
           database="SPARS"
       )
   ```

### 6. Initialize the Database Schema
Run the database initialization script. This will create all necessary tables and seed the initial users:
```bash
python init_db.py
```
**Default Seeded Accounts:**
- **Admin:** Username: `admin` | Password: `admin123`
- **Faculty:** Username: `faculty` | Password: `faculty123`

### 7. Optional: Bulk Import Data
If you possess the initial raw data in Excel formats (e.g., `PPD_LAB.xlsx`), you can utilize the provided parser scripts to batch-import students and marks:
```bash
python upload_students.py
python auto_combine.py
```

### 8. Run the Application
Boot up the Flask development server:
```bash
python app.py
```
Open your web browser and navigate to `http://127.0.0.1:5000` to access the login page.

## 📁 Project Structure

```text
SPARS/
├── app.py                   # Main Flask application and routing logic
├── db.py                    # MySQL connection handler
├── init_db.py               # Database schema initialization script
├── static/                  # Static assets
│   └── css/                 # Vanilla CSS files (admin.css, common.css)
├── templates/               # Jinja2 HTML templates
│   ├── login.html           # Authentication portal
│   ├── admin_dashboard.html # Global admin overview
│   ├── faculty_dashboard.html # Subject-scoped dashboard
│   ├── subject_analysis.html# Granular CO/marks analysis
│   └── ...                  # Additional views
├── scripts/ (Python Parsers)# Scripts for backend data processing
│   ├── upload_students.py   # Ingest student demographic data
│   ├── parser.py            # Extracts data from Excel sheets
│   └── fix_co_distribution.py # Corrects algorithmic mappings
└── PPD_LAB.xlsx             # Sample/Template data source
```



