function createOrReturnPrivateChat(id) {
    payload = {
        "csrfmiddlewaretoken": "{{csrf_token}}",
        "user2_id": id,
    }
    $.ajax({
        type: "POST",
        url: "{% url 'create-or-return-private-chat' %}",
        data: payload,
        dataType: "json",
        timeout: 5000,
        success: function (data) {
            if (data.response == "Successfully got the chat." ) {
                chatroomId = data.chatroom_id
                onGetOrCreateChatroomSuccess(chatroomId)
            }
            else if (data.response != null) {
                alert(data.reponse)
            }
        },
        error: function (data) {
            alert("Something went wrong")
        },
        
    });
}

function onGetOrCreateChatroomSuccess(chatroomId) {
    var url = "{% url 'private-chat' %}?room_id=" + chatroomId
    var win = window.location.replace(url)
    // window.open(url)
    win.focus()
}