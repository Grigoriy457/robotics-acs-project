var user_type = null;

var script = document.createElement('script');
script.src = 'https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js'; // Check https://jquery.com/ for the current version
document.getElementsByTagName('head')[0].appendChild(script);

function update_timezone() {
  var zone = moment.tz.guess();
  fetch('/api/update_user_timezone/' + zone + "/", {
    method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      console.log("Server:", data);
    })
    .catch(error => {
      console.error(error)
    })
}

var stringToHTML = function (str) {
	var parser = new DOMParser();
	var doc = parser.parseFromString(str, 'text/html');
	return doc.body;
};

function show_entry_exits(c, i) {
  if (is_logged_in == 1) {
    if (is_shown) {
      document.getElementById("right-nav").classList.remove("show");
      is_shown = false;
      return;
    }

    var index = i[0]["index"];
    var date_history = entrys_exits_history[entrys_exits_labels[index]];

    document.getElementById("date-in-title").textContent = entrys_exits_labels[index];

    if (window.innerWidth < 600) {
      document.getElementById("history-thead").innerHTML = "<tr><th>Time</th><th></th><th>Name</th></tr>"
    } else if (window.innerWidth < 700) {
        document.getElementById("history-thead").innerHTML = "<tr><th>Time</th><th><th>User type</th></th><th>Name</th></tr>"
    } else if (window.innerWidth < 900) {
      document.getElementById("history-thead").innerHTML = "<tr><th>Time</th><th></th><th>User type</th><th>Class</th><th>Name</th></tr>"
    } else {
      document.getElementById("history-thead").innerHTML = "<tr><th>Time</th><th></th><th>UID</th><th>User type</th><th>Class</th><th>Name</th></tr>"
    }

    var innerHTML = "";
    for (var i = 0; i < date_history.length; i++) {
      innerHTML += "<tr>";
      for (var j = 0; j < date_history[i].length; j++) {
        innerHTML += "<td>";
        if (j == 1) {
          if (date_history[i][j] == "entry") {
            innerHTML += '<img src="/static/img/entry.svg" alt="entry">';
          } else {
            innerHTML += '<img src="/static/img/exit.svg" alt="exit">';
          }
        } else if (j == 2 && window.innerWidth < 900) {
          innerHTML = innerHTML.slice(0, innerHTML.length - 4);
          continue;
        } else if (j == 4 && window.innerWidth < 700) {
            innerHTML = innerHTML.slice(0, innerHTML.length - 4);
            continue;
        } else if (j == 3 && window.innerWidth < 600) {
            innerHTML = innerHTML.slice(0, innerHTML.length - 4);
            continue;
        } else {
          innerHTML += date_history[i][j];
        }
        innerHTML += "</td>";
      }
      innerHTML += "</tr>";
    }
    document.getElementById("history-tbody").innerHTML = innerHTML;
    hide_body_overflow();
    document.getElementById("card-body").scrollTo(pageXOffset, 0);
    document.getElementById("right-nav").classList.add("show");
  }
}

function hide_body_overflow() {
  document.getElementsByTagName("body")[0].style.overflow = "hidden";
}

function show_body_overflow() {
  document.getElementsByTagName("body")[0].style.overflow = "auto";
}

function copyText(text, msg_text) {
  const element = document.createElement('textarea');

  element.value = text;
  element.setAttribute('readonly', '');
  element.style.position = 'absolute';
  element.style.left = '-9999px';

  document.body.appendChild(element);
  element.select();
  document.execCommand('copy');
  document.body.removeChild(element);

  alert(msg_text + " was copied!");
}

function saveUserData() {
  var sendRequest = true;

  login = document.getElementById("login-input").value.trim();
  if (login == "") {sendRequest = false; wrongInput(document.getElementById("login-input")); document.getElementById("login-input").value = ""} else {document.getElementById("login-input").style.border = ""}

  password = document.getElementById("password-input").value.trim();
  if (password == "") {sendRequest = false; wrongInput(document.getElementById("password-input")); document.getElementById("password-input").value = ""} else {document.getElementById("password-input").style.border = ""}

  first_name = document.getElementById("first_name-input").value.trim();
  if (first_name == "") {sendRequest = false; wrongInput(document.getElementById("first_name-input")); document.getElementById("first_name-input").value = ""} else {document.getElementById("first_name-input").style.border = ""}

  last_name = document.getElementById("last_name-input").value.trim();
  if (last_name == "") {sendRequest = false; wrongInput(document.getElementById("last_name-input")); document.getElementById("last_name-input").value = ""} else {document.getElementById("last_name-input").style.border = ""}

  middle_name = document.getElementById("middle_name-input").value.trim();
  if (middle_name == "") {sendRequest = false; wrongInput(document.getElementById("middle_name-input")); document.getElementById("middle_name-input").value = ""} else {document.getElementById("middle_name-input").style.border = ""}

  mail = document.getElementById("mail-input").value.trim();
  if (mail == "") {sendRequest = false; wrongInput(document.getElementById("mail-input")); document.getElementById("mail-input").value = ""} else {document.getElementById("mail-input").style.border = ""}

  phone = document.getElementById("phone-input").value.trim();
  if (phone != "") {phone = "%2b" + phone.slice(1)}
  document.getElementById("phone-input").style.border = ""

  if (sendRequest) {
    document.getElementById("save-btn").disabled = true;

    fetch(`/saveUserData/?user_id=${user_id}&login=${login}&password=${password}&first_name=${first_name}&last_name=${last_name}&middle_name=${middle_name}&mail=${mail}&phone=${phone}`, {
      method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
      if (data.is_ok) {
        document.getElementById("user_card_title").textContent = `${first_name} ${last_name}`;
      } else {
        if (data.is_wrong_login) {
          console.log("Login is invalid!");
          wrongInput(document.getElementById("login-input"));
        }
        if (data.is_mail_invalid) {
          console.log("Mail is invalid!");
          wrongInput(document.getElementById("mail-input"));
        }
        if (data.is_wrong_phone) {
          console.log("Wrong phone!");
          wrongInput(document.getElementById("phone-input"));
        }
      }
      document.getElementById("save-btn").disabled = false;
    })
    .catch(error => {
      console.error(error);
      document.getElementById("save-btn").disabled = false;
    })
  }
}

function createNewUser() {
  var sendRequest = true;

  login = document.getElementById("login-input").value.trim();
  if (login == "") {sendRequest = false; wrongInput(document.getElementById("login-input")); document.getElementById("login-input").value = ""} else {document.getElementById("login-input").style.border = ""}

  password = document.getElementById("password-input").value.trim();
  if (password == "") {sendRequest = false; wrongInput(document.getElementById("password-input")); document.getElementById("password-input").value = ""} else {document.getElementById("password-input").style.border = ""}

  first_name = document.getElementById("first_name-input").value.trim();
  if (first_name == "") {sendRequest = false; wrongInput(document.getElementById("first_name-input")); document.getElementById("first_name-input").value = ""} else {document.getElementById("first_name-input").style.border = ""}

  last_name = document.getElementById("last_name-input").value.trim();
  if (last_name == "") {sendRequest = false; wrongInput(document.getElementById("last_name-input")); document.getElementById("last_name-input").value = ""} else {document.getElementById("last_name-input").style.border = ""}

  middle_name = document.getElementById("middle_name-input").value.trim();
  if (middle_name == "") {sendRequest = false; wrongInput(document.getElementById("middle_name-input")); document.getElementById("middle_name-input").value = ""} else {document.getElementById("middle_name-input").style.border = ""}

  mail = document.getElementById("mail-input").value.trim();
  if (mail == "") {sendRequest = false; wrongInput(document.getElementById("mail-input")); document.getElementById("mail-input").value = ""} else {document.getElementById("mail-input").style.border = ""}

  phone = document.getElementById("phone-input").value.trim();
  if (phone != "") {phone = "%2b" + phone.slice(1)}
  document.getElementById("phone-input").style.border = ""

  if (sendRequest) {
    document.getElementById("save-btn").disabled = true;

    fetch(`/addNewUserData/?user_type=${user_type}&user_id=${user_id}&login=${login}&password=${password}&first_name=${first_name}&last_name=${last_name}&middle_name=${middle_name}&mail=${mail}&phone=${phone}`, {
      method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
      if (data.is_ok) {
        window.location = "/profile/" + String(data.user_id)
      } else {
        if (data.is_wrong_login) {
          console.log("Login is invalid!");
          wrongInput(document.getElementById("login-input"));
        }
        if (data.is_mail_invalid) {
          console.log("Mail is invalid!");
          wrongInput(document.getElementById("mail-input"));
        }
        if (data.is_wrong_phone) {
          console.log("Wrong phone!");
          wrongInput(document.getElementById("phone-input"));
        }
      }
      document.getElementById("save-btn").disabled = false;
    })
    .catch(error => {
      console.error(error);
      document.getElementById("save-btn").disabled = false;
    })
  }
}

function show_password() {
  document.getElementById("show-password-btn").style.display = "none";
  document.getElementById("hide-password-btn").style.display = "block";
  document.getElementById("password-input").type = "text";
}

function hide_password() {
  document.getElementById("show-password-btn").style.display = "block";
  document.getElementById("hide-password-btn").style.display = "none";
  document.getElementById("password-input").type = "password";
}

function removeUserAvatar() {
  var request = new XMLHttpRequest();
  request.open('POST', window.location.origin + "/removeUserAvatar/");
  request.onload = function() {
    if (request.status == 200) {
      document.getElementById("user-avatar").src = default_user_avatar;
      document.getElementById("user-avatar").srcset = default_user_avatar;
      document.getElementById("remove-user-avatar").style.display = "none";
    } else {
      console.warn("Status code: " + String(request.status));
    }
  }
  request.onerror = function(error){
    console.log(error);
  }
  request.send();
}

function wrongInput(object) {
  object.style.border = "1px solid #ed3838";
  object.animate(
    [
      {transform: 'translate(1px, 1px) rotate(0deg)'},
      {transform: 'translate(-1px, -2px) rotate(-1deg)'},
      {transform: 'translate(-3px, 0px) rotate(1deg)'},
      {transform: 'translate(3px, 2px) rotate(0deg)'},
      {transform: 'translate(1px, -1px) rotate(1deg)'},
      {transform: 'translate(-1px, 2px) rotate(-1deg)'},
      {transform: 'translate(-3px, 1px) rotate(0deg)'},
      {transform: 'translate(3px, 1px) rotate(-1deg)'},
      {transform: 'translate(-1px, -1px) rotate(1deg)'},
      {transform: 'translate(1px, 2px) rotate(0deg)'},
      {transform: 'translate(1px, -2px) rotate(-1deg)'},
    ],
    {
      duration: 250,
      iterations: 2,
    }
  );
}

function verifyCode() {
  token = document.getElementById("token").value;
  code = document.getElementById("confirmation-code").value;

  document.getElementById("check-btn").disabled = true;

  var request = new XMLHttpRequest();
  request.open('POST', window.location.origin + "/verifyCode/?token=" + token + "&code=" + code);
  request.onload = function() {
    if (request.status == 200) {
      if (request.responseText == "1") {
        document.getElementById("flexCheckDefault").disabled = true;
        document.getElementById("2fa-container-disabled").style.display = "none";
        document.getElementById("2fa-container-enabled").style.display = "block";
      } else {
        wrongInput(document.getElementById("confirmation-code"));
      }
    } else {
      console.warn("Status code: " + String(request.status));
    }
    document.getElementById("check-btn").disabled = false;
  }
  request.onerror = function(error){
    console.log(error);
    wrongInput(document.getElementById("confirmation-code"));
    document.getElementById("check-btn").disabled = false;
  }
  request.send();
}

function submit_function(is_error, need_confirmation_code) {
  if (is_error) {
    if (!need_confirmation_code) {
      wrongInput(document.getElementById("login-input"));
      wrongInput(document.getElementById("password-input"));
    } else {
      wrongInput(document.getElementById("confirmation-code-input"));
    }
  }
}

function disable2FA() {
  token = document.getElementById("token").value;

  document.getElementById("disable-btn").disabled = true;

  var request = new XMLHttpRequest();
  request.open('POST', window.location.origin + "/disable2FA/?token=" + token);
  request.onload = function() {
    if (request.status == 200) {
      document.getElementById("flexCheckDefault").disabled = false;
      document.getElementById("flexCheckDefault").checked = false;
      document.getElementById("2fa-container-disabled").style.display = "none";
      document.getElementById("2fa-container-enabled").style.display = "none";
    } else {
      console.warn("Status code: " + String(request.status));
    }
    document.getElementById("disable-btn").disabled = false;
  }
  request.onerror = function(error){
    console.log(error);
    wrongInput(document.getElementById("confirmation-code"));
    document.getElementById("disable-btn").disabled = false;
  }
  request.send();
}

function formatPhoneNumber(value) {
  if (!value) return value;
  const phoneNumber = value.replace(/[^\d]/g, '');
  const phoneNumberLength = phoneNumber.length;
  if (phoneNumberLength < 2) return "+" + phoneNumber
  if (phoneNumberLength < 4) return "+" + phoneNumber;
  if (phoneNumberLength < 7) {
    return `+${phoneNumber[0]} (${phoneNumber.slice(1, 4)}) ${phoneNumber.slice(4)}`;
  }
  return `+${phoneNumber[0]} (${phoneNumber.slice(1, 4)}) ${phoneNumber.slice(4, 7)}-${phoneNumber.slice(7, 9)} ${phoneNumber.slice(9, 11)}`;
}

function saveStudentMark(user_id, lesson_id, lesson_date, mark) {
  fetch(`/saveStudentMark/?user_id=${user_id}&lesson_id=${lesson_id}&lesson_date=${lesson_date}&mark=${mark}`, {
      method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      if (data.is_ok) {
        if (document.getElementById("check-btn") != null && (!document.getElementById("check-btn").disabled) && mark != "") {
          onSuccessfull("Student mark sucsessufly updated!");
        } else if (mark != "") {
          onSuccessfull("Student mark sucsessufly updated!");
        }
      } else {
        onError("Error!");
      }
    })
    .catch(error => {
      console.error(error);
      onError(error);
      return -1;
    })
}

function checkStudentsForAbsence(btn, lesson_id, class_id) {
  btn.disabled = true;
  fetch(`/api/check_students_for_absence/${lesson_id}/${class_id}/`, {
    method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      if (data.is_error) {
        onError("Error!");
      } else {
        for (var i = 0; i < data.data.length; i++) {
          console.log(data.data[i]);
          document.getElementById(`mark__${data.day}__${data.data[i].user_id}`).value = ""
          saveStudentMark(data.data[i].user_id, data.data[i].lesson_id, data.data[i].lesson_date, "");
        }
        onSuccessfull("Students are checked sucsessufly!");
      }
    })
    .catch(error => {
      console.error(error);
      onError(error);
    })
  btn.disabled = false;
}

function setCanStudentsLeave(input, lesson_id) {
  input.disabled = true;
  fetch(`/api/set_can_students_leave/${lesson_id}/${Number(input.checked)}/`, {
    method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      if (data.is_error) {
        onError("Error!");
        input.checked = !input.checked;
      } else {
        onSuccessfull("Value updated sucsessufly!");
      }
    })
    .catch(error => {
      console.error(error);
      onError(error);
      input.checked = !input.checked;
    })
  input.disabled = false;
}

function delete_account(btn) {
  btn.disabled = true;
  if (!document.getElementById("confirm-input").checked) {
    onError("You need to turn on the switch confirming that you want to delete this account!", null, 8000);
  } else {
    fetch(`/deleteAccount/${user_id}/${window.location.search}`, {
      method: "POST"
    })
      .then(response => response.json())
      .then(data => {
        if (data.is_ok) {
          onSuccessfull("This account will be deleted! (you will be redirected automaticly)");
          setTimeout(function() {window.location = data.redirect_to}, redirect_time);
        }
      })
      .catch(error => {
        console.error(error);
        onError(error);
      })
  }
  btn.disabled = false;
}

function onError(text, status_code=null, interval=5000) {
  if (text != "") {
    new Toast({
      title: false,
      text: text,
      theme: 'danger',
      autohide: true,
      interval: interval
    });
  } else if (status_code != null) {
    new Toast({
      title: false,
      text: text,
      theme: `Connection error (status code - ${status_code})!`,
      autohide: true,
      interval: interval
    });
  } else {
    new Toast({
      title: false,
      text: "Connection error!",
      theme: 'danger',
      autohide: true,
      interval: interval
    });
  }
}

function onSuccessfull(message) {
  console.log(message);
  new Toast({
      title: false,
      text: message,
      theme: 'success',
      autohide: true,
      interval: 5000
  });
}