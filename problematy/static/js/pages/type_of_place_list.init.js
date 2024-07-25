"use strict";
(function ($) {
    $(document).ready(function () {
        $('#btn-editable').on('click', '.delete-type-of-place-button', function () {
            var $this = $(this);
            var typeId = $this.closest('tr').data('type-of-place-id');

            $('.confirm-delete-type-of-place-button').remove(); // Удаляем предыдущие кнопки подтверждения, если они есть

            $('<button>').text('Confirm')
                .addClass('confirm-delete-type-of-place-button btn btn-warning')
                .data('type-of-place-id', typeId)
                .insertAfter($this);

            $this.hide(); // Скрываем кнопку "Delete"
        });

        $('#btn-editable').on('click', '.confirm-delete-type-of-place-button', function () {
            var typeId = $(this).data('type-of-place-id');
            $.ajax({
                url: `/type_of_place/${typeId}/delete/`,
                method: 'POST',
                data: {
                    'id': typeId,
                    'csrfmiddlewaretoken': getCookie('csrftoken'),
                },
                success: function (response) {
                    location.reload(); // Перезагружаем страницу для обновления списка типов мест
                },
                error: function (xhr, status, error) {
                    console.error("An error occurred: " + error);
                }
            });
        });

        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    var cookie = $.trim(cookies[i]);
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    });
})(jQuery);
