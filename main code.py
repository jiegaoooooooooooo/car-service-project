#set up: import libraries and modules
import requests           
import os    
import sqlite3                
from flask import Flask, render_template, request, redirect, session, flash  
import socket                 
from datetime import datetime, timedelta  
import bcrypt                 

app = Flask(__name__)

# Set the secret key to secure sessions 
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key')

#-------------------------------------------------------------------
# Before each request, set the username globally in the template
@app.before_request
def display_username():
    username = session.get('username')
    if username:
        app.jinja_env.globals['username'] = username  # Makes the username available in all templates
    else:
        app.jinja_env.globals['username'] = None
        
#-------------------------------------------------------------------
# Landing page route
@app.route('/')
def landing():
    return render_template('landing.html')

#-------------------------------------------------------------------
# Login page route to display the login form
@app.route('/login')
def login():
    return render_template('login.html')

#-------------------------------------------------------------------
# Logout route clears the session and redirects to the landing page
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#-------------------------------------------------------------------
# Authentication route to process login credentials
@app.route('/authenticate', methods=["get", "post"])
def authenticate():
    # Connect to the database
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    
    # Get username and password from the form
    username = str(request.form['username'])
    password = str(request.form['password']).encode('utf-8')
    
    # Retrieve user details from the database based on username
    cursor.execute("""SELECT userID, userPassword, userType 
                      FROM tblUser
                      WHERE tblUser.userName = ?""", (username,))
    authenticate_data = cursor.fetchone()
    
    # Check if user exists and provided password matches the hashed password
    if authenticate_data and bcrypt.checkpw(password, authenticate_data[1]):
        session['userId'] = authenticate_data[0]
        session['username'] = username
        user_type = authenticate_data[2]
        conn.close()
        # Redirect based on user type
        if user_type == "staff":
            return redirect('/checkIn')
        elif user_type == "customer":
            return redirect('/customer')
        else:
            return redirect('/manager')
    else:
        conn.close()
        # Render login page with error message if authentication fails
        return render_template('login.html', error="Username or password is wrong. Please try again!")

#-------------------------------------------------------------------
# Route to display the sign up page
@app.route('/signUp')
def signUp():
    return render_template('signUp.html')

#-------------------------------------------------------------------
# Create account route: processes sign-up form submission
@app.route('/createAccount', methods=["get", "post"])
def createAccount(): 
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()

    username = str(request.form['username'])
    password = str(request.form['password']).encode('utf-8')
    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    
    # Insert a new customer record; rollback and show error if username already exists
    try:
       cursor.execute("INSERT INTO tblUser VALUES(?,?,?,?)", (None, username, hashed_password, "customer"))
    except:
       conn.rollback()
       return render_template("signUp.html", error="Username already exists. Please choose a different username.")
    conn.commit()
    conn.close()
    return redirect('/login')

#-------------------------------------------------------------------
# Route to display the reset password page
@app.route('/resetPassword')
def resetPassword():
    return render_template('resetPassword.html')

#-------------------------------------------------------------------
# Change password route: processes password reset requests
@app.route('/changePassword', methods=["get", "post"])
def changePassword():
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    
    # Get form data: current username, current password and new password
    username = str(request.form['username'])
    password = str(request.form['password']).encode('utf-8')
    newPassword = str(request.form['newPassword']).encode('utf-8')
    hashed_password = bcrypt.hashpw(newPassword, bcrypt.gensalt())
    
    # Verify current password
    cursor.execute("""SELECT userPassword
                      FROM tblUser
                      WHERE tblUser.userName = ?""", (username,))
    authenticate_data = cursor.fetchone()
    if authenticate_data and bcrypt.checkpw(password, authenticate_data[0]):
        # Update password in the database if current password is correct
        cursor.execute("UPDATE tblUser SET userPassword = ? WHERE userName = ?", (hashed_password,username, ))
        conn.commit()
        conn.close()
        return redirect('/login')
    else:
        conn.close()
        return render_template('resetPassword.html', error="Username or password is wrong. Please try again!")

#-------------------------------------------------------------------
# Route to display the add car page
@app.route('/addCar')
def addCar():
    return render_template('addCar.html')

#-------------------------------------------------------------------
# Route to process car registration number and fetch vehicle data from an external API
@app.route('/regNumber', methods=['GET', 'POST'])
def regNumber():
  url = "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles"
  reg = str(request.form['regNumber'])
  payload = {"registrationNumber": reg}
  headers = {
    'x-api-key': 'ciMvGeHcY85HvJJsO2XPy1BN8hX8ZAaK6wb03hGl',
    'Content-Type': 'application/xml'
  }
  response = requests.post(url, headers=headers, json=payload)
  
  # Extract keys (titles) from API response and store in session
  title = []
  for i in response.json():
    title.append(i)
  session['title'] = title
  
  # Extract values (details) from API response and store in session
  detail = []
  for i in response.json().values():
    detail.append(i)
  session['detail'] = detail
  
  return redirect('/detail')
  
#-------------------------------------------------------------------
# Route to display vehicle details and allow additional input (e.g., car model)
@app.route('/detail', methods=['GET', 'POST'])
def detail():       
  detail = session.get('detail')
  title = session.get('title')
  num = len(detail)
  
  # If the API returns an error, render an error page
  if title[0] == "errors":
    return render_template('error.html')
  
  # If a POST request with car model is made, update the details
  if request.method == 'POST':
        model = request.form.get('model')
        if model:
            model = model.upper()
            detail.append(model)
            title.append("model")
            session['detail'] = detail
            session['title'] = title
            return redirect('/detail')  
  return render_template('detail.html', detail=detail, title=title, num=num)

#-------------------------------------------------------------------
# Route to store the vehicle details into the database
@app.route('/store_detail', methods=['GET', 'POST'])
def store_detail():
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor() 

    detail = session.get('detail')
    userId = session.get('userId')
    regNumber = detail[0]
    make = detail[4]
    type = detail[-1]
    # Insert the new car into tblCar, preventing duplicates
    try:
      cursor.execute('''INSERT INTO tblCar VALUES (?,?,?,?)''', (regNumber, make, type, userId))
      conn.commit()
      conn.close()
    except:
       conn.rollback()
       return render_template("addCar.html", error="This car already exists. Please enter a different car.")
    return redirect('/customer')

#-------------------------------------------------------------------
# Customer dashboard: displays all cars associated with the logged-in user
@app.route('/customer', methods=["get","post"])
def customer():
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    userId = session.get('userId')

    car = cursor.execute("""SELECT * FROM tblCar WHERE userId = ?""", (userId,))
    listOfCar = []
    for each in car:
        listOfCar.append(each)

    conn.close()
    return render_template('customer.html', car=listOfCar)

#-------------------------------------------------------------------
# Route to fetch and display detailed information for a specific car using its registration number
@app.route('/car_detail/<reg>', methods=["get","post"])
def car_detail(reg):
  url = "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles"
  payload = {"registrationNumber": reg}
  headers = {
    'x-api-key': 'ciMvGeHcY85HvJJsO2XPy1BN8hX8ZAaK6wb03hGl',
    'Content-Type': 'application/xml'
  }
  response = requests.post(url, headers=headers, json=payload)
  title = []
  for i in response.json():
    title.append(i)
  detail = []
  for i in response.json().values():
    detail.append(i)
  num = len(title)
  return render_template('car_detail.html', detail=detail, title=title, num=num)

#-------------------------------------------------------------------
# Route to delete a car from the customer's account
@app.route('/delete_car/<reg>', methods=["get","post"])
def delete_car(reg):
    userId = session.get('userId')
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""DELETE FROM tblCar WHERE userId = ? AND registrationNumber = ?""", (userId, reg,))
    conn.commit()
    conn.close()
    return redirect('/customer')
   
#-------------------------------------------------------------------
# Route to display the booking page for a specific car with the current date
@app.route('/booking/<reg>', methods=["get","post"])
def booking(reg):
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('booking.html', reg=reg, today=today)

#-------------------------------------------------------------------
# Route to add a booking record for a car service
@app.route('/add_booking/<reg>', methods=["get","post"])
def add_booking(reg):
    service = request.form.get('service')
    detail = request.form.get('detail')
    other_service = request.form.get('otherService')
    date = request.form.get('date')

    # Use the alternative service description if "Other" is selected
    if service == 'Other':
        service = other_service

    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tblService VALUES (?,?,?,?,?,?,?,?)''', (None, None, service, "Scheduled", date, None, reg, detail,))
    conn.commit()
    conn.close()
    
    return redirect(f'/record/{reg}')    

#-------------------------------------------------------------------
# Route to display service records for a particular car
@app.route('/record/<reg>', methods=["get","post"])
def record(reg):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    record = cursor.execute("""SELECT type, status, date, price, serviceId, regNumber FROM tblService WHERE regNumber = ?""", (reg,))
    listOfRecord = []
    for each in record:
        listOfRecord.append(each)
    return render_template('record.html', record=listOfRecord)

#-------------------------------------------------------------------
# Route to delete a service record
@app.route('/delete_record/<reg>/<id>', methods=["get","post"])
def delete_record(reg, id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""DELETE FROM tblService WHERE serviceId = ?""", (id,))
    conn.commit()
    conn.close()
    return redirect(f'/record/{reg}')   

#-------------------------------------------------------------------
# Staff check-in route: prevents multiple check-ins on the same day
@app.route('/checkIn', methods=["get","post"])
def checkIn():
    today = datetime.today().strftime('%Y-%m-%d')
    userId = session.get('userId')
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM tblCheckIn WHERE userId = ? AND date = ?""", (userId, today,))
    result = cursor.fetchone()
    # If already checked in today, redirect to staff dashboard
    if result:
        conn.close()
        return redirect('/staff')
    else:
        cursor.execute("INSERT INTO tblCheckIn VALUES(?,?,?)", (None, userId, today,))
        conn.commit()
        conn.close()
        return redirect('/staff')
    
#-------------------------------------------------------------------
# Staff dashboard: shows pending service jobs assigned to or available for the staff member
@app.route('/staff', methods=["get","post"])
def staff():
    today = datetime.today().strftime('%Y-%m-%d')
    staffId = session.get('userId')
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    # Fetch scheduled jobs with service date on or before today
    job = cursor.execute("""SELECT regNumber, type, make, carModel, serviceId, status 
                            FROM tblService, tblCar 
                            WHERE date <= ? AND status = "Scheduled" AND registrationNumber = regNumber""", (today,))
    listOfJob = []
    for each in job:
        listOfJob.append(each)
    # Include jobs that have been paused and already assigned to the current staff member
    waiting = cursor.execute("""SELECT regNumber, type, make, carModel, serviceId, status 
                                FROM tblService, tblCar 
                                WHERE date <= ? AND status = "Paused" AND registrationNumber = regNumber AND staffId = ?""", (today, staffId,))
    for each in waiting:
        listOfJob.append(each)
    conn.close()
    return render_template('staff.html', job=listOfJob, id=staffId)

#-------------------------------------------------------------------
# Route to display additional notes for a specific service job
@app.route('/additional_notes/<id>', methods=["get","post"])
def additional_notes(id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT detail FROM tblService WHERE serviceId = ?""", (id,))
    result = cursor.fetchone()
    detail = result[0]
    conn.close()
    return render_template('additional_notes.html', detail=detail)

#-------------------------------------------------------------------
# Route to assign a staff member to a service job and mark it as 'Working'
@app.route('/store_staffId/<reg>/<id>/<make>', methods=["get","post"])
def store_staffId(reg, id, make):
    session['reg'] = reg
    session['serviceId'] = id
    session['make'] = make
    staffId = session.get('userId')
    today = datetime.today().strftime('%Y-%m-%d')
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("SELECT staffId FROM tblService WHERE serviceId = ?", (id,))
    result = cursor.fetchone()
    # Prevent multiple staff members from taking the same job concurrently
    if result[0] is not None and result[0] != staffId:
        conn.close()
        return render_template("staff.html", error="Someone already take this job. Please choose a different job or work together with this person.")
    cursor.execute("""UPDATE tblService SET staffId = ?, status = 'Working', date = ? WHERE serviceId = ?""", (staffId, today, id,))
    conn.commit()
    conn.close()
    return redirect('/job')

#-------------------------------------------------------------------
# Route to display job details and allow staff to add parts, problems, or collaborate with other staff
@app.route('/job', methods=["get","post"])
def job():
    reg = session.get('reg')
    make = session.get('make')
    serviceId = session.get('serviceId')
    staffId = session.get('userId')
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    
    # Retrieve the type of service for the current job
    cursor.execute("""SELECT type FROM tblService WHERE serviceId = ?""", (serviceId,))
    result = cursor.fetchone()
    type = result[0]
    
    # Retrieve parts used for this service
    parts = cursor.execute("""SELECT parts, type, date, partId 
                              FROM tblService, tblParts 
                              WHERE tblService.serviceId = tblParts.serviceId AND regNumber = ?""", (reg,))    
    listOfParts = []
    for each in parts:
        listOfParts.append(each)
    
    # Get car model from tblCar based on registration number
    cursor.execute("""SELECT carModel FROM tblCar WHERE registrationNumber = ?""", (reg,))    
    result = cursor.fetchone()
    model = result[0]
    
    # Retrieve reported problems for this service job
    problem = cursor.execute("""SELECT problem, type, date 
                                FROM tblService, tblProblem, tblCar 
                                WHERE tblService.serviceId = tblProblem.serviceId 
                                AND regNumber = registrationNumber 
                                AND carModel = ? 
                                AND make = ?""", (model, make,))
    listOfProblem = []
    for each in problem:
        listOfProblem.append(each)
    
    # Get additional notes from the service record
    cursor.execute("""SELECT detail FROM tblService WHERE serviceId = ?""", (serviceId,))
    result = cursor.fetchone()
    note = result[0]
    
    # Retrieve list of other staff members for collaboration (excluding current staff)
    staff = cursor.execute("""SELECT userName FROM tblUser WHERE userType = 'staff' AND userId != ?""", (staffId,))
    listOfStaff = []
    for each in staff:
        listOfStaff.append(each[0])
    
    # Fetch vehicle information from the external API
    url = "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles"
    payload = {"registrationNumber": reg}
    headers = {
      'x-api-key': 'ciMvGeHcY85HvJJsO2XPy1BN8hX8ZAaK6wb03hGl',
      'Content-Type': 'application/xml'
    }
    response = requests.post(url, headers=headers, json=payload)
    title = []
    for i in response.json():
      title.append(i)
    detail = []
    for i in response.json().values():
      detail.append(i)
    num = len(title)
    conn.close()
    return render_template('job.html', reg=reg, serviceId=serviceId, type=type, parts=listOfParts, problem=listOfProblem, model=model, make=make, detail=detail, title=title, num=num, note=note, staff=listOfStaff)

#-------------------------------------------------------------------
# Route to pause a service job
@app.route('/pause/<id>', methods=["get","post"])
def pause(id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE tblService SET status = 'Paused' WHERE serviceId = ?""", (id,))
    conn.commit()
    conn.close()
    return redirect('/staff')

#-------------------------------------------------------------------
# Route to add parts used during a service job
@app.route('/addParts', methods=["get", "post"])
def addParts(): 
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    parts = request.form['parts']
    partId = request.form['partId']
    serviceId = session.get('serviceId')
    cursor.execute("INSERT INTO tblParts VALUES(?,?,?,?)", (None, parts, serviceId, partId))
    conn.commit()
    conn.close()
    return redirect('/job')

#-------------------------------------------------------------------
# Route to add a problem encountered during a service job
@app.route('/addProblem', methods=["get", "post"])
def addProblem(): 
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    problem = request.form['problem']
    serviceId = session.get('serviceId')
    cursor.execute("INSERT INTO tblProblem VALUES(?,?,?)", (None, problem, serviceId,))
    conn.commit()
    conn.close()
    return redirect('/job')

#-------------------------------------------------------------------
# Route to add another staff member to assist on a service job
@app.route('/addStaff', methods=["GET", "POST"])
def addStaff(): 
    if request.method == "POST":
        staff = request.form.get('staff')
        serviceId = session.get('serviceId')
        conn = sqlite3.connect("carService.db")
        cursor = conn.cursor()
        # Prevent adding the same staff member twice
        try:
            cursor.execute("INSERT INTO tblServiceStaff VALUES (?, ?, ?)", (None, serviceId, staff))
            conn.commit()
            conn.close()
        except:
            conn.rollback()
            conn.close()
            flash("This staff was already added.", "error")
            return redirect('/job')
    return redirect('/job')

#-------------------------------------------------------------------
# Route to mark a service job as complete
@app.route('/complete/<id>', methods=["get","post"])
def complete(id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE tblService SET status = 'Done' WHERE serviceId = ?""", (id,))
    conn.commit()
    conn.close()
    return redirect('/staff')
  
#-------------------------------------------------------------------
# Route to display attendance records for the last 30 days for a staff member
@app.route('/attendance/<id>', methods=["get","post"])
def attendance(id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT date FROM tblCheckIn WHERE userId = ?""", (id,))
    records = cursor.fetchall()
    listOfDate = [record[0] for record in records]
    today = datetime.today()
    new_date = today - timedelta(days=29)
    date = new_date.strftime('%Y-%m-%d')
    thirty_days_list = []
    color = []
    # For each day, mark green if present, red if absent
    for i in range(30):
        thirty_days_list.append(date)
        if date in listOfDate:
            color.append("green")
        else:
            color.append("red")
        new_date = today - timedelta(days=29-(i+1))
        date = new_date.strftime('%Y-%m-%d')
    conn.close()
    date_color = zip(thirty_days_list, color)
    return render_template('attendance.html', date_color=date_color, id=id)

#-------------------------------------------------------------------
# Route to display the job history for a staff member
@app.route('/jobHistory', methods=["get","post"])
def jobHistory():
    staffId = session.get('userId')
    id = session.get('userId')
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    record = cursor.execute("""SELECT type, status, date, make, carModel, regNumber 
                               FROM tblService, tblCar 
                               WHERE regNumber = registrationNumber AND staffId = ?""", (id,))
    listOfRecord = record.fetchall()
    return render_template('jobHistory.html', record=listOfRecord, id=staffId)

#-------------------------------------------------------------------
# Manager dashboard: displays all service records along with details and associated staff
@app.route('/manager', methods=["GET", "POST"])
def manager():
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    record = cursor.execute("""SELECT tblService.type, tblService.status, tblService.date, tblService.price, tblService.serviceId, tblUser.userName, GROUP_CONCAT(tblServiceStaff.staffName, ', ') as helpStaff, tblCar.make, tblCar.carModel
                               FROM tblService
                               LEFT JOIN tblUser ON tblService.staffId = tblUser.userId
                               LEFT JOIN tblCar ON tblCar.registrationNumber = tblService.regNumber
                               LEFT JOIN tblServiceStaff ON tblService.serviceId = tblServiceStaff.serviceId
                               GROUP BY tblService.serviceId
                               ORDER BY tblService.date DESC""")
    listOfRecord = record.fetchall()
    status = cursor.execute("""SELECT tblService.status
                               FROM tblService
                               ORDER BY tblService.date DESC""")
    listOfStatus = status.fetchall()
    # Assign a color to each record based on its status
    color = []
    for status in listOfStatus:
        if status[0] == "Scheduled":
            color.append("#add8e6")
        elif status[0] == "Working":
            color.append("orange")
        elif status[0] == "Paused":
            color.append("red")
        elif status[0] == "Done":
            color.append("green")
        elif status[0] == "Paid":
            color.append("white")
    conn.close()
    record_color = zip(listOfRecord, color)
    return render_template('manager.html', record_color=record_color)

#-------------------------------------------------------------------
# Route to delete a service record (manager function)
@app.route('/deleteRecord/<id>', methods=["get","post"])
def deleteRecord(id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""DELETE FROM tblService WHERE serviceId = ?""", (id,))
    conn.commit()
    conn.close()
    return redirect('/manager')

#-------------------------------------------------------------------
# Route to update the price and mark a service job as "Paid"
@app.route('/enterPrice/<id>', methods=["get","post"])
def enterPrice(id):
    price = str(request.form['price'])
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE tblService SET price = ?, status = "Paid" WHERE serviceId = ?""", (price, id,))
    conn.commit()
    conn.close()
    return redirect('/manager')

#-------------------------------------------------------------------
# Route to display detailed service information including parts and problems
@app.route('/serviceDetail/<id>', methods=["get","post"])
def carPartsService(id):
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    parts = cursor.execute("""SELECT parts FROM tblParts WHERE serviceId = ?""", (id,))
    listOfParts = parts.fetchall()
    porblems = cursor.execute("""SELECT problem FROM tblProblem WHERE serviceId = ?""", (id,))
    listOfProblems = porblems.fetchall()
    return render_template('serviceDetail.html', parts=listOfParts, problems=listOfProblems)

#-------------------------------------------------------------------
# Route to display the create staff account page
@app.route('/createStaffAccount')
def createStaffAccount():
    return render_template('createStaffAccount.html')

#-------------------------------------------------------------------
# Route to process the creation of a new staff account
@app.route('/create_Staff_Account', methods=["get", "post"])
def create_Staff_Account(): 
    conn = sqlite3.connect("carService.db")
    cursor = conn.cursor()
    username = str(request.form['username'])
    password = str(request.form['password']).encode('utf-8')
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    # Insert new staff record; if duplicate username occurs, rollback and show error
    try:
       cursor.execute("INSERT INTO tblUser VALUES(?,?,?,?)", (None, username, hashed_password, "staff"))
    except:
       conn.rollback()
       return render_template("createStaffAccount.html", error="Username already exists. Please enter a different username.")
    conn.commit()
    conn.close()
    return redirect('/createStaffAccount')

#-------------------------------------------------------------------
# Main entry point: obtains the local IP address and runs the Flask app on all available network interfaces
if __name__ == "__main__":
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.connect(('8.8.8.8', 1))
   local_ip_address = s.getsockname()[0]
   print("Local IP Address :", local_ip_address)
   app.run(host="0.0.0.0")
