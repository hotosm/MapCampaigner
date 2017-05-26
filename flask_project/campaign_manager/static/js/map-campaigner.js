// GLOBAL VARIABLE
window.isAuthenticated = false;


$(function() {
    $('#side-menu').metisMenu();
});

//Loads the correct sidebar on window load,
//collapses the sidebar on window resize.
// Sets the min-height of #page-wrapper to window size
$(function() {

    var topOffset = 50;
    var height = (($(window).innerHeight > 0) ? $(window).innerHeight : $(window).height()) - 1;
    height = height - topOffset;
    if (height < 1) height = 1;
    if (height > topOffset) {
        $("#page-wrapper").css("min-height", (height) + "px");
    }

    $(window).bind("load resize", function() {
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
    var element = $('ul.nav a').filter(function() {
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
        {image : "static/resources/loading-spinner.gif"});
}

function hideLoading() {
    $.LoadingOverlay("hide");
}

function showNotifications(text, status) {
    clearNotification();

    $('#first-row').prepend(
        '<div id="notification" class="alert alert-'+status+' alert-dismissable">' +
            '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>'+
            text+
        '</div>'
    );
}

function clearNotification() {
    if($('#notification').length > 0) {
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
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function getRandomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}
