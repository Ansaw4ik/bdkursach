$(document).ready(function() {
    const createQueueDialog = $("#createQueueDialog");
    const createQueueButton = $("#createQueueButton");
    const queueListAdmin = $("#queueListAdmin");
    const participantsList = $("#participantsList")
    const userEmailTooltip = $("#userEmailTooltip")
    const queueTable = $("#queueTable");

        function showTooltip(event, email) {
            const target = $(event.target); // Получаем элемент li
             const targetRect = target[0].getBoundingClientRect();
            userEmailTooltip.text(email);
            userEmailTooltip.css({
               top: targetRect.top + targetRect.height, // Позиционируем тултип ниже элемента
               left: targetRect.left,  // Позиционируем тултип слева от элемента
                display: 'block'
            });
        }


    function hideTooltip() {
        userEmailTooltip.css('display', 'none');
    }

    participantsList.on('mouseenter', 'li', function(e) {
        const email = $(this).data('email');
        showTooltip(e, email);
    });

    participantsList.on('mouseleave', 'li', function() {
        hideTooltip();
    });


    createQueueButton.on('click', function() {
        createQueueDialog.css('display', 'block');
    });
    $("#createQueueDialog button[type='submit']").on('click', function(event){
         event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/create_queue",
             data:  $("#createQueueForm").serialize(),
            success: function(response) {
                 if (response.success) {
                   alert('Очередь успешно создана!');
                    location.reload();
                } else {
                   alert('Ошибка при создании: ' + response.error);
                }
                createQueueDialog.css('display', 'none');
            },
             error: function(error) {
                  alert('Ошибка сети: ' + error.responseText);
                 createQueueDialog.css('display', 'none');
                }
        });

    });
    $(window).on('click', function(event) {
      if (event.target === createQueueDialog[0]) {
            createQueueDialog.css('display', 'none');
        }
    });


    });
$(function () {
    const copyRoomLinkButton = $("#copyRoomLinkButton");
    const copyNotification = $("#copyNotification");

    copyRoomLinkButton.on("click", function () {
        const roomId = $(this).data('room-id'); // Получаем room_id из data-атрибута кнопки
        const roomUrl = `${window.location.origin}/room/${roomId}`; // Генерация ссылки на комнату

        navigator.clipboard.writeText(roomUrl).then(() => {
            copyNotification.text("Скопировано!").fadeIn();


            setTimeout(() => {
                copyNotification.fadeOut();
            }, 2000);
        }).catch((err) => {
            console.error("Ошибка при копировании ссылки: ", err);
            alert("Не удалось скопировать ссылку. Попробуйте вручную.");
        });
    });
});



$(document).ready(function() {
    $("#deleteRoomButton").on("click", function() {
        if (!confirm("Вы уверены, что хотите удалить эту комнату? Это действие необратимо.")) {
            return;
        }

        const roomId = $(this).data("room-id");

        $.ajax({
            type: "DELETE",
            url: `/delete_room/${roomId}`,
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    window.location.href = '/my_rooms'; // Возврат на страницу комнат
                } else {
                    alert("Ошибка: " + response.error);
                }
            },
            error: function(error) {
                alert("Ошибка сети: " + error.responseText);
            }
        });
    });
});
