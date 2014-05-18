"use strict"

alert = (function () {
    var pushqueue = [];
    var available = false;
    var pulls = {}

    var socket = new WebSocket("ws://localhost:8888/socket");
    socket.onopen = function () {
        socket.send(window.location.pathname);
        while (pushqueue.length > 0) {
            socket.send(pushqueue.pop())
        }
        available = true;
    }
    socket.onmessage = function(e) {
        var d = e.data.split("=");
        if (d[0] in pulls) {
            pulls[d[0]](d[1]);
        }
    }

    window.push = function push(key, value) {
        pushqueue.push(String(key) + "=" + String(value))
        if (available) {
            while (pushqueue.length > 0) {
                socket.send(pushqueue.pop())
            }
        }
    }

    window.pull = function pull(key, callback) {
        pulls[key] = callback;
    }

    window.unpull = function unpull(key) {
        delete pulls[key];
    }

    return alert;
}).call()
