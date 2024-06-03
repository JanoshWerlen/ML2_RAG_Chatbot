let conversationId = null;
let awaitingFollowUp = false;

function user_says(followUp = false) {
    let user_input = $('#user_says_input').val();
    let messages_div = $('#messages');
    let filter_value = $('input[name="filter"]:checked').val();

    if (user_input.trim() !== '') {
        messages_div.append(`<div class="mb-2"><strong>You:</strong> ${user_input}</div>`);
        $('#user_says_input').val(''); // Clear the input field

        $.ajax({
            url: '/chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                message: user_input,
                filter_values: filter_value,
                conversation_id: conversationId,
            }),
            success: function(response) {
                let bot_reply = response.reply;
                messages_div.append(`<div class="mb-2"><strong>Bot:</strong> ${bot_reply}</div>`);
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    }
}

function reset(event) {
    event.preventDefault();
    $('#messages').empty();
    conversationId = null; // Reset conversation ID
    awaitingFollowUp = false; // Reset follow-up state
}

function info(event) {
    event.preventDefault();
    alert("This is a chatbot interface.");
}
