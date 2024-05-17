from flask import Flask,url_for,session,redirect,render_template,request,flash,send_file,send_from_directory
from flask_session import Session 
from flask_mysqldb import MySQL
from key import *
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import *
import os
from otp import genotp
from flask import abort
from datetime import datetime
from datetime import datetime, timedelta
import stripe


app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
stripe.api_key = 'sk_test_51MzcVYSDVehZUuDTkwGUYe8hWu2LGN0krI8iO5QOAEqoRYXx3jgRVgkY7WzXqQmpN62oMWM59ii76NKPrRzg3Gtr005oVpiW82'

app.secret_key = '23efgbnjuytr'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'mindmend'
mysql = MySQL(app)

@app.route('/')
def home():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM therapists')
    therapists_data = cursor.fetchall()
    cursor.close()

    return render_template('home.html',therapists=therapists_data)

@app.route('/user_registration', methods=['GET', 'POST'])
def user_registration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('select count(*) from users where email=%s', [email])
        count1 = cursor.fetchone()
        print(count1)
        cursor.close()
        if count1==1:
            flash('Email already in use')
            return render_template('userregistration.html')

        data = {'username': username, 'email': email, 'password': password}
        subject = 'Email Confirmation'
        body = f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm', token=token(data, salt), _external=True)}"
        sendmail(to=email, subject=subject, body=body)
        flash('Confirmation link sent to email')
        return redirect(url_for('user_login'))
    return render_template('userregistration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        # Verify the token
        serializer = URLSafeTimedSerializer(secret_key)
        data = serializer.loads(token, salt=salt, max_age=180)
    except Exception as e:
        abort (404,'Link Expired register again')
    else:
        cursor = mysql.connection.cursor()
        email=data['email']

        # Check if the user is already registered
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = %s', [email])
        count = cursor.fetchone()

        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', [data['username'], data['email'], data['password']])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('user_login'))


@app.route('/user_login',methods=['GET','POST'])
def user_login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT count(*) as h from users where email=%s and password=%s',[email,password])
        count=cursor.fetchone()
        if count[0]==1:  # Fix here
            session['user']=email
            return redirect(url_for('user_home'))
        else:
            flash('Invalid username or password')
            return render_template('userlogin.html')

    return render_template('userlogin.html')
@app.route('/user_home')
def user_home():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM therapists')
    therapists_data = cursor.fetchall()
    print(therapists_data)
    
    cursor.execute('SELECT * FROM users')
    user_data = cursor.fetchall()
    cursor.execute('SELECT * FROM appointments')
    appointment_data = cursor.fetchall()
    print(appointment_data)
    cursor.close()

    # Render the template with therapist data
    return render_template('user_home.html', therapists=therapists_data,appointment_data=appointment_data,user_data=user_data)
@app.route('/user_profile')
def user_profile():
    if 'user' in session:
        user_email = session['user']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', [user_email])
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return render_template('user_profile.html', user=user_data)
        else:
            # User not found, handle the case accordingly
            flash('User data not found.')
            return redirect(url_for('user_login'))
    else:
        # User not logged in, redirect to login page
        return redirect(url_for('user_login'))

@app.route('/edit_profile')
def edit_profile():
    if 'user' in session:
        user_email = session['user']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', [user_email])
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return render_template('edit_profile.html', user=user_data)
        else:
            flash('User data not found.')
            return redirect(url_for('user_login'))
    else:
        return redirect(url_for('user_login'))
        
@app.route('/edit_admin_profile')
def edit_admin_profile():
    if 'user1' in session:
        user_email = session['user1']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM therapists WHERE email = %s', [user_email])
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return render_template('edit_admin_profile.html', user=user_data)
        else:
            flash('User data not found.')
            return redirect(url_for('therapist_login'))
    else:
        return redirect(url_for('therapist_login'))

@app.route('/update_admin_profile', methods=['POST'])
def update_admin_profile():
    if 'user1' in session:
        # Get the updated data from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        specialties=request.form['specialties']
        credentials=request.form['credentials']
        experience=request.form['experience']
        
        # Update the user's details in the database
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE therapists SET name = %s, email = %s, password = %s,specialties=%s,credentials=%s,experience=%s WHERE email = %s',
                       (username, email, password,specialties,credentials,experience, session['user1']))
        mysql.connection.commit()
        cursor.close()
        
        flash('Profile updated successfully.')
        return redirect(url_for('admin_profile'))
    else:
        flash('You are not logged in.')
        return redirect(url_for('therapists_login'))
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' in session:
        # Get the updated data from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Update the user's details in the database
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE users SET username = %s, email = %s, password = %s WHERE email = %s',
                       (username, email, password, session['user']))
        mysql.connection.commit()
        cursor.close()
        
        flash('Profile updated successfully.')
        return redirect(url_for('user_profile'))
    else:
        flash('You are not logged in.')
        return redirect(url_for('user_login'))

@app.route('/therapists_registration', methods=['GET', 'POST'])
def therapists_registration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        specialties=request.form['specialties']
        credentials=request.form['credentials']
        experience=request.form['experience']
        cursor = mysql.connection.cursor()
        cursor.execute('select count(*) from users where email=%s', [email])
        count1 = cursor.fetchone()
        cursor.close()
        if count1==1:
            flash('Email already in use')
            return render_template('userregistration.html')

        data = {'username': username, 'email': email, 'password': password,'specialties':specialties,'credentials':credentials,'experience':experience}
        subject = 'Email Confirmation'
        body = f"Thanks for signing up\n\nfollow this link for further steps-{url_for('adminconfirm', token=token(data, salt), _external=True)}"
        sendmail(to=email, subject=subject, body=body)
        flash('Confirmation link sent to email')
        return redirect(url_for('therapists_login'))

    return render_template('therapists_registration.html')
@app.route('/adminconfirm/<token>')
def adminconfirm(token):
    try:
        # Verify the token
        serializer = URLSafeTimedSerializer(secret_key)
        data = serializer.loads(token, salt=salt, max_age=180)
    except Exception as e:
        abort (404,'Link Expired register again')
    else:
        cursor = mysql.connection.cursor()
        email=data['email']

        # Check if the user is already registered
        cursor.execute('SELECT COUNT(*) FROM therapists WHERE email = %s', [email])
        count = cursor.fetchone()

        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('therapists_login'))
        else:
            cursor.execute('INSERT INTO therapists (name, email, password,specialties,credentials,experience) VALUES (%s, %s, %s,%s,%s,%s)', [data['username'], data['email'], data['password'],data['specialties'],data['credentials'],data['experience']])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('therapists_login'))

@app.route('/therapists_login', methods=['GET', 'POST'])
def therapists_login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT count(*) as h from therapists where email=%s and password=%s',[email,password])
        count=cursor.fetchone()
        if count[0]==1:  # Fix here
            session['user1']=email
            if not session.get('user1'):
                session['user1']={}
            return redirect(url_for('therapists_home'))
        else:
            flash('Invalid username or password')
            return render_template('therapists_home.html')

    return render_template('therapists_login.html')
@app.route('/therapists_home')
def therapists_home():
    if 'user1' in session:
        user_email=session['user1']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM therapists WHERE email = %s', [user_email])
        user_data = cursor.fetchone()
        print(user_data)
        cursor.close()
        if user_data:
            return render_template('therapists_home.html', user=user_data)
        else:
            # User not found, handle the case accordingly
            flash('User data not found.')
            return redirect(url_for('therapists_login'))
    return render_template('therapists_home.html')
@app.route('/admin_profile')
def admin_profile():
    if 'user1' in session:
        user_email = session['user1']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM therapists WHERE email = %s', [user_email])
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return render_template('therapists_profile.html', user=user_data)
        else:
            # User not found, handle the case accordingly
            flash('User data not found.')
            return redirect(url_for('therapists_login'))
    else:
        # User not logged in, redirect to login page
        return redirect(url_for('therapists_login'))

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if request.method == 'POST':
        # Get the form data
        selected_time = request.form['appointment_time']
        therapist_id = request.args.get('therapist_id')  # Get therapist_id from URL query parameter

        # Convert selected time to datetime format
        start_time = datetime.strptime(selected_time, '%I:%M %p')

        # Get user_id from the session
        if 'user' in session:
            user_email = session['user']
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT user_id FROM users WHERE email = %s', [user_email])
            user_id = cursor.fetchone()[0]  # Assuming user_id is the first column returned
            cursor.close()
        else:
            # Handle the case when user is not logged in
            flash('You are not logged in.')
            return redirect(url_for('user_login'))

        # Define SQL query to insert appointment data
        insert_query = "INSERT INTO Appointments (user_id, therapist_id, start_time, status) VALUES (%s, %s, %s, %s)"

        # Execute the query with data
        cursor = mysql.connection.cursor()
        cursor.execute(insert_query, (user_id, therapist_id, start_time, 'pending'))
        mysql.connection.commit()
        cursor.close()

        # Redirect to a success page or wherever you want
        return "success"

    # Handle cases where method is not POST
    return "error"

@app.route('/view_appointments')
def view_appointments():
    if 'user1' in session:
        therapist_email = session['user1']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT therapist_id FROM therapists WHERE email = %s', [therapist_email])
        therapist_id = cursor.fetchone()[0]  # Assuming therapist_id is the first column returned
        cursor.execute('''
            SELECT * FROM appointments 
            WHERE therapist_id = %s
        ''', [therapist_id])
        appointments_data = cursor.fetchall()
        cursor.close()
        return render_template('view_appointments.html', appointments=appointments_data)
    else:
        # If therapist is not logged in, redirect to login page
        return redirect(url_for('therapists_login'))




@app.route('/update_status/<int:appointment_id>', methods=['POST'])
def update_status(appointment_id):
    new_status = request.form['status']
    # Update the appointment status in the database
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE appointments SET status = %s WHERE appointment_id = %s', (new_status, appointment_id))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('view_appointments'))

from datetime import datetime, timedelta


@app.route('/today_appointments')
def today_appointments():
    print(session.get('user1'))
    if 'user1' in session:
        user_email = session['user1']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT therapist_id FROM therapists WHERE email = %s', [user_email])
        user_id = cursor.fetchone()[0]  # Assuming user_id is the first column returned
        
        # Get today's date
        today = datetime.now().date()

        # Fetch appointments for today along with user details
        cursor.execute('''
            SELECT a.appointment_id, a.start_time, a.status, u.username, u.email 
            FROM appointments AS a
            JOIN users AS u ON a.user_id = u.user_id 
            WHERE a.user_id = %s AND DATE(a.created_at) = %s
        ''', (user_id, today))
        
        appointments_data = cursor.fetchall()
        cursor.close()

        # Debugging statement
        print(appointments_data)

        return render_template('todays_appointments.html', appointments=appointments_data)
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('therapists_login'))




@app.route('/store_message/<therapist_id>', methods=['GET', 'POST'])
def store_message(therapist_id):
    print(therapist_id)
    if session.get('user') or session.get('vendor'):  # Allow both users and vendors
        if session.get('user'):
            user_type = 'sender'  # User is sender
        else:
            user_type = 'receiver'  # Vendor is receiver

        if 'user' in session:
            user_email = session['user']
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT user_id FROM users WHERE email=%s', [user_email])
            user_id = cursor.fetchone()[0]
            cursor.close()
            cursor = mysql.connection.cursor()
            # cursor.execute("SELECT * FROM chat_messages WHERE (sender_id=%s and receiver_id = %s) ORDER BY timestamp", (therapist_id,user_id))
            # messages = cursor.fetchall()
            # cursor.close()
            # print(messages)
            # sender = [(msg[0], msg[1], msg[2],msg[3],msg[5]) for msg in messages if msg[1] == user_id]
            # receiver = [(msg[0], msg[1], msg[2],msg[3],msg[5]) for msg in messages if msg[1] != user_id]
            # print(sender)
             
            cursor.execute("SELECT * FROM chat_messages WHERE (sender_id=%s and receiver_id = %s) ORDER BY timestamp", (therapist_id,user_id))
            messages = cursor.fetchall()
            print(messages)
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM chat_messages WHERE (receiver_id=%s and sender_id = %s ) ORDER BY timestamp", (therapist_id,user_id))
            messages2 = cursor.fetchall()
            print(messages2)
            cursor.close()
            message=messages+messages2

            sender = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] == user_id]
            receiver = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] != user_id]



            if request.method == 'POST':
                message = request.form['Message']
                file=request.files['file']
                filename=genotp()+'.jpg'
                path=os.path.dirname(os.path.abspath(__file__))
                static_path=os.path.join(path,'static')
                file.save(os.path.join(static_path,filename))
                cursor = mysql.connection.cursor()
                cursor.execute('INSERT INTO chat_messages (sender_id, receiver_id, message,file_path) VALUES (%s, %s, %s,%s)', (user_id, therapist_id, message,filename))
                mysql.connection.commit()
                cursor.close()

                # Redirect to a GET request to prevent duplicate form submission

                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM chat_messages WHERE (sender_id=%s and receiver_id = %s) ORDER BY timestamp", (therapist_id,user_id))
                messages = cursor.fetchall()
                print(messages)
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM chat_messages WHERE (receiver_id=%s and sender_id = %s ) ORDER BY timestamp", (therapist_id,user_id))
                messages2 = cursor.fetchall()
                print(messages2)
                cursor.close()
                message=messages+messages2

                sender = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] == user_id]
                receiver = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] != user_id]
                return redirect(url_for('store_message', therapist_id=therapist_id))



            return render_template('chatting.html', sender=sender, receiver=receiver, sender_id=therapist_id, receiver_id=user_id)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route('/therapists_message/<u_id>', methods=['GET', 'POST'])
def therapists_message(u_id):
    if session.get('user') or session.get('user1'):  # Allow both users and vendors
        if session.get('user'):
            user_type = 'sender'  # User is sender
        else:
            user_type = 'receiver'  # Vendor is receiver
        if 'user1' in session:
            user_email = session['user1']
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT therapist_id FROM therapists WHERE email=%s', [user_email])
            user_id = cursor.fetchone()[0]
            cursor.close()
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM chat_messages WHERE (sender_id=%s and receiver_id = %s) ORDER BY timestamp", (u_id,user_id))
            messages = cursor.fetchall()
            print(messages)
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM chat_messages WHERE (receiver_id=%s and sender_id = %s ) ORDER BY timestamp", (u_id,user_id))
            messages2 = cursor.fetchall()
            print(messages2)
            cursor.close()
            message=messages+messages2

            sender = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] == user_id]
            receiver = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] != user_id]

            if request.method == 'POST':
                message = request.form['Message']
                file=request.files['file']
                filename=genotp()+'.jpg'
                path=os.path.dirname(os.path.abspath(__file__))
                static_path=os.path.join(path,'static')
                file.save(os.path.join(static_path,filename))
                cursor = mysql.connection.cursor()
                cursor.execute('INSERT INTO chat_messages (sender_id, receiver_id, message,file_path) VALUES (%s, %s, %s,%s)', (user_id, u_id, message,filename))
                mysql.connection.commit()
                cursor.close()

                # Redirect to a GET request to prevent duplicate form submission
               
                cursor = mysql.connection.cursor()
                cursor.execute('SELECT therapist_id FROM therapists WHERE email=%s', [user_email])
                user_id = cursor.fetchone()[0]
                cursor.close()
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM chat_messages WHERE (sender_id=%s and receiver_id = %s) ORDER BY timestamp", (u_id,user_id))
                messages = cursor.fetchall()
                print(messages)
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM chat_messages WHERE (receiver_id=%s and sender_id = %s ) ORDER BY timestamp", (u_id,user_id))
                messages2 = cursor.fetchall()
                print(messages2)
                cursor.close()
                message=messages+messages2

                sender = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] == user_id]
                receiver = [(msg[0], msg[1], msg[2],msg[3],msg[4],msg[5]) for msg in message if msg[1] != user_id]
                return redirect(url_for('therapists_message', u_id=u_id))


            return render_template('chatting.html', sender=sender, receiver=receiver, sender_id=u_id, receiver_id=user_id)
        else:
            return render_template(url_for('chatting.html'))
    else:
        return redirect(url_for('therapists_login'))
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the appropriate login page
    return redirect(url_for('user_login'))

@app.route('/therapist_logout')
def therapist_logout():
    # Clear the session
    session.pop('user1')
    # Redirect to the therapist login page
    return redirect(url_for('therapists_login'))


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        search_term = request.form['search_name']
        # Ignore case when searching for specialties
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM therapists WHERE LOWER(specialties) LIKE %s", ['%' + search_term.lower() + '%'])
        therapists_data = cursor.fetchall()
        cursor.close()
        return render_template('search_results.html', therapists=therapists_data)
    # Handle cases where method is not POST
    return "error"

@app.route('/cancel_appointment/<int:appointment_id>')
def cancel_appointment(appointment_id):
    print(appointment_id,78)
   
        # Connect to the database
    cursor = mysql.connection.cursor()
        
        # Delete the appointment record from the database
    cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
        
        # Commit the changes to the database
    mysql.connection.commit()
        
        # Close the database connection
    cursor.close()
        
        # Flash a success message
    flash('Appointment canceled successfully.', 'success')
        
        # Redirect to the view appointments page or any other appropriate page
    return redirect(url_for('user_home'))
    
    # Render a template with a form for confirmation
    
@app.route('/make_payment')
def make_payment():
    if session.get('user'):
        user_email = session.get('user')
        amount = 100

        checkout_session = stripe.checkout.Session.create(
            success_url=url_for('success_payment', _external=True),
            cancel_url=url_for('cancel_payment', _external=True),
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': 'Pay to doctor',
                    },
                    'unit_amount': amount*100,
                },
                'quantity': 1,
            }],
            customer_email=user_email,
        )

        return redirect(checkout_session.url)

    else:
        return redirect(url_for('userlogin'))

@app.route('/success_payment')
def success_payment():
    if session.get('user'):
        user_email = session.get('user')
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT user_id FROM users WHERE email = %s', [user_email])
        user_id = cursor.fetchone()[0]  # Retrieve user_id from the database
        cursor.execute('UPDATE appointments SET payment = "paid" WHERE user_id = %s', [user_id])
        mysql.connection.commit()
        cursor.close()
        flash('Payment successful. You can now process the certificate.')
        return "Done payment"
    else:
        return 'Payment successful.'

@app.route('/cancel_payment')
def cancel_payment():
    return 'Payment canceled.'
    
app.run(use_reloader=True,debug=True)
