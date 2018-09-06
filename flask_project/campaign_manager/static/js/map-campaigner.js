// GLOBAL VARIABLE
window.isAuthenticated = false;


$(function () {
    $('#side-menu').metisMenu();
});

//Loads the correct sidebar on window load,
//collapses the sidebar on window resize.
// Sets the min-height of #page-wrapper to window size
$(function () {

    $(window).bind("load resize", function () {
        var topOffset = 50;
        var width = (this.window.innerWidth > 0) ? this.window.innerWidth : this.screen.width;
        if (width < 768) {
            $('div.navbar-collapse').addClass('collapse');
            topOffset = 100; // 2-row-menu
        } else {
            $('div.navbar-collapse').removeClass('collapse');
        }

        var height = ((this.window.innerHeight > 0) ? this.window.innerHeight : this.screen.height) - 1;
        height = height - topOffset;
        if (height < 1) height = 1;
        if (height > topOffset) {
            $("#page-wrapper").css("min-height", (height) + "px");
        }
    });

    var url = window.location;
    // var element = $('ul.nav a').filter(function() {
    //     return this.href == url;
    // }).addClass('active').parent().parent().addClass('in').parent();
    var element = $('ul.nav a').filter(function () {
        return this.href == url;
    }).addClass('active').parent();

    while (true) {
        if (element.is('li')) {
            element = element.parent().addClass('in').parent();
        } else {
            break;
        }
    }
});


function showLoading() {
    $.LoadingOverlay("show",
        {image: "static/resources/loading-spinner.gif"});
}

function hideLoading() {
    $.LoadingOverlay("hide");
}

function showNotifications(text, status) {
    clearNotification();

    $('#first-row').prepend(
        '<div id="notification" class="alert alert-' + status + ' alert-dismissable" style="margin-bottom: 10px; margin-top: 0;">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>' +
        text +
        '</div>'
    );
}

function clearNotification() {
    if ($('#notification').length > 0) {
        $('#notification').remove();
    }
}

// UTILITIES

function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

function containsObject(obj, list) {
    var i;
    for (i = 0; i < list.length; i++) {
        if (list[i] === obj) {
            return true;
        }
    }
    return false;
}

function capitalizeFirstLetter(string) {
    if(typeof string !== 'undefined') {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
}

function getRandomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function hashCode(str) { // java String#hashCode
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return hash;
}

function intToRGB(i) {
    var c = (i & 0x00FFFFFF)
        .toString(16)
        .toUpperCase();

    return "00000".substring(0, 6 - c.length) + c;
}

function check(array1, array2) {
    for (var i = 1; i < array1.length; i++) {
        $.inArray(5 + 5, ["8", "9", "10", 10 + ""]);
    }

    return true;
}