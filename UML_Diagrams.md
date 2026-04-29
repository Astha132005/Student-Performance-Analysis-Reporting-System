# SPARS – UML Diagrams (Experiments 3 to 6) + Gantt Chart
# Student Performance Analysis and Reporting System

---

## EXPERIMENT 3(i) — Use Case Diagram

```mermaid
graph TB
    Faculty((Faculty))
    Admin((Admin))

    subgraph SPARS - Student Performance Analysis and Reporting System
        UC1([Login])
        UC2([Upload Marks])
        UC3([Upload Attendance])
        UC4([View Subject Analysis])
        UC5([View Batch Analysis])
        UC6([Search Student])
        UC7([Set Permission Window])
        UC8([Edit Marks Inline])
        UC9([Manage Subjects])
        UC10([View Dashboard])
        UC11([Auto Combine CO Scores])
        UC12([Logout])
    end

    Faculty --> UC1
    Faculty --> UC2
    Faculty --> UC3
    Faculty --> UC4
    Faculty --> UC5
    Faculty --> UC6
    Faculty --> UC10
    Faculty --> UC12

    Admin --> UC1
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC10
    Admin --> UC12

    UC2 -->|include| UC11
    UC3 -->|include| UC11
    UC7 -.->|controls| UC2
    UC7 -.->|controls| UC3
```

---

## EXPERIMENT 3(ii) — Activity Diagram (Upload Marks Flow)

```mermaid
flowchart TD
    A([Start]) --> B[Faculty Logs In]
    B --> C{Window Active?}
    C -- No --> D([Access Denied])
    C -- Yes --> E[Select Subject and Component]
    E --> F[Upload Excel File]
    F --> G{File Valid?}
    G -- No --> H([Show Error])
    G -- Yes --> I[Insert Marks into Database]
    I --> J{All 4 Components Done?}
    J -- No --> K([End])
    J -- Yes --> L[Auto Combine and Calculate CO Scores]
    L --> M([Marks Ready])
```

---

## EXPERIMENT 4(i) — Class Diagram

```mermaid
classDiagram
    class System_Interface {
        + login(username, password) : boolean
        + reportReady() : void
        + displaySuccessMessage() : void
    }

    class User {
        - username : String
        - password : String
        - role : String
        + login(username, password) : boolean
        + verifyAccess() : boolean
        + logout() : void
    }

    class Admin {
        - adminId : int
        + setPermissionWindow(start, end) : void
        + editMarks(marks_id, field, value) : void
        + manageSubjects() : void
    }

    class Faculty {
        - facultyId : int
        + uploadMarks(file, component, subject) : void
        + viewSubjectAnalysis(branch, semester) : void
        + viewBatchAnalysis(branch, semester, year) : void
    }

    class Student {
        - student_id : int
        - reg_no : String
        - name : String
        - branch : String
        - semester : int
        - pass_year : int
        + getMarks() : Marks
    }

    class Subject {
        - subject_id : int
        - subject_name : String
        - branch : String
        - semester : int
        + getStudents() : List
    }

    class Marks {
        - id : int
        - midsem_total : float
        - quiz_total : float
        - assignment_total : float
        - attendance_total : float
        - total : float
        - percentage : float
        - attainment : String
        - co1 : float
        - co2 : float
        - co3 : float
        - co4 : float
        - co5 : float
        + calculatePercentage() : float
        + calculateAttainment() : String
    }

    class MarksPermission {
        - id : int
        - start_time : DateTime
        - end_time : DateTime
        - is_active : boolean
        + isWindowOpen() : boolean
        + deactivate() : void
    }

    System_Interface "1" --> "0..*" User
    User <|-- Admin
    User <|-- Faculty

    Student "1" --> "many" Marks : has
    Subject "1" --> "many" Marks : covers
    MarksPermission "1" --> Faculty : controls
    Faculty --> Marks : uploads
    Admin --> Marks : edits
```

---

## EXPERIMENT 4(ii) — Sequence Diagram (Faculty Uploads Marks)

```mermaid
sequenceDiagram
    actor Faculty
    participant Browser
    participant FlaskApp
    participant UploadHandler
    participant Database

    Faculty->>Browser: Open /marks_entry
    Browser->>FlaskApp: GET /marks_entry
    FlaskApp->>Database: Query marks_permission
    Database-->>FlaskApp: Return permission record
    FlaskApp-->>Browser: Render page with subjects list

    Faculty->>Browser: Select Subject, Component, Upload File
    Browser->>FlaskApp: POST /faculty_upload

    FlaskApp->>Database: Check is_active and time window
    Database-->>FlaskApp: Window is active

    FlaskApp->>UploadHandler: upload_component(file, component, subject)
    UploadHandler->>Database: INSERT into midsem / quiz / assignment / attendance
    UploadHandler->>Database: UPDATE upload_status table
    UploadHandler-->>FlaskApp: count inserted, errors list

    FlaskApp->>Database: COUNT upload_status WHERE combined=0
    Database-->>FlaskApp: 4 components done

    FlaskApp->>FlaskApp: Call auto_combine(subject_name)
    FlaskApp->>Database: Compute CO scores, percentage, attainment
    FlaskApp->>Database: INSERT into marks table

    FlaskApp-->>Browser: Flash success message
    Browser-->>Faculty: Marks uploaded and combined
```

---

## EXPERIMENT 5 — State Chart Diagram (Marks Permission Lifecycle)

```mermaid
stateDiagram-v2
    [*] --> Inactive : System Initialized

    Inactive --> Scheduled : Admin Sets\nStart and End Time\n(is_active = 1)

    Scheduled --> Live : Current Time\nreaches start_time

    Live --> Live : Faculty Uploads\nExcel File\n(upload_status updated)

    Live --> AllUploaded : All 4 Components\nUploaded for a Subject

    AllUploaded --> Merged : auto_combine runs\nCO Scores Calculated

    Merged --> Live : More Subjects\nRemaining

    Live --> Expired : Current Time\nexceeds end_time\n(is_active = 0)

    Live --> Inactive : Admin Deactivates\nManually

    Expired --> Inactive : State Reset

    Inactive --> Scheduled : Admin Sets\nNew Window
```

---

## EXPERIMENT 6 — Package Diagram (Layered Architecture)

```mermaid
graph TD
    subgraph UI["UI Layer — HTML Templates"]
        T1[login.html]
        T2[admin_dashboard.html]
        T3[faculty_dashboard.html]
        T4[marks_entry.html]
        T5[subject_analysis.html]
        T6[batch_analysis.html]
        T7[student.html]
    end

    subgraph App["Application Layer — Flask Routes (app.py)"]
        R1[/login]
        R2[/admin_dashboard]
        R3[/faculty_dashboard]
        R4[/marks_entry POST/GET]
        R5[/faculty_upload]
        R6[/subject_analysis]
        R7[/batch_analysis]
        R8[/student]
        R9[/api/update]
        R10[/logout]
    end

    subgraph Service["Service Layer — Business Logic"]
        S1[upload_handler.py\nParse Excel and Insert Rows]
        S2[auto_combine.py\nTrigger CO Calculation]
        S3[combine_co.py\nCalculate CO Scores]
        S4[parser.py\nExcel Parsing Utility]
    end

    subgraph Data["Data Layer — MySQL Database"]
        D1[(users)]
        D2[(students)]
        D3[(subjects)]
        D4[(marks)]
        D5[(midsem)]
        D6[(quiz)]
        D7[(assignment)]
        D8[(attendance)]
        D9[(marks_permission)]
        D10[(upload_status)]
    end

    UI --> App
    App --> Service
    Service --> Data
    App --> Data
```

---

## GANTT CHART — SPARS Project Plan (All 10 Experiments)

```mermaid
gantt
    title SPARS – Project Plan 2026
    dateFormat YYYY-MM-DD
    axisFormat %d %b

    section Experiment 1
    Problem Statement                        :done, e1, 2026-01-05, 2026-01-11

    section Experiment 2
    SRS Document and Gantt Chart             :done, e2, 2026-01-12, 2026-01-25

    section Experiment 3
    Use Case Model and Activity Diagram      :done, e3, 2026-01-26, 2026-02-08

    section Experiment 4
    Class Diagram and Interaction Diagrams   :done, e4, 2026-02-09, 2026-02-22

    section Experiment 5
    State Chart Diagram                      :active, e5, 2026-02-23, 2026-03-02

    section Experiment 6
    Package Diagram                          :e6, 2026-03-03, 2026-03-15

    section Experiment 7
    Technical Services and Domain Layer      :e7, 2026-03-16, 2026-03-29

    section Experiment 8
    User Interface Layer Implementation      :e8, 2026-03-30, 2026-04-06

    section Experiment 9
    Component and Deployment Diagrams        :e9, 2026-04-07, 2026-04-14

    section Experiment 10
    Testing, Documentation and Presentation  :e10, 2026-04-15, 2026-04-22
```
