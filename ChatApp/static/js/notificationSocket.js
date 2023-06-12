//ws:// or wss://
var ws_scheme = window.location.protocal == "https:" ? "wss" : "ws";
var ws_path = ws_scheme + "://" + window.location.host + "/"    // development
//var ws_path = ws_scheme + "://" + window.location.host + ":8001/" // production
var notificationSocket = new WebSocket(ws_path)

notificationSocket.onmessage = function(message){
    console.log("Got Notification websocket message.");
    var data = JSON.parse(message.data)
    if (data.general_msg_type == 0){
        handleGeneralNotificationsData(data['notifications'], data['new_page_number'])
    }
}

notificationSocket.error = function(e){
    console.log("Notification socket closed unexpectedly.");
}

notificationSocket.onopen = function(e){
    console.log("Notification socket onopen.");
    setupGeneralNotificationsMenu();
    getFirstGeneralNotificationsPage();
}

notificationSocket.onclose = function(e){
    console.log("Notification socket closed.");
}

if(notificationSocket.readyState == WebSocket.OPEN){
    console.log("Notification socket OPEN complete.");
}
else if (notificationSocket.readyState == WebSocket.CONNECTING) {
    console.log("Notification socket connecting...");
} 

