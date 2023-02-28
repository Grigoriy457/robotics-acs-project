// jkanban init

(function() {
    if (document.getElementById("myKanban")) {
      var KanbanTest = new jKanban({
        element: "#myKanban",
        gutter: "10px",
        widthBoard: "450px",
        click: el => {
          let jkanbanInfoModal = document.getElementById("jkanban-info-modal");

          let jkanbanInfoModalTaskId = document.querySelector(
            "#jkanban-info-modal #jkanban-task-id"
          );
          let jkanbanInfoModalTaskTitle = document.querySelector(
            "#jkanban-info-modal #jkanban-task-title"
          );
          let jkanbanInfoModalTaskAssignee = document.querySelector(
            "#jkanban-info-modal #jkanban-task-assignee"
          );
          let jkanbanInfoModalTaskDescription = document.querySelector(
            "#jkanban-info-modal #jkanban-task-description"
          );

          let taskId = el.getAttribute("data-eid");
          let taskTitle = el.querySelector('p.text').innerHTML;
          let taskAssignee = el.getAttribute("data-assignee");
          let taskDescription = el.getAttribute("data-description");

          jkanbanInfoModalTaskId.value = taskId;
          jkanbanInfoModalTaskTitle.value = taskTitle;
          jkanbanInfoModalTaskAssignee.value = taskAssignee;
          jkanbanInfoModalTaskDescription.value = taskDescription;
        },
        buttonClick: function(el, boardId) {
          if (
            document.querySelector("[data-id='" + boardId + "'] .itemform") ===
            null
          ) {
            // create a form to enter element
            var formItem = document.createElement("form");
            formItem.setAttribute("class", "itemform");
            formItem.innerHTML = `<div class="mb-4">
              <textarea class="min-h-unset box-border focus:shadow-primary-outline text-sm leading-5.6 ease block w-full appearance-none rounded-lg border border-solid border-gray-300 bg-white bg-clip-padding px-3 py-2 font-normal text-gray-700 outline-none transition-all placeholder:text-gray-500 focus:border-blue-500 focus:outline-none" rows="2" autofocus></textarea>
              </div>
              <div class="box-border mb-4">
                  <button type="submit" class="inline-block px-8 py-2 m-0 text-xs font-bold text-center text-white uppercase align-middle transition-all border-0 rounded-lg cursor-pointer ease-in leading-pro tracking-tight-rem bg-gradient-to-tl from-emerald-500 to-teal-400 shadow-md bg-150 bg-x-25 hover:scale-102 active:opacity-85">Add</button>
                  <button type="button" id="kanban-cancel-item" class="inline-block px-8 py-2 m-0 text-xs font-bold text-center text-white uppercase align-middle transition-all border-0 rounded-lg cursor-pointer ease-in leading-pro tracking-tight-rem bg-gradient-to-tl from-red-600 to-orange-600 shadow-md bg-150 bg-x-25 hover:scale-102 active:opacity-85 mr-2 float-right">Cancel</button>
              </div>`;

            KanbanTest.addForm(boardId, formItem);
            formItem.addEventListener("submit", function(e) {
              e.preventDefault();
              var text = e.target[0].value;
              let newTaskId =
                "_" + text.toLowerCase().replace(/ /g, "_") + boardId;
              KanbanTest.addElement(boardId, {
                id: newTaskId,
                title: text,
                class: ["rounded-lg"]
              });
              formItem.parentNode.removeChild(formItem);
            });
            document.getElementById("kanban-cancel-item").onclick = function() {
              formItem.parentNode.removeChild(formItem);
            };
          }
        },
        addItemButton: true,
        boards: [{
            id: "_backlog",
            title: "Backlog",
            item: [{
                id: "_task_1_title_id",
                title: '<p class="text mb-0" data-target="#jkanban-info-modal" data-toggle="modal">Click me to change title</p>',
                class: ["rounded-lg"]
              },
              {
                id: "_task_2_title_id",
                title: '<p class="text mb-0">Drag me to "In progress" section</p>',
                class: ["rounded-lg"]
              },
              {
                id: "_task_do_something_id",
                title: '<img src="../../static/img/office-dark.jpg" class="w-full"><span class="mt-4 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-blue-500 to-violet-500">Pending</span><p class="text mt-2">Website Design: New cards for blog section and profile details</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm leadint-tight"></i><span class="text-sm leading-tight">3</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-1.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Audrey Love"><img alt="Image placeholder" src="../../static/img/team-2.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Michael Lewis"><img alt="Image placeholder" src="../../static/img/team-3.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              },
            ]
          },
          {
            id: "_progress",
            title: "In progress",
            item: [{
                id: "_task_3_title_id",
                title: '<span class="mt-2 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-orange-500 to-yellow-500">Errors</span><p class="text mt-2">Fix Firefox errors</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">11</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jana Lucie"><img alt="Image placeholder" src="../../static/img/team-3.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-2.jpg" class="w-full !rounded-circle"></a></div></div>',
                class: ["rounded-lg"]
              },
              {
                id: "_task_4_title_id",
                title: '<span class="mt-2 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-blue-700 to-cyan-500">Updates</span><p class="text mt-2">Argon Dashboard PRO - Angular 11</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">3</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jana Lucie"><img alt="Image placeholder" src="../../static/img/team-5.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-4.jpg" class="w-full !rounded-circle"></a></div></div>',
                class: ["rounded-lg"]
              },
              {
                id: "_task_do_something_4_id",
                title: '<img src="../../static/img/meeting.jpg" class="w-full"><span class="mt-3 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-blue-700 to-cyan-500">Updates</span><p class="text mt-2">Vue 3 Updates</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">9</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-1.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Audrey Love"><img alt="Image placeholder" src="../../static/img/team-2.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Michael Lewis"><img alt="Image placeholder" src="../../static/img/team-4.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              }
            ]

          },
          {
            id: "_working",
            title: "In review",
            item: [{
                id: "_task_do_something_2_id",
                title: '<span class="mt-2 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-orange-500 to-yellow-500">In Testing</span><p class="text mt-2">Responsive Changes</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">11</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jana Lucie"><img alt="Image placeholder" src="../../static/img/team-3.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-2.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              },
              {
                id: "_task_run_id",
                title: '<span class="mt-2 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-emerald-500 to-teal-400">In review</span><p class="text mt-2 mb-1">Change images dimension</p><div class="flex-1-0"><div class="h-0.75 text-xs flex overflow-visible rounded-lg bg-gray-200 mb-4 "><div class="transition-width duration-600 ease rounded-1 -mt-0.4 -ml-px flex h-1.5 flex-col justify-center overflow-hidden whitespace-nowrap bg-lime-500 text-center text-white " role="progressbar" aria-valuenow="80" aria-valuemin="0" aria-valuemax="100" style="width: 80%;"></div></div></div><div class="flex"><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-3.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              },
              {
                id: "_task_do_something_3_id",
                title: '<span class="mt-2 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-blue-700 to-cyan-500">In Review</span><p class="text mt-2 mb-1">Update Links</p><div class="flex-1-0"><div class="h-0.75 text-xs flex overflow-visible rounded-lg bg-gray-200 mb-4 "><div class="transition-width duration-600 ease rounded-1 -mt-0.4 -ml-px flex h-1.5 flex-col justify-center overflow-hidden whitespace-nowrap bg-cyan-500 text-center text-white " role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100" style="width: 60%;"></div></div></div><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">6</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jana Lucie"><img alt="Image placeholder" src="../../static/img/team-5.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Mike Alis"><img alt="Image placeholder" src="../../static/img/team-1.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              }
            ]
          },
          {
            id: "_done",
            title: "Done",
            item: [{
                id: "_task_all_right_id",
                title: '<img src="../../static/img/home-decor-1.jpg" class="w-full"><span class="mt-3 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-emerald-500 to-teal-400">Done</span><p class="text mt-2">Redesign for the home page</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">8</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Jessica Rowland"><img alt="Image placeholder" src="../../static/img/team-5.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Audrey Love"><img alt="Image placeholder" src="../../static/img/team-1.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Michael Lewis"><img alt="Image placeholder" src="../../static/img/team-4.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              },
              {
                id: "_task_ok_id",
                title: '<span class="mt-2 py-1.8 px-3 text-xxs rounded-1 inline-block whitespace-nowrap text-center align-baseline font-bold uppercase leading-none text-white bg-gradient-to-tl from-emerald-500 to-teal-400">Done</span><p class="text mt-2">Schedule winter campaign</p><div class="flex"><div> <i class="fa fa-paperclip mr-1 text-sm"></i><span class="text-sm">2</span></div><div class="ml-auto"><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Michael Laurence"><img alt="Image placeholder" src="../../static/img/team-1.jpg" class="w-full !rounded-circle"></a><a href="javascript:;" class="relative z-20 inline-flex items-center justify-center w-6 h-6 -ml-2 text-white transition-all duration-200 border-2 border-white border-solid ease-in-out text-xs rounded-circle hover:z-30" data-toggle="tooltip" data-original-title="Michael Lewis"><img alt="Image placeholder" src="../../static/img/team-4.jpg" class="w-full !rounded-circle"></a></div></div>',
                assignee: "Done Joe",
                description: "This task's description is for something, but not for anything",
                class: ["rounded-lg"]
              }
            ]
          }
        ]
      });

      var addBoardDefault = document.getElementById("jkanban-add-new-board");
      addBoardDefault.addEventListener("click", function() {
        let newBoardName = document.getElementById("jkanban-new-board-name")
          .value;
        let newBoardId = "_" + newBoardName.toLowerCase().replace(/ /g, "_");
        KanbanTest.addBoards([{
          id: newBoardId,
          title: newBoardName,
          item: []
        }]);
        document.querySelector('#new-board-modal').classList.remove('show');
        document.querySelector('body').classList.remove('modal-open');
      });

      var updateTask = document.getElementById("jkanban-update-task");
      updateTask.addEventListener("click", function() {
        let jkanbanInfoModalTaskId = document.querySelector(
          "#jkanban-info-modal #jkanban-task-id"
        );
        let jkanbanInfoModalTaskTitle = document.querySelector(
          "#jkanban-info-modal #jkanban-task-title"
        );
        let jkanbanInfoModalTaskAssignee = document.querySelector(
          "#jkanban-info-modal #jkanban-task-assignee"
        );
        let jkanbanInfoModalTaskDescription = document.querySelector(
          "#jkanban-info-modal #jkanban-task-description"
        );
        KanbanTest.replaceElement(jkanbanInfoModalTaskId.value, {
          title: jkanbanInfoModalTaskTitle.value,
          assignee: jkanbanInfoModalTaskAssignee.value,
          description: jkanbanInfoModalTaskDescription.value
        });
        jkanbanInfoModalTaskId.value = jkanbanInfoModalTaskId.value;
        jkanbanInfoModalTaskTitle.value = jkanbanInfoModalTaskTitle.value;
        jkanbanInfoModalTaskAssignee.value = jkanbanInfoModalTaskAssignee.value;
        jkanbanInfoModalTaskDescription.value = jkanbanInfoModalTaskDescription.value;
        document.querySelector('#jkanban-info-modal').classList.remove('show');
        document.querySelector('body').classList.remove('modal-open');
        document.querySelector('.modal-backdrop').remove();


      });
    }
  })();