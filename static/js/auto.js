"use strict"

// requires pushpull.js beforehand

function setPush(elem, group) {
    switch (elem.tagName) {
        case "TEXTAREA":
        case "INPUT":
            elem.onchange = function() {
                push(group, elem.value);
            }
            break;
        case "BUTTON":
            elem.onclick = function() {
                push(group, "");
            }
            break;
        case "TD":
        case "P":
        case "TABLE":
            break;
        default:
            console.log(group);
            break;
    }
}

function setPull(list, group) {
    pull(group, function(v) {
        for (var i=0;i<list.length;i++) {
            switch (list[i].tagName) {
                case "TEXTAREA":
                case "INPUT":
                    list[i].value = v;
                    break;
                case "TD":
                case "TABLE":
                case "P":
                    list[i].innerHTML = v;
                    break;
                case "BUTTON":
                    break;
                default:
                    console.log(list[i].tagName);
                    break;
            }
        }
    });
}

var elems = document.getElementsByClassName("crosslink");
var pulllist = {};
for (var i=0;i<elems.length;i++) {
    var elem = elems[i];
    var group = elem.getAttribute("name");
    if (group in pulllist) {
        pulllist[group].push(elem)
    } else {
        pulllist[group] = [elem];
    }
    setPush(elem, group);
}

for (var group in pulllist) {
    setPull(pulllist[group], group);
}
