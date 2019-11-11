/**
 * Created by User on 9/8/2019.
 */
console.log('called main.js')
var fmri_formdata;
var eye_movement_formdata;
var newuser;

console.log('called setfMRI data');

$(window).on('load', function () {
    console.log('on load')
    $('#checkRegModal').modal('show');
});

function setfMRIData() {
    console.log('called setfMRI data');
    const element = document.getElementById('frmi_data_file');
    fmri_formdata = new FormData();
    if ($(element).prop('files').length > 0) {
        file = $(element).prop('files')[0];
        fmri_formdata.append("file", file);
    }
    console.log(fmri_formdata);

    document.getElementById('upload_file_name').innerText= fmri_formdata.get('file').name

    if (fmri_formdata.get("file") != null) {
        $.ajax({
            url: '/fmri_preview',
            type: 'POST',
            data: fmri_formdata,
            processData: false,
            contentType: false,
            beforeSend: function () {
                var d = document.getElementById('fmri_preview')
                d.setAttribute("src", "static/img/loading.gif");
            },
            success: function (res) {
                console.log(res)
                var d = document.getElementById('fmri_preview')
                d.setAttribute("src", "static/img/viz.png");
                // $('fmri_preview').attr("src", "static/img/viz.png");
                console.log('***done calling')
                $("#doneBtn").click(function() {
                    $('#fmriUploadModal').modal('hide');
                })
            },
        });
    }
}

function setEMData() {
    console.log('called setfMRI data');
    const element = document.getElementById('em_data_file');
    fmri_formdata = new FormData();
    if ($(element).prop('files').length > 0) {
        file = $(element).prop('files')[0];
        fmri_formdata.append("file", file);
    }
    console.log(fmri_formdata);

    document.getElementById('upload_file_name').innerText= fmri_formdata.get('file').name

    if (fmri_formdata.get("file") != null) {
        $.ajax({
            url: '/em_preview',
            type: 'POST',
            data: fmri_formdata,
            processData: false,
            contentType: false,
            success: function (res) {
                console.log(res)
                // console.log('***done calling')
                document.getElementById('dtable').innerHTML=res.table
                $("#doneBtn").click(function() {
                    $('#emUploadModal').modal('hide');
                })
            },
        });
    }
}

function resetUploadFile() {
    fmri_formdata.delete("file");
}

function upload_fmri() {
    $('#fmriUploadModal').modal('show');
}

function uploadEyeData() {
    $('#emUploadModal').modal('show');
}
function previewTable() {
    $('#viewTableModal').modal('show');
}

$("#checkform").submit(function (e) {
    e.preventDefault();
});

$("#eyeForm").submit(function (e) {
    e.preventDefault();
});

$("#contactForm").submit(function (e) {
    e.preventDefault();
});

$("#homeContactForm").submit(function (e) {
    e.preventDefault();
});

function fmri_predict_value() {
    // $('#fmri_loading_image').show();
    // $('#fmri_predict_button ').enable(false);

    var isValidForm = document.forms['checkform'].checkValidity();

    if (isValidForm) {
        $('#pre_prog').show();
        $('#fex_prog').show();
        $('#prog').show();

        if (fmri_formdata.get("file") != null) {
            setData();
            console.log(fmri_formdata);
            preproc_progress.setAttribute("style", `width: 2%`);
            $.ajax({
                url: '/fmri_uploader',
                type: 'POST',
                data: fmri_formdata,
                processData: false,
                contentType: false,
                success: function (res) {
                    //console.log(res);
                    window.location.href = "http://adhdclassification.projects.uom.lk:5000/report";
                }
            });
        } else {
            alert("Please upload a valid data file to test")
        }

    }
}

function EM_predict_value() {
    // $('#fmri_loading_image').show();
    // $('#fmri_predict_button ').enable(false);

    var isValidEyeForm = document.forms['eyeForm'].checkValidity();
    if (isValidEyeForm) {
        $('#prog').show();
        setData();
        console.log(fmri_formdata);
        $.ajax({
            url: '/em_uploader',
            type: 'POST',
            data: fmri_formdata,
            processData: false,
            contentType: false,
            success: function (res) {
                // console.log(res);
                window.location.href = "http://adhdclassification.projects.uom.lk:5000/report";
            }
        });
    }

}

function setData() {
    const fname = document.getElementById('c_fname').value;
    const lname = document.getElementById('c_lname').value;
    const age = document.getElementById('c_age').value;
    const email = document.getElementById('c_email').value;
    const symptoms = document.getElementById('c_symptoms').value;
    const chronic = document.getElementById('c_chronic').value;

    fmri_formdata.append("fname", fname);
    fmri_formdata.append("lname", lname);
    fmri_formdata.append("age", age);
    fmri_formdata.append("email", email);
    fmri_formdata.append("symptoms", symptoms);
    fmri_formdata.append("chronic", chronic);

    localStorage.setItem("fname", fname);
    localStorage.setItem("lname", lname);
}

function eye_movement_predict_value() {
    $('#eye_movement_loading_image').show();
    console.log(fmri_formdata);
    $.ajax({
        url: '/em_uploader',
        type: 'POST',
        data: fmri_formdata,
        processData: false,
        contentType: false,
        success: function (res) {
            console.log(res);
            document.getElementById('eye_movement_adhd_val').innerHTML += res.adhd;
            document.getElementById('eye_movement_nadhd_val').innerHTML += res.nadhd;
        },
        complete: function () {
            $('#eye_movement_loading_image').hide();
        },

    });
}

function search_data() {
    var input, filter, ul, li, a, i, txtValue, found;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    console.log(filter)
    ul = document.getElementById("dtable");
    rs = ul.getElementsByClassName("table-row");
    for (i = 0; i < rs.length; i++) {
        tds = rs[i].getElementsByClassName("country");
        found = false;
        for (j = 0; j < tds.length; j++) {
            txtValue = tds[j].innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                console.log('found...')
                found = true;
            }
        }
        console.log(i + " " + found)
        if (found) {
            rs[i].style.display = "";
        } else {
            rs[i].style.display = "none";
        }
    }
}

margins = {
    top: 70,
    bottom: 40,
    left: 30,
    width: 550
};

function generate_report(first_name, last_name, age, email, symptoms, diagnosis, similarity_score) {
    var pdf = new jsPDF('p', 'pt', 'a4');
    console.log(first_name)
    pdf.setFontSize(45);
    headerFooterFormatting(pdf, pdf.internal.getNumberOfPages());
    pdf.setLineWidth(0.001);
    pdf.line(60, 170, 530, 170); // horizontal line

    pdf.setTextColor(100);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 190, 'First Name');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 190, first_name);         //replace these values with derived data from db

    pdf.line(60, 210, 530, 210);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 230, 'Last Name');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 230, last_name);

    pdf.line(60, 250, 530, 250);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 270, 'Age');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 270, age);

    pdf.line(60, 290, 530, 290);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 310, 'Email');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 310, email);

    pdf.line(60, 330, 530, 330);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 350, 'Symptoms');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 350, symptoms);

    pdf.line(60, 370, 530, 370);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 390, 'ADHD Result');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 390, diagnosis);

    pdf.line(60, 410, 530, 410);

    pdf.setFont("courier");
    pdf.setFontType("bold");
    pdf.text(150, 430, 'Probability of having ADHD');

    pdf.setFont("times");
    //pdf.setFontType("italic");
    pdf.text(330, 430, similarity_score + '%');

    pdf.line(60, 450, 530, 450);
    pdf.save(first_name + "_" + last_name + '_Report.pdf');
}

function headerFooterFormatting(doc, totalPages) {
    for (var i = totalPages; i >= 1; i--) {
        doc.setPage(i);
        //header
        header(doc);
        footer(doc, i, totalPages);
        doc.page++;
    }
}

function header(doc) {
    doc.setFontSize(30);
    doc.setTextColor(40);
    doc.setFontStyle('normal');

    if (true) {
        doc.addImage(base64Img, 'JPEG', 0, 0, 600, 120);
    }

    doc.setLineCap(2);
    doc.line(3, 120, margins.width + 43, 120); // horizontal line
}

function footer(doc, pageNumber, totalPages) {
    var str = "Page " + pageNumber;
    doc.setFontSize(10);
    doc.text(str, margins.left, doc.internal.pageSize.height - 30);
    doc.addImage(imageLogo, 'JPEG', 420, 770, 100, 50);
}

function searchUser() {
    newuser = false

    $('#regUserModal').modal('show');

    document.getElementById('c_fname').disabled = true
    document.getElementById('c_lname').disabled = true
    document.getElementById('c_age').disabled = true
    document.getElementById('c_email').disabled = true;
    document.getElementById('c_symptoms').disabled = true;
    document.getElementById('c_chronic').disabled = true;
    document.getElementById('chkYes').disabled = true;
    document.getElementById('chkNo').disabled = true;

}

function addUser() {
    newuser = true

    document.getElementById('c_fname').disabled = false;
    document.getElementById('c_lname').disabled = false;
    document.getElementById('c_age').disabled = false;
    document.getElementById('c_email').disabled = false;
    document.getElementById('c_symptoms').disabled = false;
    document.getElementById('c_chronic').disabled = false;
    document.getElementById('chkYes').disabled = false;
    document.getElementById('chkNo').disabled = false;
}

function fillUserValues() {
    var uid = document.getElementById('c_id').value
    localStorage.setItem('uid',uid)
    $.get(
        "/get_patient_data", { uid: uid.toString() },
        function (data) {
            if (data != "Error") {
                console.log(data)
                $('#regUserModal').modal('hide');;
                document.getElementById('c_fname').value = data.Patient_first_name;
                document.getElementById('c_lname').value = data.Patient_last_name;
                document.getElementById('c_age').value = data.Age;
                document.getElementById('c_email').value = data.Email;
                document.getElementById('c_symptoms').value = data.Symptoms;
                document.getElementById('c_chronic').value = data.Chronic;
            } else {
                document.getElementById("error_msg").innerHTML = "Please insert a valid patient ID";
            }
        }
    )
}

function showCheckReg() {
    $('#checkRegModal').modal('show');
}

function sendMail() {

    var isValidForm = document.forms['contactForm'].checkValidity();

    if (isValidForm) {
        var msg = document.getElementById('c_fname').value + " " + document.getElementById('c_lname').value + " informs that " + document.getElementById('c_message').value
        var email_formdata = new FormData();
        email_formdata.append("fname", document.getElementById('c_fname').value);
        email_formdata.append("lname", document.getElementById('c_lname').value);
        email_formdata.append("body", msg);
        email_formdata.append("subject", "ADHD-Care Message");
        email_formdata.append("to", "adhdcaresystem@gmail.com");
        email_formdata.append("from", document.getElementById('c_email').value);
        console.log(email_formdata);
        // window.location.href = "../contact.html";

        $.ajax({
            url: '/send_mail',
            type: 'POST',
            data: email_formdata,
            processData: false,
            contentType: false,
            success: function (res) {
                // alert(res)
                document.getElementById('c_fname').innerHTML = ""
                document.getElementById('c_lname').innerHTML = ""
                document.getElementById('c_message').innerHTML = ""
                document.getElementById('c_email').innerHTML = ""
                $('#success').modal('show');
            },
        });
    }
}

function sendHomeContactMail() {

    var isValidForm = document.forms['homeContactForm'].checkValidity();

    if (isValidForm) {
        var msg = document.getElementById('home_cname').value + " informs that " + document.getElementById('home_cmsg').value
        var email_formdata = new FormData();
        email_formdata.append("fname", document.getElementById('home_cname').value);
        email_formdata.append("lname", "");
        email_formdata.append("body", msg);
        email_formdata.append("subject", "ADHD-Care Message");
        email_formdata.append("to", "adhdcaresystem@gmail.com");
        email_formdata.append("from", document.getElementById('home_cemail').value);
        console.log(email_formdata);

        $.ajax({
            url: '/send_mail',
            type: 'POST',
            data: email_formdata,
            processData: false,
            contentType: false,
            success: function (res) {
                alert("Sucessfully sent")
            },
        });
    }
}
