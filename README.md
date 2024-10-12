# School LMS (Learning Management System)

## Overview

This School LMS application is an MSc Computer Science project on the Secure Software Development module at the University of Essex Online. The project is not intended to be a production-level application, and serves only to fulfil the requirements of an academic assignment. 

The application is ultimately designed to provide for the management and viewing of timetables, lessons and user accounts within a school environment. It offers role-based access control, allowing administrators, teachers, and students to interact with the system according to their specific needs and permissions. 

The application is pricipally developed in the Python programming language and leverages built-in libraries and python packages. It employs a responsive web interface and client-server architecture for secure data handling.

## Key Features
The application allows users to create accounts with usernames and passwords, assigning specific role-based permissions to administrators, parents, or students. Administrators retain the highest access privileges.

### User Authentication and Authorisation
- Secure JWT (JSON Web Token) based authentication system
- Role-based access control (Admin, Teacher, Student)
- Password hashing for enhanced security
- Session management with token expiration

### Lesson Management
- Create, Read, Update, and Delete (CRUD) operations for lessons
- Automatic conflict detection when scheduling lessons
- Bulk lesson creation on launch
- Lesson editing capabilities

### Timetable System
- Dynamic timetable generation based on scheduled lessons
- Personalised timetable views for students and teachers
- Weekly and monthly timetable views

### Student-Specific Features
- Personal timetable view


## Technical Architecture

### Backend
- **Framework**: FastAPI - chosen for its high performance and easy-to-use API creation and async capabilities
- **Language**: Python 3.9+
- **Authentication**: JWT (JSON Web Tokens) for secure, stateless authentication
- **Data Storage**: In-memory storage for demonstration using only Python data structures as per the requirements of the project (It is recommended to use a relational database management system such as SQL for production)

### Frontend
- **Templating Engine**: Jinja2 for server-side rendering of HTML 
- **Styling**: Custom CSS using responsive design principles
- **JavaScript**: Vanilla JS for interactive elements and authentication

### API Design
- RESTful API architecture
- Swagger UI integration for interactive API documentation

## Prerequisites

- A modern IDE like VS Code
- A modern browser
- pip (Python package installer)
- Python 3.9 or higher

To check if you have Python installed or to confirm your Python version, run:
```
python --version
```

If Python installation is required, please visit the [official Python website](https://www.python.org/downloads/) and follow the installation guidelines for your operating system, as directed.

## Project Setup

1. Clone the repository:
```
git clone https://github.com/craigbourne/school_lms.git
cd school_lms
```

2. Create a virtual environment:
```
python -m venv venv
```

3. Activate the virtual environment:

On Windows:
```
venv\Scripts\activate
```
On macOS and Linux:
```
source venv/bin/activate
```

4. Install the required project dependencies:
```
pip install -r requirements.txt
```

## Running the Application

To start the server, run:
```
python src/main.py
```

The application will be available in your browser at `http://localhost:8000`.

## Using the Application

### Logging In

You can log in using one of the test accounts created in advance. There are accounts for either an administrator, a teacher or a student. The log in details are as follows:

- Admin: username `admin`, password `adminpass`
- Teacher: username `teacher1`, password `teacherpass`
- Student: username `student1`, password `studentpass`

Alternatively, you can register your own account by clicking the "Sign Up" link on the login page. This will redirect you to a registration page and you will be required to enter a username, a password, and email address and then select the the user role for the account. You can then log in with the username and password.

### Auto-generated Data

Upon launch, the application will automatically generate:
- Test user accounts
- Mock teachers and students
- Random lesson generation for each teacher
- Automatically populated timetables

This allows for the immediate exploration of the application's capabilities, without the arduous task of manual data entry.

### Dashboard

After logging in, you'll be directed to the main dashboard, which serves as a central hub for navigation and access to the application's features. The dashboard content is dynamically generated based on the user's role. The content in the dashboard includes some or all of the following, depending on who is logged in:

### Timetable View

The timetable view provides a visual representation of the weekly schedule:

- **Students**: See their class timetable with subjects, times, and classroom locations
- **Teachers**: View their teaching schedule, including class details and student groups
- **Admins**: Access to all timetables for all users. 

### Lesson List

The lesson list offers a comprehensive view of lessons, tailored to each user role:

- **Students**: View lessons for their year group, including details like subject, teacher, and classroom
- **Teachers**: See lessons they're teaching, with options to edit lesson details or add resources
- **Administrators**: Can view all lessons for all users

### Managing Lessons

Administrators and teachers have access to CRUD lesson management tools:

- **Add New Lessons**: Create new lessons with details such as subject, time, duration, year group and assigned class
- **Edit Lessons**: Modify existing lesson details or change schedules
- **Delete Lessons**: Remove lessons from the system (limited to admin only)

The lesson management interface includes conflict detection to prevent double-booking of teachers or classrooms.

## Security Measures

- **Password Hashing**: All user passwords are securely hashed before storage using bcrypt.
- **Input Validation**: Basic input validation is implemented using Pydantic models to ensure data types match expected formats.
- **JWT Authentication**: JSON Web Tokens are used for maintaining user sessions securely.

Note: While the current implementation includes these basic security measures, a production-ready application would require additional security features such as CSRF protection, perhaps using a package like [fastapi-csrf-protect](https://pypi.org/project/fastapi-csrf-protect/), rate limiting possibly with a package like [slowapi](https://pypi.org/project/slowapi/), and more comprehensive input validation and sanitisation.

## Code Quality and Testing

### Running Pylint

To check code quality using Pylint (configured to follow PEP-8 standards):
```
pylint src
```

To check an individial file:
```
pylint src/{file_name}.py

# For example:
pylint src/name.py
```

### Running Tests

To run the test suite using pytest:
```
pytest
```
To run individual tests on parts of the application, you can test any function within the testing file by using:
```
pytest tests/test_main.py::{test function name here} -v

#For example:
pytest tests/test_main.py::test_user_login_success -v
```

## Future Enhancements

While the current version of the School LMS serves as a prototype, potential enhancements could be implemented to improve functionality, security, and user experience:

### Security Enhancements
1. **Rate Limiting**: Add API rate limiting to prevent abuse and enhance system stability by limiting the number of requests a user can make in a given timeframe.

2. **Two-Factor Authentication (2FA)**: Introduce an additional layer of security by implementing 2FA, requiring users to provide two different authentication factors to verify themselves.

3. **Enhanced Input Validation**: Implement more stringent input validation and sanitisation to further protect against injection attacks and ensure data integrity.

4. **CSRF Protection**: Implement Cross-Site Request Forgery protection to prevent unauthorised commands from being transmitted from a user that the web application trusts.

### Feature Enhancements
1. **Student Grading System**: Implement a grading feature allowing teachers to input or amend grades for assignments and exams, and students to view their academic progress.

2. **Continuous Integration/Continuous Deployment (CI/CD) Pipeline**: Integrate a CI/CD pipeline using Jenkins to automate the testing process, ensuring code quality and streamlining the development workflow.

3. **Advanced Admin Timetable Management**:
Implement filtering options for the admin timetable view by teacher, class, or student.

4. **Enhanced User Dashboards**:
- For Teachers: Display upcoming lessons and provide quick access to student lists.
- For Students: Show today's timetable, upcoming homework or assignments, and recent grades.

5. **Interactive Timetable**: Develop an interactive timetable interface allowing users to click on and expand individual lessons for more details, providing a more engaging and informative user experience.

6. **Advanced Lesson Management**:
- Implement advanced filtering and sorting options in the lesson list view.
- Introduce bulk operations functionality, allowing administrators or teachers to perform actions on multiple lessons simultaneously. For example, if a teacher was absent from school due to illness or other circumstances, an entire week's worth of lessons could be rescheduled or reassigned to a different teacher or teachers with a single operation, significantly improving efficiency in timetable management.

7. **Integration with External Calendar Systems**: Allow synchronisation with popular calendar applications (e.g., Google Calendar, Outlook) to help users manage their schedules more effectively.

8. **Notification System**: Develop a notification system to alert users about timetable changes, upcoming deadlines, or important announcements.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License.

## Acknowledgments

- FastAPI framework and its contributors
- All open-source libraries used in this project
- Tim Brayshaw, Ioannis Maragkos and Lauren Pechey for contributing to the design document, on which this application is based