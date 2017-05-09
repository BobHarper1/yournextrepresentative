$(function(){
    $('.js-bulk-known-person-alternate-name').on('click', function(e){
        e.preventDefault();

        $person = $(this).parents('li');
        $link = $person.find('.js-bulk-known-person-alternate-name')
        $form = $( $('.js-bulk-known-person-alternate-name-form').html() );
        $form.appendTo($person);
        $form.find('input[type="text"]').focus();

        $form.on('submit', function(){
            $form.find('#altnameerr').remove();
            $form.find('.alert').remove();
            $form.find('.errorlist').remove();
            $name = $form.find('input[name="name"]').val();
            $.ajax({
                url: $link.attr('href'),
                type: "POST",
                data: {
                    csrfmiddlewaretoken: $form.find('input[type="hidden"]').val(),
                    name : $name,
                    source : $form.find('input[name="source"]').val()
                },

                success: function(json) {
                    if (json['success']) {
                        $other = $person.find('.other-names');
                        if ($other.length == 0) {
                            $first_name = $person.find('>:first-child');
                            $first_name.after('<ul class="other-names"><li>Other names:</li></ul>');
                            $other = $person.find('.other-names');
                        }
                        $names = $other.find('.other-name');
                        $names.remove()
                        for (var i = 0; i < json.names.length; i++) {
                            var name = json.names[i];
                            var highlight = '';
                            if (name == $name) {
                                highlight = ' highlight';
                            }
                            $other.append('<li class="other-name' + highlight + '">' + json.names[i] + '</li>');
                        }
                        $form.remove();
                    } else {
                        if (json['errors']) {
                            for (var err in json.errors) {
                                if (!json.errors.hasOwnProperty(err)) { continue; }
                                el = $form.find('input[name="' + err + '"]');
                                el.before('<ul class="errorlist"><li>' + json.errors[err] + '</li></ul>')
                            }
                        }
                    }
                },

                error: function(xhr,errmsg,err) {
                    $form.prepend("<div class='alert-box alert radius' id='altnameerr'>There was a problem adding the name, please try again</div>");
                }
            });
            return false;
        });

        $form.on('click', '.js-bulk-known-person-alternate-name-cancel', function(){
            $form.remove();
        });
    });
});
