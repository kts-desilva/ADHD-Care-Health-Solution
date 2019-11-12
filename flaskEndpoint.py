from med2image import med2image
from keras.models import load_model
from keras.preprocessing import image
import cv2
import numpy as np
import os
import tablib
from flask import Flask, render_template, request, flash, redirect, request, jsonify, session,g, render_template
import tensorflow as tf
from werkzeug import secure_filename
from sklearn.externals import joblib
import pandas as pd
from flask_mysqldb import MySQL

from nipype.interfaces import fsl
import time
from flask_mail import Mail, Message

from keras import backend as K

from flask_session import Session

from nilearn.image.image import mean_img
from nilearn.plotting import plot_epi
import nibabel
from matplotlib import pyplot as plt

nii_file = "" #fmri data file
csv_file = "" #eye movement data file

fmri_status = 0  #fmri data prediction status
preproc_status = 0 #fmri preprocessing status
fex_status = 0 #fmri feature extraction status
em_status = 0 #eye movement data prediction status

def getfMRIModel():
    fmri_model = load_model('fmri_model.h5')
    fmri_model.compile(loss='binary_crossentropy',optimizer='rmsprop', metrics=['accuracy'])
    return fmri_model

def getEyeMovementModel():
    em_model = joblib.load('eye_movement_ensembled.pkl')
    return em_model

def getEyeMovementPrediction():
    global csv_file
    
    em_model= getEyeMovementModel()

    predict_data = pd.read_csv(csv_file, index_col=[0])

    # Onehot encoding for gender (binary) column
    predict_data['Gender'] = pd.get_dummies(predict_data['Gender'], prefix='Gender')

    predictions = em_model.predict(predict_data)
    counts = np.bincount(predictions)
    bclass=np.argmax(counts) # Get the highest probable class

    probValue=0
    if(bclass==1):
        probValue=counts[1]/sum(counts)
    else:
        probValue=counts[0]/sum(counts)
        if probValue ==1:
            probValue=0.11
    K.clear_session()
    return probValue

def preporcessFMRI():
    global nii_file, preproc_status

    # skull stripping
    btr = fsl.BET()
    btr.inputs.in_file = nii_file
    btr.inputs.frac = 0.7
    btr.inputs.out_file = nii_file
    btr.cmdline
    res = btr.run()
    preproc_status = 20

    # segmentation and bias correction
    fastr = fsl.FAST()
    fastr.inputs.in_files = nii_file
    fastr.cmdline
    out = fastr.run()
    preproc_status = 40

    # coregistration
    flt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
    flt.inputs.in_file = nii_file
    flt.inputs.reference = nii_file
    flt.inputs.output_type = "NIFTI_GZ"
    preproc_status = 45
    flt.cmdline
    preproc_status = 50
    res = flt.run()
    preproc_status = 60

    # motion correction
    mcflt = fsl.MCFLIRT()
    mcflt.inputs.in_file = nii_file
    mcflt.inputs.cost = 'mutualinfo'
    mcflt.inputs.out_file = nii_file
    mcflt.cmdline
    res = mcflt.run()
    preproc_status = 80

    # smoothing
    sus = fsl.SUSAN()
    sus.inputs.in_file = nii_file
    sus.inputs.out_file = nii_file
    sus.inputs.brightness_threshold = 2000.0
    sus.inputs.fwhm = 8.0
    result = sus.run()
    preproc_status = 100

def resetValues():
    global fmri_status, preproc_status, fex_status, em_status

    if(fmri_status == 100 and preproc_status == 100 and fex_status == 100):
        fmri_status = 0
        preproc_status = 0
        fex_status = 0

    if (em_status == 100):
        em_status = 0

def getFMRIPrediction():
    global nii_file, fmri_status, fex_status

    preporcessFMRI()

    time.sleep(2)

    fex_status = 50
    c_convert = med2image.med2image_nii(inputFile=nii_file, outputDir="temp9", outputFileStem="image",
                                        outputFileType="png", sliceToConvert='-1', frameToConvert='0', showSlices=False, reslice=False)
    time.sleep(1)
    fex_status = 100
    time.sleep(2)

    med2image.misc.tic()
    c_convert.run()
    fmri_status = 40
    
    fmri_model = getfMRIModel()

    images = []

    for img in os.listdir('/home/adhd/adhd_cnn/dataFolder/temp9/'):
        img = cv2.imread('temp9/'+img)
        # img=img.astype('float')/255.0
        img = cv2.resize(img, (73, 61))
        img = np.reshape(img, [1, 73, 61, 3])
        images.append(img)

    images = np.vstack(images)

    clas = fmri_model.predict_classes(images, batch_size=10)
    fmri_status = 60

    print('Possibility of ADHD: ', (clas == 0).sum()/len(clas))
    print('Possibility of non-ADHD: ', (clas == 1).sum()/len(clas))

    adhd = (clas == 0).sum()/len(clas)
    nadhd = (clas == 1).sum()/len(clas)
    K.clear_session()   #To avoid reinstantiation of Tensorflow graph
    return adhd

def storeData(fname, lname, email, age, diag, score, data_type, user, symptoms, chronicDisease):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Diagnosis (Patient_first_name,Patient_last_name,Email,Age,Diagnosis,Composite_Score,Data_Type,User,Symptoms,Test_date,Test_time,ChronicDisease) VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,CURDATE(),CURTIME(),%s)",
                (fname, lname, email, age, diag, score, data_type, user, symptoms,chronicDisease))
    mysql.connection.commit()
    cur.close()

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = '/home/adhd/adhd_cnn/dataFolder/uploads'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'ADHD'

app.config.update(dict(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='adhdcaresystem@gmail.com',
    MAIL_PASSWORD='adhd@123',
))

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

mysql = MySQL(app)
mail = Mail(app)

@app.route('/')
def render_homepage():
    resetValues()
    return render_template('home.html')

@app.route('/fmri_predict')
def render_fmripage():
    resetValues()
    return render_template('health_info.html')

@app.route('/em_predict')
def render_empage():
    resetValues()
    return render_template('health_info_em.html')

@app.route('/report')
def render_reportpage():
    return render_template('report.html')

@app.route("/predict", methods=['GET', 'POST'])
def predict():
    resetValues()
    data = {'success': False}

    params = request.json
    if(params == None):
        params = request.args
    print(params)
    adhd = getPrediction()
    nadhd = 1-adhd

    if(params != None):
        data['adhd'] = str(adhd)
        data['nadhd'] = str(nadhd)
        data['success'] = True
    return jsonify(data)

@app.route("/status", methods=['GET', 'POST'])
def get_status():
    global fmri_status, preproc_status, fex_status
    status_data = {'data': fmri_status,
                   'preproc': preproc_status, 'fex': fex_status}
    return jsonify(status_data)

@app.route("/em_status", methods=['GET', 'POST'])
def get_em_status():
    global em_status
    if 'em_status' not in session:
        session['em_status']=0
    print("em_status", session['em_status'])
    status_data = {'data': em_status}
    return jsonify(status_data)

@app.route("/fmri_preview", methods=['GET', 'POST'])
def get_fmri_preview():
    data={"image":""}

    x_size = 64
    y_size = 64
    n_slice = 64
    n_volumes = 96

    if request.method == 'POST':
        f= request.files['file']
        nii_file = os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
        f.save(nii_file)
        mean_haxby = mean_img(nii_file)

        plot_epi(mean_haxby,output_file="static/img/viz.png")

        data = {'image': "static/img/viz.png"}
    return jsonify(data)
    
@app.route("/em_preview" , methods=['GET', 'POST'])
def get_em_preview():
    global dataset
    if request.method == 'POST':
        dataset = tablib.Dataset()
        f = request.files['file']
        em_file = os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
        df=pd.read_csv(em_file)
        dataset=df.head(10)
    
    data = dataset.to_html()
    print(data)
    dt={'table':data}
    #return dataset.html
    return jsonify(dt)
    
@app.route("/fmri_uploader", methods=['GET', 'POST'])
def upload_fmri_file():
    global nii_file, fmri_status, preproc_status
    resetValues()
    preproc_status = 5
    if request.method == 'POST':
        print(request.form)
        f = request.files['file']
        nii_file = os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
        f.save(nii_file)
        flash('file uploaded suceessfully')
        preproc_status = 10
        data = {'success': False}

        params = request.json
        if(params == None):
            params = request.args
        adhd = getFMRIPrediction()
        nadhd = 1-adhd
        fmri_status = 85

        if(params != None):
            data['adhd'] = str(adhd)
            data['nadhd'] = str(nadhd)
            data['success'] = True

        if (adhd > nadhd):
            diag = 'ADHD'
            score = adhd
        else:
            diag = 'Non-ADHD'
            score = nadhd
        fmri_status = 100
        print(score)
        r = request.form
        if session.get('email'):
            user = session['email']
        else:
            user = "Guest"
        storeData(r['fname'], r['lname'], r['email'], int(
            r['age']), diag, score, 'fmri', user, r['symptoms'],r['chronic'])

        time.sleep(1)
        # return jsonify(data)

        return redirect('/report')

@app.route("/send_mail", methods=['GET', 'POST'])
def index():
    r = request.form
    fname = r['fname']
    lname = r['lname']
    to = r['to']
    subject = r['subject']
    body = r['body']
    sender = r['from']

    msg = Message(subject, sender=sender, recipients=[to])
    msg.body = body

    mail.send(msg)
    rst = {'result': True}
    return jsonify(rst)

@app.route("/get_data", methods=['GET', 'POST'])
def getData():
    r = request.form
    fname = r['fname']
    lname = r['lname']
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM Diagnosis where Patient_first_name = %s && Patient_last_name =%s ORDER BY Patient_id DESC LIMIT 1", (fname, lname))
    row = cur.fetchone()
    data = {}
    if len(row) > 0:
        data['Patient_id'] = row[0]
        data['Patient_first_name'] = row[1]
        data['Patient_last_name'] = row[2]
        data['Email'] = row[3]
        data['Age'] = str(row[4])
        data['Diagnosis'] = row[5]
        data['Composite_Score'] = str(row[6])
        data['Symptoms'] = row[9]
        data['ChronicDisease'] = row[12]

    print(data)
    cur.close()
    return jsonify(data)

@app.route("/get_patient_data", methods=['GET', 'POST'])
def get_patient_data():
    cid = request.args.get('uid')
    cur = mysql.connection.cursor()
    if cid != None:
        cur.execute("SELECT * FROM Diagnosis where Patient_id = %s", [cid])
        row = cur.fetchone()
        data = {}
        if row != None:
            if len(row) > 0:
                data['Patient_first_name'] = row[1]
                data['Patient_last_name'] = row[2]
                data['Email'] = row[3]
                data['Age'] = str(row[4])
                data['Symptoms'] = row[9]
                data['Chronic'] = row[12]
                print(data)
                cur.close()
                return jsonify(data)
            else:
                return "Invalid pateint ID"
        else:
            return "Error"
    else:
        return "Error"

@app.route("/em_uploader", methods=['GET', 'POST'])
def upload_em_file():
    global csv_file, em_status
    if request.method == 'POST':
        f = request.files['file']
        csv_file = os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
        f.save(csv_file)
        flash('file uploaded suceessfully')

        session['em_status'] = 10
        em_status = 10

        data = {'success': False}

        params = request.json
        if(params == None):
            params = request.args
        print(params)

        time.sleep(1)
        session['em_status'] = 40
        em_status = 40
        adhd = getEyeMovementPrediction()
        nadhd = 1-adhd
        session['em_status'] = 60
        em_status = 60

        if(params != None):
            data['adhd'] = str(adhd)
            data['nadhd'] = str(nadhd)
            data['success'] = True

        if (adhd > nadhd):
            diag = 'ADHD'
            score = adhd
        else:
            diag = 'Non-ADHD'
            score = nadhd

        print(score)
        time.sleep(1)
        session['em_status'] = 80
        em_status = 80

        r = request.form

        if session.get('email'):
            user = session['email']
        else:
            user = "Guest"
        
        storeData(r['fname'], r['lname'], r['email'], int(r['age']), diag, score, 'EM', user, r['symptoms'],r['chronic'])
        
        session['em_status'] = 100
        em_status = 100
        time.sleep(1)

        return redirect('/report')
    
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        if session.get('name') is not None:
            if session['name'] != '' and session['email'] != '':
                return redirect('/account')
        else:
            return render_template("login.html")
    else:
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO User (first_name,last_name, Email, psw) VALUES (%s,%s,%s,%s)",
                    (fname, lname, email, password,))
        mysql.connection.commit()
        session['name'] = request.form['fname']+request.form['lname']
        session['email'] = request.form['email']
        return render_template("register_success.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        curl = mysql.connection.cursor()
        curl.execute("SELECT * FROM User WHERE Email=%s", (email,))
        user = curl.fetchone()
        curl.close()

        if len(user) > 0:
            if password == user[3]:
                session['name'] = user[1]+user[2]
                session['email'] = user[0]
                return redirect("/account")
            else:
                return render_template('login.html',message="Error password and email not match")
        else:
            return render_template('login.html',message="Error user not found")
    else:
        if session['name'] != '' and session['email'] != '':
            return redirect('/account')
        else:
            return render_template("login.html")

@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/")

@app.route('/account', methods=["GET", "POST"])
def account():
    if session['name'] != '' and session['email'] != '':
        print('Session started ....')
        email = session['email']
        curl = mysql.connection.cursor()
        curl.execute(
            "SELECT * FROM Diagnosis inner join User ON Diagnosis.User = User.Email WHERE Diagnosis.User=%s", (email,))
        data = curl.fetchall()
        curl.close()
        return render_template('account.html', data=data,len=len(data))
    else:
        return render_template("login.html")


app.run(host='0.0.0.0', debug=False)
