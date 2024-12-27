  $(document).ready(function() {
       const createRoomDialog = $("#createRoomDialog");
       const addRoomIcon = $("#addRoomIcon");

       addRoomIcon.on("click", function() {
           createRoomDialog.css('display', 'block');
       });
        $(window).on('click', function(event) {
           if (event.target === createRoomDialog[0]) {
                createRoomDialog.css('display', 'none');
            }
        });
       $('#createRoomForm').submit(function(event) {
            event.preventDefault(); // Отменяем стандартное действие submit
             const form = $(this);
             $.ajax({
                    type: 'POST',
                    url: '/create_room',
                    data: form.serialize(),// передаем данные формы form.serialize()
                    success: function(response) {
                        if (response.success) {
                            alert('Комната успешно создана!');
                            location.reload(); // Перезагружаем страницу для отображения изменений
                        } else {
                            alert('Ошибка при создании: ' + response.error);
                        }
                       createRoomDialog.css('display', 'none'); // Закрываем модальное окно
                         form[0].reset();

                    },
                   error: function(error) {
                        alert("Ошибка сети:" + error.responseText);
                      createRoomDialog.css('display', 'none');
                    }
             });

        });

   });
