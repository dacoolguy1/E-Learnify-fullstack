#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_url_path='/static')

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Eronville2023!'
app.config['MYSQL_DB'] = 'course_enrollment'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Set a secret key for session management
app.secret_key = 'sss'

@app.route('/coursehome', methods=['GET', 'POST'])
def coursehome():
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT email FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

        cursor1 = mysql.connection.cursor()
        cursor1.execute('SELECT c.id, c.image, c.title, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))
        courses = cursor1.fetchall()

        for course in courses:
            course['is_enrolled'] = True if course['enrollment_id'] else False

        return render_template('coursehome.html', courses=courses, user=user)
    else:
        return redirect('/login')
    

    # return render_template('')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, hashed_password))
        mysql.connection.commit()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/coursehome')
        else:
            return 'Invalid email or password'

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT email FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

        cursor1 = mysql.connection.cursor()
        cursor1.execute('SELECT c.id, c.title, c.image, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))
        courses = cursor1.fetchall()

        for course in courses:
            course['is_enrolled'] = True if course['enrollment_id'] else False

        return render_template('course_list.html', courses=courses, user=user)
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    session.clear() #here we clear the user session
    return redirect('/')

@app.route('/about')
def aboutpage():
    return render_template('aboutpage.html')
    

@app.route('/')
def home_page():
    cursor1 = mysql.connection.cursor()
    cursor1.execute('SELECT * FROM courses')
    courses = cursor1.fetchall()

    return render_template('index.html', courses=courses)

# @app.route('/course_list')
# def course_list():
#     if 'user_id' in session:
#         user_id = session['user_id']

#         cursor = mysql.connection.cursor()
#         cursor.execute('SELECT c.id, c.title, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))

#         courses = cursor.fetchall()

#         return render_template('course_list.html', courses=courses)
#     else:
#         return redirect('/login')

# ...

@app.route('/mark_module_done', methods=['POST'])
def mark_module_done():
    if 'user_id' in session:
        user_id = session['user_id']
        module_id = request.form['module_id']
        course_id = request.form['course_id']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM modules WHERE id = %s', (module_id,))
        module = cursor.fetchone()

        if module:
            # Check if the user has already marked the module as completed
            cursor.execute('SELECT id FROM progress WHERE user_id = %s AND module_id = %s', (user_id, module_id))
            progress = cursor.fetchone()

            if progress:
                return 'Module already marked as completed'
            else:
                # Insert module completion into the progress table
                cursor.execute("INSERT INTO progress (user_id, module_id, course_id, progress_percent,  completed) VALUES (%s, %s, %s, %s, %s)",
                               (user_id, module_id, course_id, 100, 1))
                mysql.connection.commit()
                cursor.close()

                return 'Module marked as completed'
        else:
            return 'Invalid module ID'
    else:
        return redirect('/login')


@app.route('/coursepage/<int:course_id>')
def coursepage(course_id):
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT email FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

        cursor.execute('SELECT * FROM modules WHERE course_id = %s', (course_id,))
        modules = cursor.fetchall()

        cursor.execute('SELECT c.id, c.title, c.image, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s WHERE c.id = %s', (user_id, course_id,))
        course = cursor.fetchone()

        if course:
            if course['enrollment_id']:  # Check if the user is enrolled in the course
                course['is_enrolled'] = True
                print(user_id)

                # Fetch the progress data for the user from the database
                cursor.execute('SELECT Progress_percent FROM progress WHERE User_id = %s AND course_id = %s', (user_id, course_id,))
                progress = cursor.fetchone()
                if progress:
                    course['progress_percent'] = progress['Progress_percent']
                else:
                    course['progress_percent'] = 0

                return render_template('maincourse.html', user=user, course=course, modules=modules)
            else:
                return 'You are not enrolled in this course'
        else:
            return "Course not found"
    else:
        return 'You are not logged in'


# ...


# @app.route('/coursepage/<int:course_id>')
# def coursepage(course_id):
#    if 'user_id' in session:
#         user_id = session['user_id']

#         cursor = mysql.connection.cursor()
#         cursor.execute('SELECT email FROM users WHERE id = %s', (session['user_id'],))
#         user = cursor.fetchone()

#         cursor1 = mysql.connection.cursor()
#         cursor1.execute('SELECT c.id, c.title, c.image, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))
#         courses = cursor1.fetchall()
#         # course = courses[course_id - 1]  # Subtract 1 to get the correct index
#         course_index = course_id - 1
#         if course_index < len(courses):
#             course = courses[course_index]
#             for course in courses:
#                 course['is_enrolled'] = True if course['enrollment_id'] else False

        

#         return render_template('maincourse.html', courses=courses, user=user)
#    else:
#        return 'You are not enrolled'


@app.route('/course/<int:course_id>')
def course_details(course_id):
    cursor1 = mysql.connection.cursor()
    cursor1.execute('SELECT * FROM courses')
    courses = cursor1.fetchall()

    course = courses[course_id - 1]  # Subtract 1 to get the correct index
    return render_template('course_details.html', course=course)
@app.route('/course_list')
def course_list():
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT c.id, c.title, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))

        courses = cursor.fetchall()

        for course in courses:
            course['is_enrolled'] = True if course['enrollment_id'] else False

        return render_template('course_list.html', courses=courses)
    else:
        return redirect('/login')


@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    if 'user_id' in session:
        user_id = session['user_id']

        # Check if the course_id exists in the courses table
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id FROM courses WHERE id = %s', (course_id,))
        course = cursor.fetchone()

        if course:
            # Check if the user is already enrolled in the course
            cursor.execute('SELECT id FROM enrollments WHERE user_id = %s AND course_id = %s', (user_id, course_id))
            enrollment = cursor.fetchone()

            if enrollment:
                return 'You are already enrolled in this course'
            else:
                # Insert enrollment into the enrollments table
                cursor.execute("INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s)", (user_id, course_id))
                mysql.connection.commit()
                cursor.close()

                # Re-fetch the courses after enrolling
                cursor = mysql.connection.cursor()
                cursor.execute('SELECT c.id, c.title, c.image, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))
                courses = cursor.fetchall()

                for course in courses:
                    course['is_enrolled'] = True if course['enrollment_id'] else False

                return render_template('course_list.html', courses=courses)
        else:
            return 'Invalid course ID'
    else:
        return redirect('/login')


@app.route('/unenroll/<int:enrollment_id>', methods=['POST'])
def unenroll(enrollment_id):
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id FROM enrollments WHERE id = %s AND user_id = %s', (enrollment_id, user_id))
        enrollment = cursor.fetchone()

        if enrollment:
            cursor.execute('DELETE FROM enrollments WHERE id = %s AND user_id = %s', (enrollment_id, user_id))
            mysql.connection.commit()
            cursor.close()

            # Re-fetch the courses after unenrolling
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT c.id, c.title, c.image, c.description, c.instructor, c.duration, e.id AS enrollment_id FROM courses AS c LEFT JOIN enrollments AS e ON c.id = e.course_id AND e.user_id = %s', (user_id,))
            courses = cursor.fetchall()

            for course in courses:
                course['is_enrolled'] = True if course['enrollment_id'] else False

            return render_template('course_list.html', courses=courses)
        else:
            return 'Invalid enrollment ID'
    else:
        return redirect('/login')



@app.route('/insert_courses')
def insert_courses():
    # Define the list of courses
    new_courses = [
        {
            'title': 'UI/UX Case Study',
            'description': 'Learn the meaning of Case Study, uses and function .',
            'instructor': ' Grace David',
            'duration': '7 weeks',
            'image': '../static/images/v99_194.png'
        },
        {
            'title': 'JavaScript For Beginners',
            'description': 'Learn the meaning of Js, uses and function',
            'instructor': 'John Smith',
            'duration': '3 weeks',
            'image': '../static/images/v99_203.png'
        },
        {
            'title': 'Data science',
            'description': 'Learn the how art of extracting knowledge and gaining insights from data',
            'instructor': ' John Doe',
            'duration': '6 weeks',
            'image': '../static/images/v99_221.png'
        },
        # Add more courses...
    ]

    # Insert the courses into the database
    cursor = mysql.connection.cursor()
    for course in new_courses:
        title = course['title']
        description = course['description']
        instructor = course['instructor']
        duration = course['duration'][:2]  # Truncate to the first 10 characters to avoid errors
        image = course['image']
        cursor.execute('INSERT INTO courses (title, description, instructor, duration, image) VALUES (%s, %s, %s, %s, %s)', (title, description, instructor, duration, image))
        mysql.connection.commit()

    return 'Courses inserted successfully'
@app.route('/insert_modules')
def insert_modules():
    try:
        cursor = mysql.connection.cursor()
        
        # Insert module details using executemany()
        modules = [
            (1, 40, 'Module 1: Introduction to HTML', 'In this module, you will learn the basics of HTML, including tags, elements, and structure.', 'https://www.w3schools.com/html/'),
            (2, 40, 'Module 2: HTML Elements and Attributes', ' Explore different HTML elements and attributes and how to use them in your web pages.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element'),
            (3, 40, 'Module 3: HTML Forms', ' Learn how to create forms in HTML for user input, such as text fields, checkboxes, and dropdowns.', 'https://www.learn-html.org/en/Form_Elements'),
            (4, 40, 'Module 4: HTML Semantic Elements', ' Discover the importance of semantic HTML elements and how they contribute to website accessibility and SEO.', 'https://developer.mozilla.org/en-US/docs/Glossary/Semantics#Semantics_in_HTML'),
            (5, 41, 'Module 1: Introduction to SQL', 'This module provides an introduction to SQL and its importance in database management systems', 'https://www.w3schools.com/sql/'),
            (6, 41, 'Module 2: Retrieving Data with SQL', ' Learn how to retrieve data from a database using SQL queries.', 'https://www.geeksforgeeks.org/sql-select-statement/'),
            (7, 41, 'Module 3: Modifying Data with SQL', ' Explore SQL statements for inserting, updating, and deleting data in a database.', 'https://www.tutorialspoint.com/sql/sql-insert-query.htm'),
            (8, 41, 'Module 4: SQL Joins and Relationships', ' Understand SQL joins and how to establish relationships between tables in a database.', 'https://mode.com/sql-tutorial/sql-joins/'),
            (9, 42, 'Module 1: HTML Fundamentals', 'Learn the basics of HTML, including tags, elements, and structure of a web page.', 'https://developer.mozilla.org/en-US/docs/Learn/HTML'),
            (10, 42, 'Module 2: CSS Styling', ' Explore CSS and learn how to style web pages, including selectors, properties, and layout techniques.', 'https://www.w3schools.com/css/'),
            (11, 42, 'Module 3: JavaScript Basics', '  Introduction to JavaScript programming language, covering variables, functions, conditionals, and DOM manipulation.', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide'),
            (12, 42, 'Module 4: Responsive Web Design', ' Understand the principles of responsive web design and learn how to create websites that adapt to different screen sizes.', 'https://developers.google.com/web/fundamentals/design-and-ux/responsive'),
            (13, 43, 'Module 1: Introduction to UI/UX Design', 'Get an overview of UI (User Interface) and UX (User Experience) design principles, processes, and tools.', 'https://www.interaction-design.org/courses/ux-design-fundamentals'),
            (14, 43, 'Module 2: User Research and Persona Development', 'Learn about user research techniques, such as interviews and surveys, and how to create user personas.', 'https://www.nngroup.com/articles/user-research-methods/'),
            (15, 43, 'Module 3: Wireframing and Prototyping', ' Explore the process of creating wireframes and prototypes to visualize and test user interfaces.', 'https://helpx.adobe.com/xd/how-to/wireframe-prototype-app.html'),
            (16, 43, 'Module 4: Usability Testing and Iteration', ' Learn how to conduct usability testing sessions and use feedback to iterate and improve designs.', 'https://www.usability.gov/how-to-and-tools/methods/usability-testing.html'),
            (17, 44, 'Module 1: Introduction to JavaScript', 'Learn the basics of JavaScript, including variables, data types, operators, and control flow.', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide'),
            (18, 44, 'Module 2: DOM Manipulation', '  Explore how to interact with the Document Object Model (DOM) using JavaScript to modify HTML elements and handle events.', 'https://javascript.info/modifying-document'),
            (19, 44, 'Module 3: Functions and Scope', '  Dive into functions, function declarations, function expressions, and variable scope in JavaScript', 'https://www.w3schools.com/js/js_functions.asp'),
            (20, 44, 'Module 4: Arrays and Objects', ' Learn about arrays and objects, two fundamental data structures in JavaScript, and how to manipulate and iterate over them.', 'https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/Arrays'),
            (21, 45, 'Module 1: Introduction to Data Science', 'Explore the fundamentals of data science, including data analysis, data visualization, and data manipulation techniques.', 'https://www.coursera.org/learn/introduction-to-data-science'),
            (22, 45, 'Module 2: Machine Learning Algorithms', ' Learn about various machine learning algorithms, such as linear regression, logistic regression, decision trees, and random forests.', 'https://towardsdatascience.com/machine-learning-algorithms-for-beginners-with-python-code-examples-ml-19c6afd60daa'),
            (23, 45, 'Module 3: Data Cleaning and Preprocessing', '  Dive into techniques for cleaning and preprocessing data, including handling missing values, outlier detection, and feature scaling.', 'https://www.datacamp.com/courses/cleaning-data-in-python'),
            (24, 45, 'Module 4: Data Visualization and Exploratory Data Analysis', '  Explore data visualization techniques using libraries such as Matplotlib and Seaborn, and learn how to perform exploratory data analysis.', 'https://www.kaggle.com/learn/data-visualization')
            # Add more module details here
        ]
        modules_tuples = map(tuple, modules)
        query = "INSERT INTO modules (id, course_id, title, description, link) VALUES (%s, %s, %s, %s,%s)"
        cursor.executemany(query,  modules_tuples)
        mysql.connection.commit()
        cursor.close()
        
        return 'Modules inserted successfully'
    except Exception as e:
        return f'Error inserting modules: {str(e)}'


if __name__ == '__main__':
    app.run()
