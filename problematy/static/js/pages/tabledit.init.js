"use strict";
!function ($) {
    function EditableTable() {
    }

    EditableTable.prototype.init = function () {
        // Функция для получения значения CSRF токена из куки
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        // Настройка AJAX-запросов для включения CSRF токена
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        });

        // Инициализация Tabledit
        $("#btn-editable").Tabledit({
            url: 'actions/',
            buttons: {
                edit: {
                    class: "btn btn-success",
                    html: '<span class="mdi mdi-pencil"></span>',
                    action: "edit"
                },
                delete: {
                    class: "btn btn-danger",
                    html: '<span class="mdi mdi-delete"></span>',
                    action: "delete"
                }
            },
            inputClass: "form-control form-control-sm",
            deleteButton: true,
            saveButton: false,
            autoFocus: false,
            columns: {
                identifier: [0, "id"],
                editable: [[1, "full_name"], [3, "role"]]
            }
        });
    };

    $.EditableTable = new EditableTable();
}(window.jQuery);

$(document).ready(function() {
    window.jQuery.EditableTable.init();
});
