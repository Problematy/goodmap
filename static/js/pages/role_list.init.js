"use strict";
(function ($) {
    $(document).ready(function () {
        // Обработка нажатия на кнопку "Edit"
        $('#btn-editable').on('click', '.edit-role-button', function () {
            var roleId = $(this).closest('tr').data('role-id');
            window.location.href = `/roles/edit/${roleId}`;
        });

        $('#btn-editable').on('click', '.delete-role-button', function () {
            var $this = $(this);
            var roleId = $this.closest('tr').data('role-id');

            $('.confirm-delete-role-button').remove();

            $('<button>').text('Confirm')
                .addClass('confirm-delete-role-button btn btn-warning')
                .data('role-id', roleId)
                .insertAfter($this);

            $this.hide();
        });

        $('#btn-editable').on('click', '.confirm-delete-role-button', function () {
            var roleId = $(this).data('role-id');
            $.ajax({
                url: `/roles/delete/${roleId}/`,
                method: 'POST',
                data: {
                    'id': roleId,
                    'csrfmiddlewaretoken': getCookie('csrftoken'),
                },
                success: function (response) {
                    console.log("Role deleted successfully");
                    location.reload();
                },
                error: function (xhr, status, error) {
                    console.log("An error occurred: " + error);
                }
            });
        });

        // Функция для получения значения CSRF токена из куки
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = jQuery.trim(cookies[i]);
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
