"use strict";
(function ($) {
    $(document).ready(function () {
        // Показываем кнопку подтверждения удаления при нажатии на кнопку "Delete"
        $('#btn-editable').on('click', '.delete-attribute-button', function () {
            var $this = $(this);
            var attributeId = $this.closest('tr').data('attribute-id');

            $('.confirm-delete-attribute-button').remove(); // Удаляем предыдущие кнопки подтверждения, если они есть

            $('<button>').text('Confirm')
                .addClass('confirm-delete-attribute-button btn btn-warning')
                .data('attribute-id', attributeId)
                .insertAfter($this);

            $this.hide(); // Скрываем кнопку "Delete"
        });

        // Обработка нажатия на кнопку подтверждения удаления
        $('#btn-editable').on('click', '.confirm-delete-attribute-button', function () {
            var attributeId = $(this).data('attribute-id');
            $.ajax({
                url: `/attributes/${attributeId}/delete/`,
                method: 'POST',
                data: {
                    'id': attributeId,
                    'csrfmiddlewaretoken': getCookie('csrftoken'),
                },
                success: function (response) {
                    location.reload();
                },
                error: function (xhr, status, error) {
                }
            });
        });

        // Функция для получения значения CSRF токена из куки
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = $.trim(cookies[i]);
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
