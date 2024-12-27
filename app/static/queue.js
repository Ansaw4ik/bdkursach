$(document).ready(function() {
    const infoModal = $("#infoModal");
    const queueInfoIcon = $("#queueInfoIcon");
    const closeInfoModal = $("#closeInfoModal");
    const addEntryModal = $("#addEntryModal");
    const addEntryBtn = $("#addEntryBtn");
    const closeAddEntryModal = $("#closeAddEntryModal");
    const userEmailTooltip = $("#userEmailTooltip");
    const queueTable = $("#queueTable");
    const queueBody = $("#queueBody");
    function showTooltip(event, email) {
        userEmailTooltip.text(email);
        userEmailTooltip.css({
            top: event.pageY + 10,
            left: event.pageX + 10,
            display: 'block'
        });
    }
     function hideTooltip() {
        userEmailTooltip.css('display', 'none');
    }
      queueBody.on('mouseenter', 'td .username-hover', function(e) {
         const email = $(this).data('email');
        showTooltip(e, email);

    });
    queueBody.on('mouseleave', 'td .username-hover', function() {
        hideTooltip();
    });

    // Функция для открытия модального окна
    queueInfoIcon.on('click', function() {
        infoModal.css('display', 'block');
    });

    closeInfoModal.on('click', function() {
        infoModal.css('display', 'none');
    });
    addEntryBtn.on('click', function() {
        addEntryModal.css('display', 'block');
    });
     closeAddEntryModal.on('click', function() {
        addEntryModal.css('display', 'none');
    });
    $(window).on('click', function(event) {
       if (event.target === infoModal[0]) {
            infoModal.css('display', 'none');
        }
          if (event.target === addEntryModal[0]) {
            addEntryModal.css('display', 'none');
        }
    });
    queueTable.on('change', 'input[type="checkbox"]', function() {
        const entryId = $(this).data('entry-id');
        const queueId = queueTable.data('queue-id');
        const isCompleted = this.checked;
           $.ajax({
            url: `/complete_entry/${queueId}/${entryId}`,
            type: 'POST',
             contentType: 'application/json',
            data: JSON.stringify({is_completed: isCompleted}),
            success: function(response) {
                if (response.success) {
                     $(this).closest('tr').toggleClass('completed', isCompleted);
                } else {
                    alert("Ошибка: " + response.error);
                    $(this).prop('checked', !isCompleted);
                 }
            }.bind(this),
            error: function(error) {
               alert("Ошибка сети: " + error.responseText);
                $(this).prop('checked', !isCompleted);
            }.bind(this)
        });
    });
   $('#addEntryForm').submit(function(event) {
        event.preventDefault();
         const form = $(this);
          $.ajax({
            type: 'POST',
            url: `/add_entry/${form.find('input[name="queueId"]').val()}`,
            data: form.serialize(), // сериализация данных формы
            success: function(response) {
                if (response.success) {
                    alert('Запись добавлена!');
                     location.reload();
                } else {
                  alert('Ошибка при добавлении: ' + response.error)
                 }
                 addEntryModal.css('display', 'none');
                  form[0].reset();
            },
              error: function(error){
                  alert('Ошибка сети: ' + error.responseText)
              }
          });
    });
});
$(document).ready(function () {
    $("#deleteQueueBtn").on("click", function () {
        const queueId = $(this).data("queue-id");

        if (!queueId || !confirm("Вы уверены, что хотите удалить эту очередь?")) {
            return;
        }

        $.ajax({
            url: `/delete_queue/${queueId}`,
            type: "POST",
            success: function (response) {
                if (response.success) {
                    alert("Очередь успешно удалена!");
                    window.location.href = response.redirect_url; // Перенаправление на страницу комнаты
                } else {
                    alert("Ошибка: " + response.error);
                }
            },
            error: function (error) {
                alert("Ошибка сети: " + error.responseText);
            },
        });
    });
});
