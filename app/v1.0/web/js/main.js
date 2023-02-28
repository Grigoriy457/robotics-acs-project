var dev = false;

var update_com_list_timer;
var last_uid = "";

var min_width = 1000;
var min_height = 711;

window.onresize = function (){
     window.resizeTo(min_width, min_height);
}

function close_program() {
     eel.close_program_py()();
     console.log("closed!");
     window.close();
}

function on_start() {
     cabinets_div.style.display = "none";
     eel.get_cabinets()(function(ret) {
          for (var i = 0; ret.length > i; i++) {
               let newOption = new Option(ret[i], ret[i]);
               cabinets_select.append(newOption);
          }
     });
     check()
}


function change_display(id, value) {
     document.getElementById(id).style.display = value;
}
eel.expose(change_display);


function display_uid(ret) {
     if (ret == "error") {
          show_hide_dialog("0");
          return "clear";
     } else {
          if (typeof(ret) == "string") {
               if (ret == "1") {
                    return;
               } else if (ret == "0") {
                    document.getElementById("name").value = "";
                    cabinets_select.value = "";
                    type.value = "";
                    uid.innerHTML = "";
                    document.getElementsByClassName("upload_button")[0].textContent = "Добавить";

                    user_type_changed();
               }
          } else if (typeof(ret) == "object") {
               document.getElementById("name").value = ret[0];
               cabinets_select.value = ret[1];
               type.value = ret[2];
               uid.innerHTML = ret[3];
               if (ret[0] != "") {
                    document.getElementsByClassName("upload_button")[0].textContent = "Обновить";
               } else {
                    document.getElementsByClassName("upload_button")[0].textContent = "Добавить";
               }

               user_type_changed();
          }
     }
}
eel.expose(display_uid);


function hide_dialog() {
     document.getElementById("message").style.opacity = 0;
     document.getElementById("page").style.backgroundColor = "#4565FF";
     document.getElementById('data').style.display = "block";
     document.getElementById("check_button").disabled = 1;
}


function show_dialog() {
     document.getElementById("message").style.opacity = 1;
     document.getElementById("page").style.backgroundColor = "#454545";
     if (!dev) {
          document.getElementById('data').style.display = "none";
     }
     document.getElementById("check_button").disabled = 0;
}


function show_hide_dialog(ret) {
     if (ret == "0") {
          show_dialog();
          update_com_list_timer = setInterval(update_com_list, 500);
     } else {
          hide_dialog();
     }
}
eel.expose(show_hide_dialog);


async function update_com_list() {
     data = await eel.get_com_list()();

     var com_list = data[0];
     var ret = data[1];

     if (ret == "0") {
          clearInterval(update_com_list_timer);
          return
     }

     now_select = ports_list.options[ports_list.selectedIndex].text;

     ports_list.options.length = 0;

     let newOption = new Option("Выберите COM порт");
     ports_list.append(newOption);

     if (com_list.length != 0) {
          for (var i = 0; com_list.length > i; i++) {
               let newOption = new Option(com_list[i][1], com_list[i][0]);
               ports_list.append(newOption);
               if (now_select == com_list[i][1]) {
                    newOption.selected = true;
               } else {
                    newOption.selected = false;
               }
          }
     }
}


async function check() {
     document.getElementById("message").style.opacity = 0;
     document.getElementById("check_button").disabled = 1;
     if (!dev) {
          document.getElementById('data').style.display = "none";
     }

     now_port = ports_list.options[ports_list.selectedIndex].value;

     ret = await eel.check_port(now_port)();

     show_hide_dialog(ret);
     if (ret == "1") {
          console.log("start_click from js");
          eel.start_click(now_port);
     }
}

function add_user_js() {
     console.log("press");
     var fio = document.getElementById("name").value;
     var _type = document.getElementById("type").value;
     var cabinet = cabinets_select.options[cabinets_select.selectedIndex].value;

     eel.add_user(fio, cabinet, _type, uid.innerHTML)(function(ret){
          if (ret != "1") {
               new Toast({
                    title: false,
                    text: ret,
                    theme: 'danger',
                    autohide: true,
                    interval: 5000
               });
          } else {
               last_uid = uid.innerHTML;
               document.getElementsByClassName("upload_button")[0].textContent = "Обновить";
               new Toast({
                    title: false,
                    text: "Информация успешно сохранена!",
                    theme: 'success',
                    autohide: true,
                    interval: 5000
               });
          }
     });
}

function user_type_changed() {
     if (type.value.includes("Ученик")) {
          cabinets_div.style.display = "block";
     } else {
          cabinets_div.style.display = "none";
          cabinets_select.options[0].selected = true;
     }
}