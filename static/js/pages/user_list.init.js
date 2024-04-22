"use strict";
(function ($) {
    $(document).ready(function () {
        $('#btn-editable').on('click', '.edit-role-button', function () {
            var userId = $(this).data('user-id');
            window.location.href = `/user/edit/${userId}/`; // Убедитесь, что путь соответствует вашим URL-адресам в Django
        });

        $('#btn-editable').on('click', '.delete-role-button', function () {
            var $row = $(this).closest('tr');
            var userId = $(this).data('user-id');
            $row.find('.confirm-delete-role-button').remove();

            $('<button>').text('Confirm Delete')
                .addClass('confirm-delete-role-button btn btn-warning')
                .data('user-id', userId)
                .insertAfter(this);

            $(this).hide();
        });

        $('#btn-editable').on('click', '.confirm-delete-role-button', function () {
            var userId = $(this).data('user-id');
            var $row = $(this).closest('tr');

            $.ajax({
                url: `/user/delete/${userId}/`, // Убедитесь, что путь соответствует вашим URL-адресам в Django
                method: 'POST',
                data: {
                    'csrfmiddlewaretoken': getCookie('csrftoken'),
                },
                success: function (response) {
                    console.log("User deleted successfully");
                    $row.remove(); // Удаляем строку из DOM после успешного удаления
                },
                error: function (xhr, status, error) {
                    console.log("An error occurred: " + error);
                }
            });
        });

        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
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
