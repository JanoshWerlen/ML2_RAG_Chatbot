let conversationId = null;
let awaitingFollowUp = false;

function user_says(followUp = false) {
  let user_input = $('#user_says_input').val();
  let messages_div = $('#messages');
  let filter_value = $('input[name="filter"]:checked').val();

  if (user_input.trim() !== '') {
    messages_div.append(`<div class="mb-2"><strong>You:</strong> ${user_input}</div>`);

    $.ajax({
      url: '/chat',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        message: user_input,
        filter_values: filter_value,
        conversation_id: conversationId,
        follow_up: followUp,
        awaiting_follow_up: awaitingFollowUp
      }),
      success: function(response) {
        messages_div.append(`<div class="mb-2"><strong>Bot:</strong> ${response.response}</div>`);
        $('#user_says_input').val(''); // Clear the input field
        if (response.conversation_id) {
          conversationId = response.conversation_id;
        }
        if (response.follow_up_prompt) {
          messages_div.append(`<div class="mb-2"><strong>Bot:</strong> Möchten Sie eine Folgefrage stellen? (Ja/Nein)</div>`);
          awaitingFollowUp = true;
        } else {
          awaitingFollowUp = false;
        }
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

// Handle follow-up response
$(document).on('keypress', '#user_says_input', function(e) {
  if(e.which == 13) {
    let user_input = $('#user_says_input').val().trim().toLowerCase();
    if (awaitingFollowUp) {
      if (user_input === 'ja') {
        awaitingFollowUp = false;
        messages_div.append(`<div class="mb-2"><strong>Bot:</strong> Bitte geben Sie Ihre Folgefrage ein:</div>`);
      } else if (user_input === 'nein') {
        awaitingFollowUp = false;
        conversationId = null; // Reset conversation if no follow-up
        messages_div.append(`<div class="mb-2"><strong>Bot:</strong> Vielen Dank für Ihre Fragen. Wenn Sie weitere Fragen haben, lassen Sie es mich wissen.</div>`);
      } else {
        messages_div.append(`<div class="mb-2"><strong>Bot:</strong> Ungültige Eingabe. Bitte antworten Sie mit 'Ja' oder 'Nein'.</div>`);
      }
    } else {
      user_says();
    }
  }
});
